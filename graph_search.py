import os
import time
import re
import requests
import argparse
import logging
import sys
sys.path.append(os.path.join(os.path.dirname("..")))
from concurrent.futures import ThreadPoolExecutor
from graph_utils.chatgpt.config.config import (
    OPENAI_CONFIG,
    LOGGER_MODES,
    APPLICATION_PROMPTS,
)
from graph_utils.chatgpt.utils import init_logging
# from fsm_generation.fsm_generator import Manager
from graph_utils.graph_generate_bak import Knowledge_Graph
import json
import concurrent.futures
from tqdm import tqdm  # Assume tqdm is installed
import multiprocessing as mp
from multiprocessing import Pool
from graph_utils.review import *
# from paper_decompose.paper_decompose import Paper_Decompose
# from paper_decompose.section_generator import SectionGeneration

def process_pdf_list(pdf_ls):
    """Process a list of PDFs or directories, extracting individual PDF files."""
    if not isinstance(pdf_ls, list):
        pdf_ls = [pdf_ls]
    temp_ls = []
    for pdf in pdf_ls:
        if os.path.isdir(pdf):
            temp_ls.extend([os.path.join(pdf, file) for file in os.listdir(pdf) if file.endswith('.pdf')])
        else:
            temp_ls.append(pdf)
            
    for num in range(len(temp_ls)):
        file_path = pdf_ls[num][:-4]+"/"+pdf_ls[num][:-4].split("/")[-1]+".md"
        temp_ls[num] = file_path
    return temp_ls


# Define the function for sending POST requests
def send_post_request(path):
    session = requests.Session()
    session.trust_env = False
    post_data = {
        'filepath': path,
        # 在这里添加其他参数
    }
    try:
        response = session.post("http://127.0.0.1:2675/marker", data=json.dumps(post_data))
        response.raise_for_status()  # 检查是否有 HTTP 错误
        return response.json().get('output', '')  # 返回 'output' 字段，如果没有则返回空字符串
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error for path {path}: {str(e)}")


def table_generate(template, table):
    head1=0
    head2=0
    head3=0
    head4=0
    for doc in template:
        # print(doc.metadata)
        for k, v in doc.metadata.items():
            # print(k, v)
            if k == "Header 1" and (table == [] or "# "+v != table[head1]):
                table.append("# "+v)
                head1 = table.index("# "+v)
            elif k == "Header 2" and (table == [] or "## "+v != table[head2]):
                table.append("## "+v)
                head2 = table.index("## "+v)
            elif k == "Header 3" and (table == [] or "### "+v != table[head3]):
                table.append("### "+v)
                head3 = table.index("### "+v)
            elif k == "Header 4" and (table == [] or "#### "+v != table[head4]):
                table.append("#### "+v)
                head4 = table.index("#### "+v)
    return table


def position(doc):
    if 'Header 3' in doc.metadata:
        return doc.metadata['Header 3']
    elif 'Header 2' in doc.metadata:
        return doc.metadata['Header 2']
    elif 'Header 1' in doc.metadata:
        return doc.metadata['Header 1']
    elif 'Header 4' in doc.metadata:
        return doc.metadata['Header 4']
    else:
        return None
    
def position_count(doc):
    if 'Header 3' in doc.metadata:
        return doc.metadata['Header 3'], 3
    elif 'Header 2' in doc.metadata:
        return doc.metadata['Header 2'], 2
    elif 'Header 1' in doc.metadata:
        return doc.metadata['Header 1'], 1
    elif 'Header 4' in doc.metadata:
        return doc.metadata['Header 4'], 4
    else:
        return None

# from enhanced_pre_recall import enhanced_retry

def process_single_pdf(pdf_id):
    """Wrapper function for processing a single PDF file, used for parallel processing."""
    try:
        # Set an independent process name for each process for easier debugging
        current_process = mp.current_process()
        process_name = f"Worker-{current_process.pid}-PDF{pdf_id}"
        
        print(f"[{process_name}] Starting to process Paper_{pdf_id}...")
        start_time = time.time()
        
        # 调用原始的main函数
        result = main(pdf_id)
        
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"[{process_name}] ✅ Paper_{pdf_id} processed successfully, time taken: {processing_time:.2f}s")
        
        return {
            'pdf_id': pdf_id,
            'status': 'success',
            'processing_time': processing_time,
            'result': result,
            'process_name': process_name
        }
        
    except Exception as e:
        current_process = mp.current_process()
        process_name = f"Worker-{current_process.pid}-PDF{pdf_id}"
        print(f"[{process_name}] ❌ Paper_{pdf_id} processing failed: {str(e)}")
        return {
            'pdf_id': pdf_id,
            'status': 'error',
            'error': str(e),
            'processing_time': 0,
            'process_name': process_name
        }

def main(pdf_id):
    # Initialize logging
    init_logging()
    logger = logging.getLogger(__name__)
    logger.setLevel(LOGGER_MODES)

    # Load configurations, giving priority to command line arguments
    api_key = OPENAI_CONFIG['api_key']
    base_url = OPENAI_CONFIG['base_url']
    # organization = OPENAI_CONFIG['organization']
    # pdf_ls = NOUGAT_CONFIG['pdf']
    # keyword = ARXIV_CONFIG['key_word']
    # download = True
    # daily_type = ARXIV_CONFIG['daily_type']
    # run_all = True
    # specific_app = "blog"
    # recompute = True
    # Validate API key and base URL
    if not (api_key and base_url):
        raise ValueError("API key and base URL must be provided either via --api_key and --base_url or in the config file.")

    template_graph = Knowledge_Graph(filtered=False,type_name="FTTemplate")

        
    md_text = ""
    # Use absolute path
    base_path = os.path.join(os.getcwd(), "origin_paper", "more_paper")
    base_path = os.path.abspath(base_path)
    paths = []
    for i in range(1, 6):
        pdf_file = os.path.join(base_path, f"{i}.pdf")
        si_file = os.path.join(base_path, f"{i}-si.pdf")
        paths.append([pdf_file, si_file])
    path_set = paths[pdf_id-1]
    for path in path_set:
        if os.path.exists(path):
            md_text += send_post_request(path)+"\n\n"

    knowledge_graph = Knowledge_Graph(markdown=md_text,type_name="FT Framework", filtered=False)
    if knowledge_graph.title == "None":
        knowledge_graph.title = "Paper "+str(pdf_id)

    generate_graph = "False" in str(knowledge_graph.graph.query("""MATCH (d:Document)
    WHERE d.title = "{title}"
    RETURN COUNT(d) > 0 AS exists LIMIT 1""".replace("{title}",knowledge_graph.title)))

    if generate_graph:
        knowledge_graph.filter_content()

        logging.info("Converting Documnets to Graph...")
        async def process_documents():
            documents = await knowledge_graph.llm_transformer.aconvert_to_graph_documents(knowledge_graph.splits)
            return documents
        
        # Call the async function using an event loop
        import asyncio
        documents = asyncio.run(process_documents())
        logging.info("Converting Documnets to Graph...Complete!")
        logging.info("Reviewing Graph Documents...")

        def process_one_doc(doc):
            try:
                review = review_graph_document(knowledge_graph.minillm, doc)   # Use your review LLM here
                reviewed_doc = apply_review(doc, review)
                return reviewed_doc
            except Exception as e:
                logging.exception(f"Review failed for one document: {e}")
                return doc  # Keep the original doc if an error occurs

        max_workers = 8  # Adjust based on your model rate limits; smaller is usually more stable
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            reviewed_documents = list(executor.map(process_one_doc, documents))

        logging.info("Reviewing Graph Documents...Complete!")
        logging.info("Adding Documents to Graph...")
        knowledge_graph.graph.add_graph_documents(
            documents,
            baseEntityLabel=True,
            include_source=True
        )
        logging.info("Adding Documents to Graph...Complete!")
        logging.info("Graph generated!!!")
        knowledge_graph.graph.query("""CREATE FULLTEXT INDEX entity IF NOT EXISTS
    FOR (n:__Entity__)
    ON EACH [n.id];""")

        
    summary = knowledge_graph.reason_answer(APPLICATION_PROMPTS["decompose_prompts"]["ft_summary_generation_simplified"].replace("{title}", knowledge_graph.title))
    new_table = table_generate(template_graph.splits, table=[])

    leaf_section = []
    for doc in template_graph.splits:
        title, cnt= position_count(doc)
        title = cnt*"#" + " " + title
        leaf_section.append(title)

    leaf_section = []
    for doc in template_graph.splits:
        title, cnt= position_count(doc)
        title = cnt*"#" + " " + title
        leaf_section.append(title)
    new_table = table_generate(template_graph.splits, table=[])

    ###################################################################################################
    # all parallel

    section_results = []
    delay = 30
    max_retries = 3
    
    # @enhanced_retry(max_retries=max_retries, delay=delay)
    def process_qa_chunk(args):
        template_num, chunk_questions, chunk_start = args
        question_str = "\n".join(chunk_questions)
        
        for retry in range(max_retries):
            try:
                if template_num == 7:
                    result = knowledge_graph.reason_answer(f"Please provide detailed answers to the following questions, marking each answer with the corresponding question. Use the format 'Q: [Original Question], A: [Answer]'. Write out the original question but do not use numbered indexes.**you should note that all questions should clearly exclude the activation processes existing in the characterization techniques.**\n<question>"+question_str+"\n</question>")
                elif template_num in (len(template_graph.splits)-1, len(template_graph.splits)-2):
                    result = knowledge_graph.graph_answer(f"Please provide detailed answers to the following questions, marking each answer with the corresponding question. Use the format 'Q: [Original Question], A: [Answer]'. Write out the original question but do not use numbered indexes.\n<question>"+question_str+"\n</question>")
                else:
                    result = knowledge_graph.mini_answer(f"Please provide detailed answers to the following questions, marking each answer with the corresponding question. Use the format 'Q: [Original Question], A: [Answer]'. Write out the original question but do not use numbered indexes.\n<question>"+question_str+"\n</question>")
                return (chunk_start, result.split("\n"))  # 返回包含chunk_start的元组
            except Exception as e:
                print(f"\x1b[31mSection {template_num+1} QA Chunk {chunk_start//5+1} Error ({retry+1}/{max_retries}):\x1b[0m", str(chunk_questions))
                print(f"\x1b[31mSection {template_num+1} QA Chunk {chunk_start//5+1} Error ({retry+1}/{max_retries}):\x1b[0m", str(e))
                if retry < max_retries - 1:
                    time.sleep(delay)
        return (chunk_start, None)  # 所有重试失败

    # @enhanced_retry(max_retries=max_retries, delay=delay)
    def process_section(args):
        template_num, sec = args
        message = [
            {"role": "system", "content": APPLICATION_PROMPTS["decompose_prompts"]["system_prompt"]},
            {"role": "user", "content": APPLICATION_PROMPTS["decompose_prompts"]["decoompose_table_prompt"]
            .replace('{table}', "\n".join(new_table), 1)
            .replace('{describe}', sec.page_content, 1)
            .replace('{summary}', summary, 1)
            .replace('{example}', APPLICATION_PROMPTS["decompose_prompts"][template_graph.example_dict[template_num]], 1)}
        ]
        
        # 问题生成部分的重试逻辑
        questions = None
        for retry in range(max_retries):
            try:
                response = knowledge_graph.reasonllm.invoke(message)
                questions = response.content.replace("```", "").replace("json", "")
                questions = json.loads(questions)
                decompose_questions = [questions[str(i+1)]['question'] for i in range(len(questions))]
                print(f"Section {template_num+1} Generate {len(questions)} Questions")
                break
            except Exception as e:
                print(f"\x1b[31mSection {template_num+1} Questions Generation Error ({retry+1}/{max_retries}):\x1b[0m", str(e))
                if retry < max_retries - 1:
                    time.sleep(delay)
        else:
            print(f"\x1b[31mSection {template_num+1} questions generation failed after {max_retries} retries\x1b[0m")
            return None  # 所有重试失败
        
        # 问答处理部分并行化
        results = []
        chunk_args = []
        for chunk_start in range(0, len(decompose_questions), 5):
            chunk_questions = decompose_questions[chunk_start:chunk_start+5]
            chunk_args.append((template_num, chunk_questions, chunk_start))
        
        chunk_results = {}  # Ordered dict-like storage for chunk results
        # Tunable parameter 1: process QA in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as qa_executor:
            qa_progress = tqdm(qa_executor.map(process_qa_chunk, chunk_args), 
                            total=len(chunk_args), 
                            desc=f"Processing section {template_num+1} QA", 
                            position=0, leave=False)
            
            for chunk_start, chunk_result in qa_progress:
                if chunk_result is not None:
                    chunk_results[chunk_start] = chunk_result  # Save results by chunk_start
        
        # Merge chunk results in the original order (to ensure correct ordering)
        for chunk_start in sorted(chunk_results.keys()):  # 按起始位置排序
            chunk_result = chunk_results[chunk_start]
            if chunk_result:
                results.extend(chunk_result)
        
        qa_pair = "\n".join([s for s in results if s.strip()])
        
        # Section generation
        section_generation = [
            {"role": "system", "content": APPLICATION_PROMPTS["decompose_prompts"]["system_prompt"]},
            {"role": "user", "content": APPLICATION_PROMPTS["decompose_prompts"]["section_generation_just_from_table"]
            .replace('{position}', position(sec), 1)
            .replace('{qa}', qa_pair, 1)
            .replace('{summary}', summary, 1)
            .replace('{table}', "\n".join(new_table), 1)
            .replace('{describe}', leaf_section[template_num] + "\n" + sec.page_content, 1)
            .replace('{origin_title}', knowledge_graph.title, 1)}
        ]
        
        for retry in range(max_retries):
            try:
                if template_num in (len(template_graph.splits)-1, len(template_graph.splits)-2):
                    section_result = knowledge_graph.graphllm.invoke(section_generation).content
                else:
                    section_result = knowledge_graph.reasonllm.invoke(section_generation).content
                return section_result
            except Exception as e:
                print(f"\x1b[31mSection {template_num+1} Generation Error ({retry+1}/{max_retries}):\x1b[0m", str(e))
                if retry < max_retries - 1:
                    time.sleep(delay)
        return None  # 章节生成最终失败

    # Parallel processing section (tunable parameter 2: process sections in parallel)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [(template_num, sec) for template_num, sec in enumerate(template_graph.splits)]
        progress_bar = tqdm(executor.map(process_section, tasks), 
                            total=len(tasks), 
                            desc="Parallel Section Processing", 
                            position=0, leave=True)
        
        for result in progress_bar:
            if result is not None:
                section_results.append(result)
            else:
                section_results.append("Section processing failed (all retries exhausted)")  # Add an error placeholder

    full_article=["# "+knowledge_graph.title]
    cnt=0
    for v in new_table[1:]:
    # Check whether the current line matches any leaf section v
        if any(re.match(f"{re.escape(section)}", v) for section in leaf_section):
            current=section_results[cnt]
            # already="\n".join(full_article)
            # regen_section_result = section_generator.results_regeneration(
            #     current=current,
            #     already=already,
            #     reset_messages=True,
            #     response_only=True,
            # )
            full_article.append(current.replace("```markdown","").replace("```",""))
            cnt+=1
        else:
            full_article.append(v.replace("```markdown","").replace("```",""))
    article_result = "\n\n".join(full_article)
    # print(article_result)
    # save_dir = "./papersavings/"+knowledge_graph.title.replace(" ","_").replace("/","_")+".md"
    save_dir = "./papersavings/Paper_"+str(pdf_id)+".md"
    with open(save_dir,"w",encoding="utf-8") as f:
        f.write(article_result)


def run_parallel_processing(max_workers=3):
    """Process all PDF files in parallel."""
    base_path = "./papersavings/"
    
    # Check which files need to be processed
    pdf_ids_to_process = []
    for pdf_id in range(1, 4):
        output_file = base_path + f"Paper_{pdf_id}.md"
        if os.path.exists(output_file):
            print(f"Paper_{pdf_id} already exists, skipping...")
        else:
            pdf_ids_to_process.append(pdf_id)
    
    if not pdf_ids_to_process:
        print("All files have already been processed!")
        return
    
    print(f"Files to process: {pdf_ids_to_process}")
    print(f"Processing with {max_workers} parallel worker processes...")
    
    # Record total start time
    total_start_time = time.time()
    
    # Use a process pool for parallel processing
    with Pool(processes=max_workers) as pool:
        # Create a progress bar
        with tqdm(total=len(pdf_ids_to_process), desc="Parallel processing", position=0) as pbar:
            # Submit all tasks
            results = []
            for pdf_id in pdf_ids_to_process:
                result = pool.apply_async(process_single_pdf, (pdf_id,))
                results.append((pdf_id, result))
            
            # Wait for all tasks to complete and update the progress bar
            completed_results = []
            for pdf_id, result in results:
                try:
                    completed_result = result.get()  # Get result
                    completed_results.append(completed_result)
                    pbar.update(1)
                    pbar.set_postfix({
                        f'Paper_{pdf_id}': completed_result['status']
                    })
                except Exception as e:
                    error_result = {
                        'pdf_id': pdf_id,
                        'status': 'error',
                        'error': str(e),
                        'processing_time': 0
                    }
                    completed_results.append(error_result)
                    pbar.update(1)
                    pbar.set_postfix({f'Paper_{pdf_id}': 'error'})
    
    # Calculate total processing time
    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time
    
    # Summarize results
    successful_count = sum(1 for r in completed_results if r['status'] == 'success')
    failed_count = len(completed_results) - successful_count
    
    print(f"\n📊 Processing summary:")
    print(f"✅ Successfully processed: {successful_count} files")
    print(f"❌ Failed: {failed_count} files")
    print(f"⏱️ Total time: {total_processing_time:.2f}s")
    
    # Show detailed results
    print(f"\n📋 Detailed results:")
    for result in completed_results:
        if result['status'] == 'success':
            print(f"  Paper_{result['pdf_id']}: ✅ Success (time: {result['processing_time']:.2f}s)")
        else:
            print(f"  Paper_{result['pdf_id']}: ❌ Failed - {result['error']}")
    
    return completed_results

def run_sequential_processing():
    """Process all PDF files sequentially (original method)."""
    base_path = "./papersavings/"
    for pdf_id in range(1,6):
        if os.path.exists(base_path+"Paper_"+str(pdf_id)+".md"):
            print(f"Paper_{pdf_id} already exists, skipping...")
            continue
        print(f"Processing Paper_{pdf_id}...")
        main(pdf_id)

if __name__ == "__main__":
    import argparse
    
    # Add command-line argument support
    parser = argparse.ArgumentParser(description='Batch processing tool for Fischer-Tropsch knowledge graphs')
    parser.add_argument('--mode', choices=['parallel', 'sequential'], default='parallel',
                       help='Processing mode: parallel or sequential')
    # Tunable parameter 3: process files in parallel
    parser.add_argument('--workers', type=int, default=3,
                       help='Maximum number of worker processes for parallel mode (default: 3)')
    
    args = parser.parse_args()
    
    if args.mode == 'parallel':
        print(f"🚀 Starting parallel processing mode (max workers: {args.workers})")
        run_parallel_processing(max_workers=args.workers)
    else:
        print("🔄 Starting sequential processing mode")
        run_sequential_processing()
