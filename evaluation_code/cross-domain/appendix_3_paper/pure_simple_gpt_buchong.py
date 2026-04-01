
import os
import time
import re
import requests
import argparse
import logging
import sys
sys.path.append(os.path.join(os.path.dirname("..")))
from graph_utils.chatgpt.config.config import (
    GENERAL_CONFIG,
    OPENAI_CONFIG,
    ARXIV_CONFIG,
    NOUGAT_CONFIG,
    # DOCUMENT_PROMPTS,
    # SECTION_PROMPTS,
    # ALIGNMENT_CONFIG,
    LOGGER_MODES,
    APPLICATION_PROMPTS,
)
from graph_utils.chatgpt.utils import init_logging
# from fsm_generation.fsm_generator import Manager
from graph_utils.graph_generate_bak import Knowledge_Graph
from tqdm import *
import json
# # Initialize logging
# init_logging()
# logger = logging.getLogger(__name__)
# logger.setLevel(LOGGER_MODES)

# Load configurations, giving priority to command line arguments
api_key = OPENAI_CONFIG['api_key']
base_url = OPENAI_CONFIG['base_url']
organization = OPENAI_CONFIG['organization']
pdf_ls = NOUGAT_CONFIG['pdf']
keyword = ARXIV_CONFIG['key_word']
download = True
daily_type = ARXIV_CONFIG['daily_type']
run_all = True
specific_app = "blog"
recompute = True
# Validate API key and base URL
if not (api_key and base_url):
    raise ValueError("API key and base URL must be provided either via --api_key and --base_url or in the config file.")



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
    
# for path_set in paths:
# print(paths)

def main(num, subject = "cof"):
    
    base_path = f"/mnt/d/Phd/practice/mof_pack/to_zhao/{subject}/"
    paths = []
    for i in range(20):
        paths.append([base_path+str(i+1)+".pdf",base_path+str(i+1)+"-si.pdf"])
    
    if os.path.exists(f"./to_zhao/{subject}_compare/{num}.md"):
        print(f"File for paper {num} already exists, skipping...")
        return
    md_text = ""
    print(f"Processing paper {num}...")
    path_set = paths[num-1]
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

    if subject == "cof":
        prompt = """Generate a structured report based on the provided COF synthesis research paper and template by:  
1. Extracting key information (monomer composition, synthesis conditions, characterization data, performance metrics, mechanism insights) from the paper.  
2. Populating template sections with relevant data, maintaining scientific accuracy and terminology specific to Covalent Organic Framework research.  
3. Ensuring logical flow and alignment with template structure (introduction, experimental, characterization, performance, conclusion).  

Input:  
- Paper text (COF synthesis focused)  

<Content of the paper in markdown format>
{CONTENT}
</Content of the paper in markdown format>

- Report template structure  

<Template structure>
{TEMPLATE}
</Template structure>

Output:  
Fully populated report following the template, integrating data from the paper while preserving chemical precision and academic tone.  """
    elif subject == "mof":
        prompt = """Generate a structured report based on the provided Metal-Organic Framework (MOF) research paper and template by:  
1. Extracting key information (MOF composition, synthesis methods, characterization data, performance metrics, mechanism insights) from the paper.  
2. Populating template sections with relevant data, maintaining scientific accuracy and terminology specific to MOF research.  
3. Ensuring logical flow and alignment with template structure (introduction, methodology, results, discussion, conclusion).  

Input:  
- Paper text (MOF synthesis, characterization, and application focused)  

<Content of the paper in markdown format>
{CONTENT}
</Content of the paper in markdown format>

- Report template structure  

<Template structure>
{TEMPLATE}
</Template structure>

Output:  
Fully populated report following the template, integrating data from the paper while preserving chemical precision and academic tone."""
    elif subject == "ows":
        prompt = """Generate a structured report based on the provided Overall Water Splitting (OWS) paper and template by:
1.  Extracting key information (photocatalyst design & composition, synthesis method, system architecture, characterization results, performance metrics, and mechanistic insights) from the paper.
2.  Populating template sections with relevant data, maintaining scientific accuracy and terminology specific to photocatalytic or photoelectrochemical Overall Water Splitting.
3.  Ensuring logical flow and alignment with the OWS-specific template structure.

**Input:**
- **Paper text** (Overall Water Splitting focused)
```
<Content of the paper in markdown format>
{CONTENT}
</Content of the paper in markdown format>
```

- **Report template structure** (OWS-specific)
```
<Template structure>
{TEMPLATE}
</Template structure>
```

Output:  
Fully populated report following the template, integrating data from the paper while preserving chemical precision and academic tone."""

    
    knowledge_graph = Knowledge_Graph(markdown=md_text,type_name="FT Framework", filtered=False)
    text_list = []
    for split in knowledge_graph.splits:
        text_list.append(split.page_content)
    text = "\n\n".join(text_list)

    
    file_name = f"./template/{subject.upper()}.md"
    with open(file_name, 'r') as file:
        template = file.read()
    prompt = prompt.replace("{CONTENT}", text).replace("{TEMPLATE}", template)
    # print(prompt)

    
    result  = knowledge_graph.graphllm.invoke(prompt)
    # print(result)

    
    resulttext = result.content.replace("```markdown", "").replace("```", "")
    with open(f"./to_zhao/{subject}_compare/{num}.md", 'w') as file:
        file.write(resulttext)
if __name__ == "__main__":
    for num in range(1, 10):
        main(num)


