from langchain.text_splitter import CharacterTextSplitter,MarkdownTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader,UnstructuredMarkdownLoader
from langchain_community.document_loaders import UnstructuredPDFLoader
# from langchain.document_loaders import UnstructuredImageLoader
from rapidocr_onnxruntime import RapidOCR
from langchain.text_splitter import TokenTextSplitter, RecursiveCharacterTextSplitter, CharacterTextSplitter, MarkdownHeaderTextSplitter
# from .chatgpt.chatgpt_helper import GPTHelper
from .chatgpt.config.config import (
    # GENERAL_CONFIG,
    # ARXIV_CONFIG,
    # NOUGAT_CONFIG,
    APPLICATION_PROMPTS,
    SPLIT_CONFIG,
)

def read_file(path):
    # print(path)
    with open(path, 'r', encoding='utf-8') as file:
        data = file.read()
    return data

#加载md文件
def load_md_file(md_file):    
    loader = UnstructuredMarkdownLoader(md_file)
    docs = loader.load()
    print(docs[0].page_content[:100])
    return docs
#加载txt文件
def load_txt_file(txt_file):    
    loader = UnstructuredFileLoader(txt_file)
    docs = loader.load()
    print(docs[0].page_content[:100])
    return docs
#加载pdf文件
def load_pdf_file(pdf_file):    
    loader = UnstructuredPDFLoader(pdf_file)
    docs = loader.load()
    print('pdf:\n',docs[0].page_content[:100])
    return docs
#加载jpg文件
def load_jpg_file(jpg_file):
    ocr = RapidOCR()
    result,_ = ocr(jpg_file)
    docs = ""
    if result:
        ocr_result = [line[1] for line in result]
        docs += "\n".join(ocr_result)
        print('jpg:\n',docs[:100])
    return docs

#分割md文件
def load_md_splitter(md_file, chunk_size=1024, chunk_overlap=20):
    docs = load_md_file(md_file)
    text_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(docs)
    #默认展示分割后第一段内容
    print('split_docs[0]: ', split_docs[0])
    return split_docs
#分割txt文件
def load_txt_splitter(txt_file, chunk_size=1024, chunk_overlap=20):
    docs = load_txt_file(txt_file)
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(docs)
    #默认展示分割后第一段内容
    print('split_docs[0]: ', split_docs[0])
    return split_docs
#分割pdf文件
def load_pdf_splitter(pdf_file, chunk_size=1024, chunk_overlap=20):
    docs = load_pdf_file(pdf_file)
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(docs)
    #默认展示分割后第一段内容
    print('split_docs[0]: ', split_docs[0])
    return split_docs
#分割jpg文件
def load_jpg_splitter(jpg_file, chunk_size=1024, chunk_overlap=20):
    docs = load_jpg_file(jpg_file)
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.create_documents([docs])
    #默认展示分割后第一段内容
    print('split_docs[0]: ', split_docs[0])
    return split_docs

# class llm_tools():
#     def __init__(self,
#                  api_key,
#                  base_url,
#                  organization,
#                  model_config:dict={},
#                  proxy:dict = None,
#                  prompt_ratio:float = 0.8,
#                  **kwargs):
#         self.generator = GPTHelper(api_key=api_key,
#                                             base_url=base_url,
#                                             organization=organization,
#                                             model_config=model_config,
#                                             proxy=proxy,
#                                             prompt_ratio=prompt_ratio,
#                                             **kwargs)
#     def filter(self, text:str):
#         gen_prompts = APPLICATION_PROMPTS["decompose_prompts"]
#         system_messages = [gen_prompts.get("system_prompt", '')]
#         self.generator.init_messages("system", system_messages)
#         user_input = gen_prompts.get("content_filter", '').replace('{content}', text, 1)

#         flag, generate =  self.generator.request_text_api(user_input=user_input,
#                                               reset_messages=True,
#                                               response_only=True,
#                                               )
#         return generate
    
#     def batch_filter(self, text):
#         gen_prompts = APPLICATION_PROMPTS["decompose_prompts"]
#         system_messages = [gen_prompts.get("system_prompt", '')]
#         self.generator.init_messages("system", system_messages)
#         user_input = []
#         for t in text:
#             user_input.append(gen_prompts.get("content_filter", '').replace('{content}', t, 1))

#         flag, generate =  self.generator.multi_request(article_texts=user_input,
#                                                         reset_messages=True,
#                                                         response_only=True,
#                                               )
#         return generate

# def load_md_filtered(path):
#     # Load configurations, giving priority to command line arguments
#     api_key = SPLIT_CONFIG['api_key']
#     base_url = SPLIT_CONFIG['base_url']
#     organization = SPLIT_CONFIG['organization']
#     # pdf_ls = NOUGAT_CONFIG['pdf']
#     # save_dir = GENERAL_CONFIG['save_dir']
#     # keyword = ARXIV_CONFIG['key_word']
#     download = True
#     # daily_type = ARXIV_CONFIG['daily_type']
#     run_all = True
#     specific_app = "blog"
#     recompute = True
#     model_config = SPLIT_CONFIG["model_config"]
#     # llm = llm_tools(api_key=api_key, 
#     #                 base_url=base_url, 
#     #                 organization=organization, 
#     #                 model_config=model_config, 
#     #                 # proxy=GENERAL_CONFIG["proxy"]
#     #                 )
#     markdown_document = read_file(path)
    
#     headers_to_split_on = [
#         ("#", "Header 1"),
#         ("##", "Header 2"),
#         ("###", "Header 3"),
#     ]
#     markdown_splitter = MarkdownHeaderTextSplitter(
#         headers_to_split_on=headers_to_split_on,
#         # strip_headers = False
#         )
#     rs = markdown_splitter.split_text(markdown_document)
    
#     for content in rs:
#         content.page_content = llm.filter(content.page_content)
        
#     return rs

def load_md_no_filtered_batch(path):
    markdown_document = read_file(path)
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        # strip_headers = False
        )
    rs = markdown_splitter.split_text(markdown_document)
        
    return rs

def load_md_filtered_batch(path):
    # Load configurations, giving priority to command line arguments
    # api_key = SPLIT_CONFIG['api_key']
    # base_url = SPLIT_CONFIG['base_url']
    # organization = SPLIT_CONFIG['organization']
    # pdf_ls = NOUGAT_CONFIG['pdf']
    # save_dir = GENERAL_CONFIG['save_dir']
    # keyword = ARXIV_CONFIG['key_word']
    # download = True
    # daily_type = ARXIV_CONFIG['daily_type']
    # run_all = True
    # specific_app = "blog"
    # recompute = True
    # model_config = SPLIT_CONFIG["model_config"]
    markdown_document = read_file(path)
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        # strip_headers = False
        )
    rs = markdown_splitter.split_text(markdown_document)
    
    # llm = llm_tools(api_key=api_key, base_url=base_url, organization=organization, model_config=model_config, proxy=GENERAL_CONFIG["proxy"])
    # input_text = []
    # for content in rs:
    #     input_text.append(content.page_content)
    # output_text = llm.batch_filter(input_text)
    
    # for output, content in zip(output_text, rs):
    #     content.page_content = output
        
    return rs
        
def split_md_filtered(doc):
    chunk_size = 2048
    chunk_overlap = 256
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    # Split
    splits = text_splitter.split_documents(doc)
    for index in range(len(splits) - 1, -1, -1):  # 从后向前遍历
        if len(splits[index].page_content) < 30:
            # print(splits[index].page_content)
            del splits[index]
    return splits
        
    