
import requests
from graph_utils.graph_generate_bak import Knowledge_Graph
import os, json, re
from langchain.schema import HumanMessage
from langchain.text_splitter import MarkdownHeaderTextSplitter
multi_gen_info = """
### ✅ Task Objective
Please complete the following two tasks:

1. **Content Analysis**: Analyze the input provided by the user, including:
   * **[Multiple Report Contents]**: Denoted as `report_contents` (an array containing one or more report texts, all derived from the same original article)
   * **[Questionnaire Problem List]**: Denoted as `eval_paper` (a list of questions to be evaluated)

2. **Information Extraction**: For each questionnaire question in `eval_paper`, list the specific information points that need to be retrieved from the `report_contents` to answer the question. Requirements:
   * Information points should be clear and extractable declarative content.
   * Avoid vague wording such as "whether", "have or not" and other judgmental words.
   * Information points need to be specific, such as "catalyst type", "support characterization method", "experimental temperature value", etc.
   * Since all `report_contents` come from the same article, there is no need to distinguish which specific report an information point comes from; focus on collecting all relevant content.


### ✅ Input Content
```python
{
  "report_contents": [
    "{report_contents}"  # All reports are from the same original article
  ],
  "eval_paper": [{question_text}]
}
```


### ✅ Output Format
Output a JSON object containing the field:
```json
{
    "retrieve_info": [
    "<Specific information point 1 to be retrieved (e.g., 'Catalyst synthesis steps')>",
    "<Specific information point 2 to be retrieved (e.g., 'XRD characterization conditions')>",
    ...
    ]
}
```

> If a question does not involve clear information points from any report, set `retrieve_info` as an empty array: `[]`


### ✅ Example
#### Input:
```json
{
  "report_contents": [
    "Report 1: This study uses Fe-based catalysts. The particle size was characterized by TEM as 50nm, and the reaction temperature was 300℃.",
    "Report 2: SiO₂ was used as the support. XRD tests were conducted with a scanning rate of 10°/min, and CO conversion reached 60%."
  ],
  "eval_paper": ["What characterization methods and reaction parameters are involved in the reports?"]
}
```

#### Output:
```json
{
    "retrieve_info": [
    "Catalyst type (Fe-based catalyst)",
    "Particle size characterization method (TEM) and corresponding data (50nm)",
    "Reaction temperature (300℃)",
    "Support type (SiO₂)",
    "XRD characterization condition (scanning rate 10°/min)",
    "CO conversion data (60%)"
    ]
}
```


### ✅ Instruction Tips
* Since all `report_contents` are from the same article, focus on integrating information across reports rather than distinguishing their sources. For example, if "reaction pressure" is mentioned in both report 1 and report 2, extract it as a unified information point like "reaction pressure value".
* For questions requiring comprehensive information, collect all related content from all reports. For example:
  * Question: "What are the characterization methods used in the study?"
  * Parsed into retrieval points: ["TEM characterization details", "XRD testing conditions", "Other characterization methods mentioned (e.g., XPS, BET)"]
* Information points should be as specific as possible to the experimental or data description level, such as "reduction atmosphere composition", "catalyst activation time", "product selectivity data", etc.
* Avoid redundant duplication of the same information across different reports (e.g., if two reports mention the same reaction temperature, extract it once as "reaction temperature value").
```
"""
multi_get_answer = """### ✅ Task Objective

Please complete a questionnaire scoring task based on literature comparison for multiple reports, involving three input pieces of information:

1. **Multiple report original texts (report_contents)**: An array of Fischer-Tropsch synthesis experimental reports submitted by the user (**exactly 5 reports**, each report is an independent text to be evaluated).
2. **Questionnaire questions (eval_paper)**: Scoring questions for evaluating the reports.
3. **Paper retrieval information (paper_info)**: Support data provided by the user from references or original papers, used to verify the accuracy of each report.

---

### ✅ Input Format

The input is a JSON object containing the following fields:

```json
{
  "report_contents": [
    "{report_contents}"  // N is the number of reports to be evaluated
  ],
  "eval_paper": [{question_text}],
  "paper_info": [{paper_info}]
}
```

---

### ✅ Output Format

⚠️ **Your response must be strictly a valid JSON object and nothing else. Do not include explanations, markdown, comments, or any other format outside the JSON block.**

```json
{
  "questions": [
    {
      "question_text": "<Original questionnaire question>",
      "score_suggestion": [
        <integer 1 to 10>,  // Score for report_contents[0]
        <integer 1 to 10>,  // Score for report_contents[1]
        ...  // Scores for other reports in order
      ]
    },
    ...  // Evaluations for other questions
  ]
}
```

> The length of `score_suggestion` array must be consistent with the length of `report_contents` array, and the order of scores corresponds to the order of reports in `report_contents`.

---

### ✅ Scoring Criteria

| Score Range | Description                                                                                                                     |
|-------------|---------------------------------------------------------------------------------------------------------------------------------|
| 9-10        | Report is fully consistent with the paper, with complete, clear, and rigorous logic; all key data and references are accurately presented. |
| 6-8         | Report is generally consistent with the paper but has minor differences in wording, trivial missing details, or slightly unclear citations of non-critical information. |
| 1-5         | Report deviates from the paper significantly, lacks key information, contains obvious data errors, or fails to cite necessary sources. |

---

### ✅ Processing Instructions

For each questionnaire question in `eval_paper` and each report in `report_contents` (in order):

1. Locate relevant content in the current report (from `report_contents`) and `paper_info`.
2. Compare the report's values, methods, conditions, and citations with the paper information.
3. Generate a scoring suggestion (1-10) for the current report on the current question, referring to the scoring criteria.
4. Collect scores for all reports in the order of `report_contents` into the `score_suggestion` array of the corresponding question.
5. Return the result in **strict JSON** format as defined above.

---

### ❌ Forbidden Output

* Do **not** include any text outside the JSON block.
* Do **not** include explanations, formatting (e.g., Markdown), or non-JSON commentary.
* Do **not** change the order of scores in `score_suggestion` (must match the order of `report_contents`).
* Do **not** make the length of `score_suggestion` inconsistent with `report_contents`.

---

### ✅ Example Input:

```json
{
  "report_contents": [
    "Report 1: The C5+ selectivity of catalyst B is 75%, consistent with Table 3 of the paper (250℃, 1.5MPa).",
    "Report 2: The C5+ selectivity of catalyst B is 60%, which differs from the paper data."
  ],
  "eval_paper": ["Does the report accurately reference the paper for the selectivity data of catalyst B? (1-10 points)"],
  "paper_info": ["Table 3 of the paper: The C5+ selectivity of catalyst B at 250℃ and 1.5MPa is 75%."]
}
```

### ✅ Expected Output:

```json
{
  "questions": [
    {
      "question_text": "Does the report accurately reference the paper for the selectivity data of catalyst B? (1-10 points)",
      "score_suggestion": [10, 3]
    }
  ]
}
```"""
multi_get_answer_no_info = """
### ✅ Task Objective  
Complete a questionnaire scoring task based on literature comparison for multiple reports, involving two input pieces of information:  
1. **Multiple report original texts (report_contents)**: An array of Fischer-Tropsch synthesis experimental reports submitted by the user (**exactly 5 reports**, each report is an independent text to be evaluated).
2. **Questionnaire questions (eval_paper)**: Scoring questions for evaluating the reports.  

---  
### ✅ Input Format  
The input is a JSON object containing the following fields:  
```json
{
  "report_contents": [
    "{report_contents}"  // N is the number of reports to be evaluated
  ],
  "eval_paper": [{question_text}]
}
```  

---  
### ✅ Output Format  
The output is a JSON object containing scoring suggestions for each report in order:  
```json
{
  "questions": [
    {
      "question_text": "<Original questionnaire question>",
      "score_suggestion": [
        <integer 1~10>,  // Score for report_contents[0]
        <integer 1~10>,  // Score for report_contents[1]
        ...  // Scores for other reports in order
      ]
    },
    ...  // Evaluations for other questions
  ]
}
```  
> The length of `score_suggestion` must be consistent with the length of `report_contents`, and the order of scores corresponds to the order of reports in `report_contents`.  

---  
### ✅ Scoring Criteria  
| Score Range | Description                                                                                     |  
|-------------|-------------------------------------------------------------------------------------------------|  
| 9-10        | Data in the report is completely accurate; content is comprehensive, logic is rigorous, and all key information is clearly presented. |  
| 6-8         | The report is generally consistent with standard requirements, but has minor expression differences, trivial detail omissions, or slightly unclear descriptions of non-critical information. |  
| 1-5         | There are obvious deviations in core data, missing critical information, logical contradictions, or major errors in key content. |  

---  
### ✅ Processing Steps  
For each questionnaire question and each report in `report_contents` (in order):  
1. **Locate relevant content**: Identify paragraphs in the current report related to the question.  
2. **Evaluation and verification**:  
   - Check accuracy of core data, completeness of description, and rigor of logic in the report.  
   - Identify issues such as data deviations, missing information, or logical flaws.  
3. **Generate scoring suggestions**:  
   - Assign a score of 1–10 to the current report based on the evaluation results, referring to the scoring criteria.  
   - Collect scores for all reports in the order of `report_contents` into the `score_suggestion` array of the corresponding question.  

---  
### ✅ Example  
#### Input:  
```json
{
  "report_contents": [
    "Report 1: Catalyst B shows CO conversion 70% and C5+ selectivity 75%, consistent with standard data; all test conditions are clearly recorded.",
    "Report 2: Catalyst B has CO conversion 60% (deviating from standard 70%) and C5+ selectivity 65%, with no record of test conditions."
  ],
  "eval_paper": ["Does the report accurately present key data and basic test information of catalyst B? (1-10 points)"]
}
```  

#### Output:  
```json
{
  "questions": [
    {
      "question_text": "Does the report accurately present key data and basic test information of catalyst B? (1-10 points)",
      "score_suggestion": [10, 3]
    }
  ]
}
```"""
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

def split_markdown_by_headers(paper_content, headers_to_split_on):
    """
    根据指定的Markdown标题层级分割文本
    :param paper_content: 要分割的Markdown内容
    :param headers_to_split_on: 标题层级列表，格式如[("#", "Header 1"), ("##", "Header 2")...]
    :return: 分割后的文本块列表
    """
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return splitter.split_text(paper_content)

def check_paper_id_exists(data: list[dict], paper_id: int) -> bool:
    """检查指定的 Paper_id 是否存在于 JSON 数据中"""
    return any(item.get("Paper id") == paper_id for item in data)

def multi_calculate_average_score(answers, answer_id_range, expected_length, score_length):
    """计算指定答案ID范围内的平均分数"""
    # score = 0
    count = 0
    scores = []
    
    for response in answers:
        try:
            # 清理JSON格式并解析
            clean_response = response.replace("```json", "").replace("```", "").strip()
            answer = json.loads(clean_response)["questions"]
            valid = True
            for single_answer in answer:
                if len(single_answer['score_suggestion']) != score_length:
                    valid = False  # 如果有任何一个答案的分数长度不符合预期，则标记为无效
                    break  # 跳过不符合预期长度的答案
            if not valid:
                continue
            # 验证答案长度
            if len(answer) != expected_length:
                continue
                
            # 累加分数
            for answer_id in range(answer_id_range[0], answer_id_range[1]):
                if len(scores)<=answer_id-answer_id_range[0]:
                    scores.append(answer[answer_id]['score_suggestion'])
                else:
                    scores[answer_id-answer_id_range[0]] = [a + b for a, b in zip(scores[answer_id-answer_id_range[0]], answer[answer_id]['score_suggestion'])]
            count += 1
        except (json.JSONDecodeError, KeyError, IndexError, AssertionError):
            continue  # 跳过格式错误的响应
    try:
        scores = [[round(num/count, 2) for num in score] for score in scores]
        return scores, count
    except:
        return [], 0

def multi_generate_and_evaluate(knowledge_graph, small_answer, eval_small_dict, index, score_length, max_retries=5):
    """生成评估回答并计算分数，处理count为0的重试情况"""
    complete_eval_answer = []
    correction_eval_answer = []
    retries = 0
    
    while retries <= max_retries:
        # 调用大模型生成评估回答
        eval_answer = knowledge_graph.evalllm.generate([[HumanMessage(content=small_answer)]])
        candidate_eval_answer = [generation.text for generation in eval_answer.generations[0]]
        
        # 计算第一部分答案的平均分数
        answer_range1 = (eval_small_dict[str(index)][0], eval_small_dict[str(index)][1])
        expected_length = eval_small_dict[str(index)][1] + eval_small_dict[str(index)][3]
        if (retries==0) or (retries>0 and count1==0):
            score1, count1 = multi_calculate_average_score(
                candidate_eval_answer, 
                answer_range1,
                expected_length,
                score_length=score_length
            )
        
            if count1 > 0:
                complete_eval_answer+=score1
        
        # 计算第二部分答案的平均分数
        answer_range2 = (
            eval_small_dict[str(index)][1] + eval_small_dict[str(index)][2],
            eval_small_dict[str(index)][1] + eval_small_dict[str(index)][3]
        )
        
        if (retries==0) or (retries>0 and count2==0):
            score2, count2 = multi_calculate_average_score(
                candidate_eval_answer, 
                answer_range2,
                expected_length,
                score_length=score_length
            )
            
            if count2 > 0:
                correction_eval_answer+=score2
        
        # 检查是否需要重试
        if count1 > 0 and count2 > 0:
            break  # 有有效分数，无需重试
        
        retries += 1
        if retries > max_retries:
            print(f"警告：问题{index}重试{max_retries}次后仍无有效分数")
            break
        
        # 重试生成回答
        print(f"问题{index} count为0，正在重试生成回答... (第{retries}次)")

    return complete_eval_answer, correction_eval_answer

def main(
        num, 
        eval_paper_save_dir = "./evaluation_paper_all_results.json",
        save_dir = None,
        name = "Generation"
    ):
    if os.path.exists(eval_paper_save_dir):
        with open(eval_paper_save_dir,"r") as f:
            data = json.load(f)
        if check_paper_id_exists(data, num):        
            print(f"{name} Paper {num} 已存在，跳过处理。")
            return 
    print(f"正在处理{name}  Paper {num}...")
    md_text = ""
    base_path = "./origin_paper/more_paper/"
    paths = []
    for i in range(125):
        paths.append([base_path+str(i+1)+".pdf",base_path+str(i+1)+"-si.pdf"])
    # for path_set in paths:
    # print(paths)
    path_set = paths[num-1]
    for path in path_set:
        if os.path.exists(path):
            # print(path)
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

    knowledge_graph = Knowledge_Graph(markdown=md_text,type_name="FT Framework", filtered=False)

    reports = []
    reports_splits = []

    save_dirs = [
                "./papersavings/Paper_"+str(num)+".md",
                "./papersavings/pure/"+str(num)+".md",
                "./papersavings/pure_simple/"+str(num)+".md",
                "./papersavings/pure_simple_easy/"+str(num)+".md",
                "./papersavings/mmapis/"+str(num)+"-merge/blog.md"
                ]
    for save_dir in save_dirs:
        with open(save_dir,"r",encoding="utf-8") as f:
            report_content = f.read()

        from langchain.text_splitter import MarkdownHeaderTextSplitter
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            # ("###", "Header 3"),
            # ("####", "Header 4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            # strip_headers = False
            )
        splits = markdown_splitter.split_text(report_content)
        
        # if len(splits) != 6:
        #     print(f"Warning: {save_dir} does not have 6 splits, found {len(splits)}. Skipping this file. File is {num}.")
        #     return 
        
        # print(report_content)
        # print(splits[0].page_content)
        reports.append(report_content)
        reports_splits.append(splits)

    eval_paper_path = './template/FT/evaluation/all_paper_en.md'
    with open(eval_paper_path, "r", encoding="utf-8") as f:
        paper_content = f.read()

    # 定义两种不同的标题分割配置
    small_headers = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
        ("#####", "Header 5"),
    ]

    regular_headers = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    # 获取两种分割结果
    eval_small_splits = split_markdown_by_headers(paper_content, small_headers)
    eval_splits = split_markdown_by_headers(paper_content, regular_headers)

    # 保留原有的变量提取逻辑
    # scoring = eval_splits[-1]
    functional_eval = eval_splits[-3]
    format_normativeness = eval_splits[-4]
    eval_dict = {
        '0': [0, 5],
        '1': None,
        '2': [1, 6],
        '3': [2, 6],
        '4': [3, 6],
        '5': [4, 7],
        'format': 6,
        'functional': 5
    }
    eval_small_dict = {
        '0':[0, 7, 0, 3],
        '1':None,
        '2':[0, 4, 0, 2],
        '3':[0, 3, 0, 2],
        '4':[0, 2, 0, 2],
        '5':[0, 1, 0, 1]
    }

    complete_eval_answer = []
    correction_eval_answer = []
    format_eval_score = []
    functional_eval_score = []
    splits_num = 6
    for index in range(splits_num):
        eval_question_list = eval_dict[str(index)]
        if not eval_question_list:
            continue
        paper_question = "Content Completeness Questions:\n"+eval_small_splits[eval_question_list[0]].page_content+"\nInformation Accuracy:\n"+eval_small_splits[eval_question_list[1]].page_content
        # print(paper_question)
        extracted_splits = [sublist[index].page_content for sublist in reports_splits[:-2]]+reports[-2:]
        # extracted_splits = reports
        gen_info_prompt = multi_gen_info.replace("{report_contents}", "\",\n\"".join(extracted_splits)).replace("{question_text}", paper_question)
        # print(gen_info_prompt)
        origin_paper_info = knowledge_graph.minillm.invoke(gen_info_prompt).content.replace("```json","").replace("```","")
        origin_paper_info = "\n".join(json.loads(origin_paper_info)["retrieve_info"])
        # print(origin_paper_info)
        origin_paper_answer = knowledge_graph.structured_retriever(origin_paper_info, knowledge_graph.minillm)
        # print(f"original answer: {origin_paper_answer}")    
        small_answer = multi_get_answer.replace("{report_contents}", "\",\n\"".join(extracted_splits)).replace("{question_text}", paper_question).replace("{paper_info}", origin_paper_answer)
        # print(f"small_answer: {small_answer}")
        complete_scores, correction_scores = multi_generate_and_evaluate(
            knowledge_graph,
            small_answer, 
            eval_small_dict, 
            index,
            score_length=len(reports_splits)
        )
        complete_eval_answer+=complete_scores
        correction_eval_answer+=correction_scores
        # eval_answer = knowledge_graph.evalllm.generate([[HumanMessage(content=small_answer)]])
        
        # candidate_eval_answer = [generation.text for generation in eval_answer.generations[0]]
        # for answer_id in range(eval_small_dict[str(index)][0], eval_small_dict[str(index)][1]):
        #     score = 0
        #     count = 0
        #     for idx, response in enumerate(candidate_eval_answer, 1):
        #         answer = json.loads(response.replace("```json",'').replace("```",''))["questions"]
        #         if len(answer) != eval_small_dict[str(index)][1]+eval_small_dict[str(index)][3]:
        #             continue
        #         score += answer[answer_id]['score_suggestion']
        #         count += 1
        #     complete_eval_answer.append(round(score/count, 2))
        # for answer_id in range(eval_small_dict[str(index)][1]+eval_small_dict[str(index)][2], eval_small_dict[str(index)][1]+eval_small_dict[str(index)][3]):
        #     score = 0
        #     count = 0
        #     for idx, response in enumerate(candidate_eval_answer, 1):
        #         answer = json.loads(response.replace("```json",'').replace("```",''))["questions"]
        #         if len(answer) != eval_small_dict[str(index)][1]+eval_small_dict[str(index)][3]:
        #             continue
        #         score += answer[answer_id]['score_suggestion']
        #         count += 1
        #     correction_eval_answer.append(round(score/count, 2))
    ##
    format_answer = knowledge_graph.evalllm.generate([[HumanMessage(content=multi_get_answer_no_info.replace("{report_contents}","\",\n\"".join(reports)).replace("{question_text}",format_normativeness.page_content))]])
    functional_answer = knowledge_graph.evalllm.generate([[HumanMessage(content=multi_get_answer_no_info.replace("{report_contents}", "\",\n\"".join(reports)).replace("{question_text}",functional_eval.page_content))]])

    format_eval_answer = [generation.text for generation in format_answer.generations[0]]

    def extract_json_blocks(text):
        """
        提取所有 ```json ... ``` 块中的内容（不含三引号本身）
        """
        pattern = r"```json\s*(.*?)\s*```"
        matches = re.findall(pattern, text, flags=re.DOTALL)
        return matches[0]

    for format_answer_id in range(eval_dict['format']):
        scores = []
        count = 0
        for idx, response in enumerate(format_eval_answer, 1):
            try:
                answer = json.loads(response.replace("```json",'').replace("```",''))['questions']
                valid = True
                for single_answer in answer:
                    if len(single_answer['score_suggestion']) != 5:
                        valid = False  # 如果有任何一个答案的分数长度不符合预期，则标记为无效
                        break  # 跳过不符合预期长度的答案
                if not valid:
                    continue
                if len(answer) != eval_dict['format']:
                    continue
                
                if scores == []:
                    scores = answer[format_answer_id]['score_suggestion']
                else:
                    # score += answer[functional_answer_id]['score_suggestion']
                    scores = [a + b for a, b in zip(scores, answer[format_answer_id]['score_suggestion'])]
                count += 1
            except:
                continue
        format_eval_score.append([round(score/count, 2)  for score in scores])
        
    functional_eval_answer = [generation.text for generation in functional_answer.generations[0]]
    for functional_answer_id in range(eval_dict['functional']):
        scores = []
        count = 0
        for idx, response in enumerate(functional_eval_answer, 1):
            try:
                answer = json.loads(response.replace("```json",'').replace("```",''))['questions']
                valid = True
                for single_answer in answer:
                    if len(single_answer['score_suggestion']) != 5:
                        valid = False  # 如果有任何一个答案的分数长度不符合预期，则标记为无效
                        break  # 跳过不符合预期长度的答案
                if not valid:
                    continue
                if len(answer) != eval_dict['functional']:
                    continue
                if scores == []:
                    scores = answer[functional_answer_id]['score_suggestion']
                else:
                    scores = [a + b for a, b in zip(scores, answer[functional_answer_id]['score_suggestion'])]
                count += 1
            except:
                continue
        functional_eval_score.append([round(score/count, 2)  for score in scores])
    eval_paper_result = {
        "Paper id":num,
        "Completeness":complete_eval_answer, 
        "Information Accuracy":correction_eval_answer,
        "Format Normativeness":format_eval_score,
        "Practicality and Functionality":functional_eval_score
    }
    if os.path.exists(eval_paper_save_dir):
        with open(eval_paper_save_dir,"r") as f:
            data = json.load(f)
        data.append(eval_paper_result)
        with open(eval_paper_save_dir, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    else:
        with open(eval_paper_save_dir, "w") as f:
            json.dump([eval_paper_result], f, indent=4, ensure_ascii=False)
        
            

if __name__=="__main__":
    # main(1)
    for i in range(1, 126):
        main(i, save_dir=None)
        # main(i, 
        #      save_dir=f"./papersavings/pure/{i}.md",
        #      eval_paper_save_dir = "./evaluation_paper_pure_results.json",
        #      name="Pure")
        # main(i, 
        #      save_dir=f"./papersavings/papersavings-gen/papersavings-qwen/Paper_{i}.md",
        #      eval_paper_save_dir = "./evaluation_paper_qwen_results.json",
        #      name="qwen")
        # main(i, 
        #      save_dir=f"./papersavings/papersavings-gen/papersavings-ds/Paper_{i}.md",
        #      eval_paper_save_dir = "./evaluation_paper_ds_results.json",
        #      name="ds")
        # main(i, 
        #      save_dir=f"./papersavings/pure_simple/{i}.md",
        #      eval_paper_save_dir = "./evaluation_paper_pure_simple_results.json",
        #      name="Pure")


