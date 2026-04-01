import openai
import json
import argparse
import tqdm
import time
from openai import OpenAI
import requests
import os
import re

# 定义发送 POST 请求的函数
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
        return f"Error for path {path}: {str(e)}"
    
def llm_analysis(client, cur_prompt, ignore, args):
    while True:
        try:
            _response = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "system", "content": cur_prompt}],
                temperature=0.7,
                max_tokens=30,
                top_p=0.7,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                n=20  # 生成20个候选回答
            )
            time.sleep(10)
            # print('response', _response)
            # all_responses = [_response['choices'][i]['message']['content'] for i in
            #                  range(len(_response['choices']))]
            # instance['all_responses'] = all_responses
            # new_json.append(instance)
            # ct += 1
            # 关键修改：从对象属性获取响应内容，而不是字典索引
            all_responses = [choice.message.content for choice in _response.choices]
            print('all_responses', all_responses)
            # instance['all_responses'] = all_responses
            # new_json.append(instance)
            # # ct += 1
            return calculate_position_averages(all_responses)
        except Exception as e:
            print(e)
            if ("limit" in str(e)):
                time.sleep(2)
            else:
                ignore += 1
                print('ignored', ignore)

                break
    
import re

def calculate_position_averages(str_list, length=5):
    """
    计算字符串列表中每个位置分数的平均值
    每个字符串格式类似'Coherence: [4, 3, 5, 4, 3, 5]'，包含5个分数
    
    参数:
    str_list (list): 包含字符串的列表
    
    返回:
    list/None: 包含5个位置平均值的列表（保留两位小数），若无效则返回None
    """
    # 初始化6个位置的分数列表
    position_scores = [[] for _ in range(length)]
    
    # 匹配中括号内的数字列表
    pattern = re.compile(r'\[(.*?)\]')
    
    for s in str_list:
        # 提取中括号内的内容
        match = pattern.search(s)
        if not match:
            print(f"忽略格式不正确的字符串: {s}")
            continue
        
        # 提取数字部分并分割
        numbers_str = match.group(1)
        numbers_list = numbers_str.split(',')
        
        # 检查是否有6个分数
        if len(numbers_list) != length:
            print(f"忽略分数数量不正确的字符串（应为{length}个，实际{len(numbers_list)}个）: {s}")
            continue
        
        # 转换为数字并添加到对应位置
        for i in range(length):
            try:
                num = float(numbers_list[i].strip())
                position_scores[i].append(num)
            except ValueError:
                print(f"忽略无法转换的数字: {numbers_list[i]}（来自字符串: {s}）")
    
    # 计算每个位置的平均值
    averages = []
    for i in range(length):
        if not position_scores[i]:
            print(f"位置{i+1}没有有效分数")
            return None
        avg = sum(position_scores[i]) / len(position_scores[i])
        averages.append(round(avg, 2))
    
    return averages
    

def blog_reader(number, mk_type=None):
    if mk_type == "pure":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/pure/"+str(number)+".md"
    elif mk_type == "pure_simple":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/pure_simple/"+str(number)+".md"
    elif mk_type == "pure_simple_easy":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/pure_simple_easy/"+str(number)+".md"
    elif mk_type == "gpt":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/Paper_"+str(number)+".md"
    elif mk_type == "qwen":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/papersavings-gen/papersavings-qwen/Paper_"+str(number)+".md"
    elif mk_type == "ds":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/papersavings-gen/papersavings-ds/Paper_"+str(number)+".md"
    elif mk_type == "blog":
        save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/mmapis/"+str(number)+"-merge/blog.md"
    # if not os.path.exists(save_dir):
    #     save_dir = "./papersavings/Paper_"+str(num)+".md"
    with open(save_dir,"r",encoding="utf-8") as f:
        blog_content = f.read()

    from langchain.text_splitter import MarkdownHeaderTextSplitter
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        # ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        # strip_headers = False
        )
    splits = markdown_splitter.split_text(blog_content)
    # print(splits[0].page_content)
    return splits, blog_content

from typing import Union
def read_json_file(file_path: str) -> Union[dict, list, None]:
    """读取JSON文件并返回解析后的数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 不存在")
        with open(file_path, 'w', encoding='utf-8') as file:
            # data = json.load(file)
            return []
        
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {e}")
    except Exception as e:
        print(f"错误：读取文件时发生意外错误 - {e}")
    return []


def check_paper_id_exists(data: list[dict], paper_id: int) -> bool:
    """检查指定的 Paper_id 是否存在于 JSON 数据中"""
    return any(item.get("Paper_id") == paper_id for item in data)

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    # argparser.add_argument('--save_fp', type=str, default='results/gpt4o_pure_detailed_openai.json')
    argparser.add_argument('--summeval_fp', type=str, default='data/summeval.json')
    argparser.add_argument('--type_name', type=str, default=None)
    argparser.add_argument('--key', type=str, default="")
    argparser.add_argument('--model', type=str, default='gpt-4o-mini')
    # argparser.add_argument('--model', type=str, default='gpt-4.1-mini')
    args = argparser.parse_args()
    saving_path = './gval_results/all.json'
    summeval = json.load(open(args.summeval_fp))
    coh_prompt = """
You will be given a chemistry paper and 5 different experimental protocols generated from it.

Your task is to evaluate the **coherence** of each protocol individually, using a scale from 1 to 10.

---

### Definition of Coherence (1–10):

"Coherence" refers to how clearly and logically the experimental protocol presents information. A coherent protocol should have good structure, logical flow of experimental steps, and be easy to follow for reproduction.

Scoring guide:
10 = Exceptionally coherent; flawless structure and logical flow of procedures  
8–9 = Very coherent; only minor imperfections in step sequence  
6–7 = Generally coherent; a few noticeable issues in logical progression  
4–5 = Some structural or logical issues affecting reproducibility  
2–3 = Poor coherence; hard to follow the experimental sequence  
1 = Extremely incoherent; chaotic structure

---

### Input Chemistry Paper

{paper_text}

---

### Experimental Protocols

Protocol 1:  
{protocol_1}

Protocol 2:  
{protocol_2}

Protocol 3:  
{protocol_3}

Protocol 4:  
{protocol_4}

Protocol 5:  
{protocol_5}

---

### Output Format

Only output a Python-style list of coherence scores, in the following format:

Coherence: [score1, score2, score3, score4, score5]
"""
    con_prompt = """
You will be given a chemistry paper and 5 different experimental protocols written based on it.

Your task is to evaluate each protocol individually for **Consistency**, using a scale from 1 to 10.

---

### Definition of Consistency (1–10):

"Consistency" refers to how well the experimental protocol aligns factually with the source chemistry paper. A consistent protocol should accurately reflect the methods, materials, procedures, and experimental details described in the original research.

Scoring guide:
10 = Fully consistent; all experimental details match the paper  
8–9 = Mostly consistent; very minor deviations in non-critical details  
6–7 = Some inconsistencies in materials, methods, or procedures  
4–5 = Several factual inaccuracies affecting reproducibility  
2–3 = Many unsupported or hallucinated steps/materials  
1 = Entirely inconsistent with the source paper

---

### Source Chemistry Paper

{paper_text}

---

### Experimental Protocols

Protocol 1:  
{protocol_1}

Protocol 2:  
{protocol_2}

Protocol 3:  
{protocol_3}

Protocol 4:  
{protocol_4}

Protocol 5:  
{protocol_5}

---

### Output Format

Only output a Python-style list of consistency scores in the format below:

Consistency: [score1, score2, score3, score4, score5]
"""
    flu_prompt = """
You will be given 5 experimental protocols, each written for the same chemistry paper.

Your task is to evaluate each protocol individually for **Fluency**, using a scale from 1 to 10.

---

### Definition of Fluency (1-10):

"Fluency" refers to the grammatical, technical, and stylistic quality of the experimental protocol. Consider grammar, spelling, punctuation, precise scientific terminology, clarity of instructions, and logical sentence structure appropriate for laboratory documentation.

Scoring guide:
10 = Perfectly fluent; natural, error-free, and professionally presented
8-9 = Very fluent; only minor grammatical or terminological issues
6-7 = Mostly fluent; some noticeable errors but generally understandable
4-5 = Several grammatical, terminological, or clarity problems affecting comprehension
2-3 = Poor fluency; frequent or severe issues impeding understanding
1 = Very poor; extremely difficult to understand and follow

---
### Source Chemistry Paper

{paper_text}

---

### Experimental Protocols

Protocol 1:
{protocol_1}

Protocol 2:
{protocol_2}

Protocol 3:
{protocol_3}

Protocol 4:
{protocol_4}

Protocol 5:
{protocol_5}

---

### Output Format

Only output a Python-style list of fluency scores:

Fluency: [score1, score2, score3, score4, score5]
"""
    rel_prompt = """
You will be given a chemistry paper and 5 experimental protocols written based on it.

Your task is to evaluate each protocol individually for **Relevance**, using a scale from 1 to 10.

---

### Definition of Relevance (1-10):

"Relevance" refers to how well the experimental protocol includes important methodological information from the chemistry paper, and avoids redundancy or unrelated content.

Scoring guide:
10 = Covers all key experimental details with no irrelevant content  
8-9 = Covers most key methodological points; minor redundancy  
6-7 = Covers some main experimental steps; noticeable omissions  
4-5 = Limited relevance; some extraneous info or missing core procedures  
2-3 = Mostly irrelevant or overly verbose with unnecessary details  
1 = Completely off-topic or redundant

---

### Source Chemistry Paper

{paper_text}

---

### Experimental Protocols

Protocol 1:  
{protocol_1}

Protocol 2:  
{protocol_2}

Protocol 3:  
{protocol_3}

Protocol 4:  
{protocol_4}

Protocol 5:  
{protocol_5}

---

### Output Format

Only output a Python-style list of relevance scores:

Relevance: [score1, score2, score3, score4, score5]
"""

    ct, ignore = 0, 0

    # new_json = []
    # 创建客户端（新版本使用 OpenAI 类，不再是旧的 APIKey 全局配置）
    client = OpenAI(api_key=args.key)
    
    md_text = ""
    base_path = "/mnt/d/Phd/practice/mof_pack/origin_paper/more_paper/"
    paths = []
    for i in range(126):
        paths.append([base_path+str(i+1)+".pdf",base_path+str(i+1)+"-si.pdf"])
        # paths.append([base_path+str(i+1)+".pdf"])
    for num in tqdm.tqdm(range(1, 126)):
        
        my_json = read_json_file(saving_path)
        if check_paper_id_exists(my_json, num):
            print(f"Paper {num} 已存在，跳过处理。")
            continue
        print(f"正在处理 Paper {num}...")
        # num = 1
        ignore = num
        path_set = paths[num-1]
        md_text = ""
        for path in path_set:
            if os.path.exists(path):
                print(path)
                md_text += send_post_request(path)+"\n\n"
                cleaned_text = re.sub(r'!\[.*?\]\(.*?\)', r'![]()', md_text)
                cleaned_text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'![]()', cleaned_text)
                cleaned_text = re.sub(r'!\[([^\]]*)\]\[[^\]]*\]', r'![]()', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\\\[\\\[\d+\\\]\\\]\(\#page-\d+-\d+\)', ',', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[\\\[(\d+)\\\]\]\(#page-\d+-\d+\)', r'[\1]', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[\[(\d+)\]\]\(#page-\d+-\d+\)', r'[\1]', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[(\d+)\]\(#page-\d+-\d+\)', r'\1', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[\\\((\d+)\\\)\]\(#page-\d+-\d+\)', r'(\1)', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[\((\d+)\)\]\(#page-\d+-\d+\)', r'(\1)', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[([^\]]+)\]\([^)]+\)', r'\1', cleaned_text)
                cleaned_text = re.sub(r'(?<!\!)\[(.*?)\]\(#[^)]+\)', r'\1', cleaned_text)
                cleaned_text = re.sub(r'\\([()])', r'\1', cleaned_text)
                cleaned_text = re.sub(r'<([a-zA-Z0-9]+)>(.*?)</\1>', r'\2', cleaned_text)
                md_text = re.sub(r'<span\s+id=(?:"[^"]*"|\'[^\']*\')[^>]*></span>', '', cleaned_text).strip()
        # save_dir = "/mnt/d/Phd/practice/mof_pack/papersavings/Paper_"+str(num)+".md"
        # with open(save_dir,"r",encoding="utf-8") as f:
        #     report_content = f.read()
        types = [
            # 'qwen',
            # 'ds',
            'gpt',
            'pure_simple_easy',
            'pure_simple',
            'pure',
            'blog',
        ]
        reports = []
        for type_name in types:
            blog_splits, report_content = blog_reader(num, type_name)
            reports.append(report_content)
        
        instance = {}
        instance["Paper_id"] = num
        # instance['source'] = md_text
        # instance['system_output'] = report_content
        # for instance in tqdm.tqdm(summeval):
        #     source = instance['source']
        #     system_output = instance['system_output']
        cur_con_prompt = con_prompt.replace('{paper_text}', md_text).replace('{protocol_1}', reports[0]).replace('{protocol_2}', reports[1]).replace('{protocol_3}', reports[2]).replace('{protocol_4}', reports[3]).replace('{protocol_5}', reports[4])
        cur_coh_prompt = coh_prompt.replace('{paper_text}', md_text).replace('{protocol_1}', reports[0]).replace('{protocol_2}', reports[1]).replace('{protocol_3}', reports[2]).replace('{protocol_4}', reports[3]).replace('{protocol_5}', reports[4])
        cur_flu_prompt = flu_prompt.replace('{paper_text}', md_text).replace('{protocol_1}', reports[0]).replace('{protocol_2}', reports[1]).replace('{protocol_3}', reports[2]).replace('{protocol_4}', reports[3]).replace('{protocol_5}', reports[4])
        cur_rel_prompt = rel_prompt.replace('{paper_text}', md_text).replace('{protocol_1}', reports[0]).replace('{protocol_2}', reports[1]).replace('{protocol_3}', reports[2]).replace('{protocol_4}', reports[3]).replace('{protocol_5}', reports[4])
            # cur_prompt = prompt.replace('{{Document}}', source).replace('{{Summary}}', system_output)
        # instance['prompt'] = cur_prompt
        # print('cur_prompt', cur_prompt)
            # break
            
        # con_score = llm_analysis(client, cur_con_prompt, ignore, args)
        # coh_score = llm_analysis(client, cur_coh_prompt, ignore, args)
        # flu_score = llm_analysis(client, cur_flu_prompt, ignore, args)
        # rel_score = llm_analysis(client, cur_rel_prompt, ignore, args)
        from concurrent import futures

        # 定义要执行的函数和参数
        tasks = [
            (llm_analysis, client, cur_con_prompt, ignore, args),
            (llm_analysis, client, cur_coh_prompt, ignore, args),
            (llm_analysis, client, cur_flu_prompt, ignore, args),
            (llm_analysis, client, cur_rel_prompt, ignore, args)
        ]

        # 并行执行所有任务
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有任务并获取 Future 对象列表
            futures_list = [executor.submit(func, *args) for func, *args in tasks]
            
            # 获取所有结果（按提交顺序排列）
            con_score, coh_score, flu_score, rel_score = [future.result() for future in futures_list]
        
        instance['con_score'] = con_score
        instance['coh_score'] = coh_score
        instance['flu_score'] = flu_score
        instance['rel_score'] = rel_score
        my_json.append(instance)
        # print('ignored total', ignore)
        with open(saving_path, 'w') as f:
            json.dump(my_json, f, indent=4)
    # with open(saving_path, 'w') as f:
    #     json.dump(new_json, f, indent=4)
