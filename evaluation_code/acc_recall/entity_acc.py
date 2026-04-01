
import requests
import sys
from pathlib import Path

# 把项目根目录加入路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from graph_utils.graph_generate_bak import Knowledge_Graph
import os, json, re
from langchain.schema import HumanMessage
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import uuid
import logging
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
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

def split_documents_finer(raw_text, header_split_levels=None, chunk_size=300, chunk_overlap=50):
    """
    两级切分：先按Markdown标题拆分，再对长内容进一步切分
    raw_text: 原始Markdown文本
    header_split_levels: Markdown标题层级（默认切分#、##、###）
    chunk_size: 最终片段最大长度（越小越碎，建议300-500）
    chunk_overlap: 片段重叠长度（确保上下文连贯）
    """
    # 1. 第一级：按Markdown标题切分（保留标题元数据）
    if header_split_levels is None:
        header_split_levels = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),  # 细化到四级标题
        ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=header_split_levels)
    header_docs = markdown_splitter.split_text(raw_text)
    
    # 2. 第二级：对每个标题下的内容进一步切分（控制粒度）
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]  # 优先按段落拆分
    )
    
    fine_docs = []
    for doc in header_docs:
        # 对每个标题下的内容再次切分
        split_docs = recursive_splitter.split_documents([doc])
        # 保留原始元数据（标题层级信息）
        for split_doc in split_docs:
            fine_docs.append(split_doc)
    
    return fine_docs

def structured_retriever(entity: str, knowledge_graph: Knowledge_Graph) -> list:
    # return [knowledge_graph.mini_answer(f"Please organize all the content related to this entity: {entity}")]
    return [x.page_content for x in knowledge_graph.splits]
     
# ===============================
# 1. 初始化向量数据库
# ===============================
def init_vector_stores(raw_paper_docs, protocol_docs):
    embeddings = OpenAIEmbeddings()
    raw_paper_db = Chroma.from_documents(
        documents=raw_paper_docs,
        embedding=embeddings,
        collection_name="raw_paper_collection",
    )
    protocol_db = Chroma.from_documents(
        documents=protocol_docs,
        embedding=embeddings,
        collection_name="protocol_collection",
    )
    return raw_paper_db, protocol_db, embeddings

# ===============================
# 2. 召回候选片段
# ===============================
def retrieve_candidates(entity_name, knowledge_graph, protocol_content, top_k=5):
    query_raw = f"{entity_name}"
    # query_protocol = f"{entity_name}"
    # raw_docs = raw_db.similarity_search(query_raw, k=top_k)
    # protocol_docs = protocol_db.similarity_search(query_protocol, k=top_k)
    # 仅保留包含实体名的片段，降低噪声
    # raw_texts = [d.page_content for d in raw_docs if entity_name.lower() in d.page_content.lower()]
    # proto_texts = [d.page_content for d in protocol_docs if entity_name.lower() in d.page_content.lower()]
    # 若过滤后为空，用原始检索结果兜底
    # if not raw_texts: raw_texts = [d.page_content for d in raw_docs]
    raw_texts = structured_retriever(query_raw, knowledge_graph)
    # if not proto_texts: proto_texts = [d.page_content for d in protocol_docs]
    return raw_texts, [protocol_content]

# ===============================
# 3. LLM一致性检查（结构化判断）
# ===============================
def llm_consistency_check_ref(entity_name, raw_texts, protocol_texts, llm=None):
    if not llm:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(r"""You are an expert reviewer in experimental replication practices.
Use the 【Original Paper】 as the main reference to evaluate whether the 【Protocol】 description of {entity_name} is **reasonably aligned**.

【Original Paper】:
{raw_text}

【Protocol】:
{protocol_text}

### Rules

1. **Invalid (valid = false)**

   * The Protocol contains details about {entity_name} that **clearly contradict** the Original Paper in a way that could reasonably affect the experiment.
   * The Protocol omits **essential aspects** of {entity_name} that the Original Paper indicates are necessary for performing the experiment.

2. **Valid (valid = true)**

   * The Protocol’s description of {entity_name} is **generally consistent** with the Original Paper.
   * Missing non-essential details about {entity_name} does **not** make it invalid as long as the description aligns with the Original Paper.

### Output strict JSON

{{
"entity": "entity_name",
"valid": true/false        // false only if there is a clear contradiction or omission of essential aspects; true otherwise.
}}
""")

    combined_raw = "\n".join(raw_texts)       # 防止超长
    combined_protocol = "\n".join(protocol_texts)

    resp = llm.predict(prompt.format(
        entity_name=entity_name,
        raw_text=combined_raw,
        protocol_text=combined_protocol
    ))

    # 尝试解析为 dict；失败则回传原字符串，避免中断流程
    try:
        data = json.loads(resp.replace("```json", "").replace("```", "").strip())
    except Exception:
        data = {"raw_response": resp, "entity": entity_name}
    return data

# ===============================
# 4. 主流程（整合以上步骤）
# ===============================

def entity_consistency_check_best_practice_v2(
    entity_list, knowledge_graph, protocol_section, top_k=5, max_workers=8
):
    # embeddings = OpenAIEmbeddings()

    # 为本次调用生成唯一的 collection 名称，避免并发冲突
    # uid = uuid.uuid4().hex[:8]
    # proto_name = f"protocol_collection_{uid}"

    # raw_db = Chroma.from_documents(raw_paper_docs, embeddings, collection_name=raw_name)
    # protocol_db = Chroma.from_documents(protocol_docs, embeddings, collection_name=proto_name)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 建议：在主线程先做检索，避免在同一 collection 上并发 query（更稳）
    entity_inputs = []
    for e in entity_list:
        raw_texts, protocol_texts = retrieve_candidates(e, knowledge_graph, protocol_section, top_k=top_k)
        entity_inputs.append((e, raw_texts, protocol_texts))

    def process_entity(inp):
        e, raw_texts, protocol_texts = inp
        return llm_consistency_check_ref(e, raw_texts, protocol_texts, llm)

    try:
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for fut in as_completed(executor.submit(process_entity, x) for x in entity_inputs):
                results.append(fut.result())
        return results
    finally:
        pass
        # try:
        #     protocol_db._client.delete_collection(proto_name)
        # except Exception:
        #     pass



def unified_materials_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # 统一类别的实体模型：仅分三大类
    class UnifiedMaterialsEntities(BaseModel):
        """从文本中提取的材料相关实体，统一分为三大类"""
        
        reagents: List[str] = Field(
            default=[], 
            description="All chemical reagents, including metal precursors, additives, solvents, gases, acid-base regulators, complexing agents and other chemical substances used in experiments"
        )
        
        experimental_equipment: List[str] = Field(
            default=[], 
            description="All specific experimental equipment, including synthesis equipment, characterization equipment, activation equipment, reaction equipment, product analysis equipment and other equipment directly used in the core experimental processes"
        )
        
        common_lab_equipment: List[str] = Field(
            default=[], 
            description="All common laboratory equipment, including drying equipment, calcination equipment, balances, stirrers and other general laboratory tools"
        )

    # 提示词专注于提取三大类实体
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in chemical experiments (Fischer–Tropsch synthesis).
                Extract all relevant entities from the text and classify them into three categories ONLY:
                1. Reagents: All chemical substances used in experiments, including but not limited to:
                   - Metal precursors, additive/promoter precursors, solvents, acids/bases, complexing agents
                   - Surface modifiers, passivation gases, synthesis gases, drying agents, cleaning agents, etc.
                  
                2. Experimental Equipment: Specialized equipment directly involved in core experiment processes:
                   - Synthesis equipment, characterization instruments (ICP, TEM, XRD, etc.)
                   - Activation equipment, reaction equipment, product analysis instruments, etc.
                  
                3. Common Lab Equipment: General laboratory tools for routine operations:
                   - Drying equipment, calcination equipment, balances, magnetic stirrers, pumps, etc.

                Guidelines:
                - Only include entities explicitly mentioned in the text (no assumptions)
                - Each entity should appear in only one most appropriate category
                - Return simple lists of entity names (include key attributes if critical, e.g., "syngas (H₂/CO=2:1)")
                - Do not add explanations, formatting, or extra text - just the entities themselves
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all materials entities from the following text: {question}"
            ),
        ]
    )

    # 创建提取链
    unified_entities_chain = prompt | llm.with_structured_output(UnifiedMaterialsEntities)
    return unified_entities_chain

def synthesis_methods_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Simplified entity model with 3 core categories
    class SynthesisMethodEntities(BaseModel):
        """Extracted entities related to catalyst synthesis methods (simplified 3 categories)"""
        
        synthesis_techniques: List[str] = Field(
            default=[], 
            description="Names of catalyst synthesis methods/techniques (e.g., hydrothermal method, co-precipitation, impregnation)"
        )
        
        chemical_substances: List[str] = Field(
            default=[], 
            description="All chemical reagents with details (concentrations, formulas) (e.g., Fe(NO₃)₃, NH₄OH (0.1M), metal nitrate solution)"
        )
        
        experimental_factors: List[str] = Field(
            default=[], 
            description="Combined equipment with specific conditions (e.g., Teflon-lined autoclave at 180°C for 6 hours, stirred reactor under 2 MPa pressure)"
        )

    # Prompt template for simplified extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in catalyst synthesis methods (Fischer–Tropsch synthesis).
                Extract all relevant entities from the text and classify them into these 3 categories ONLY:
                1. Synthesis techniques: Names of preparation methods/techniques
                2. Chemical substances: All reagents with concentrations/formulas if specified
                3. Experimental factors: Equipment combined with their specific conditions (temperature, pressure, time with units) as single entities

                Guidelines:
                - Only extract entities explicitly mentioned in the text
                - Each entity belongs to only one most appropriate category
                - Preserve exact terms, units, and chemical names as in original text
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all synthesis method entities from the following text: {question}"
            ),
        ]
    )

    # Create extraction chain
    synthesis_entities_chain = prompt | llm.with_structured_output(SynthesisMethodEntities)
    return synthesis_entities_chain

def synthesis_procedures_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Entity model with max 3 categories
    class SynthesisProceduresEntities(BaseModel):
        """Extracted entities from catalyst synthesis procedures"""
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with quantities (e.g., 0.15g Fe(NO₃)₃·9H₂O, 50mL deionized water, 0.1M NH₄OH)"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Specific equipment with their associated experimental parameters (e.g., 500mL three-necked flask with magnetic stirring at 800 rpm, Teflon-lined autoclave heated to 180°C for 6 hours)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in catalyst synthesis procedures (Fischer–Tropsch synthesis).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Chemical reagents: All substances with quantities (solids, liquids, gases)
                2. Equipment with parameters: Specific equipment names (including model/specifications when mentioned) combined with their directly associated experimental parameters (temperature, time, speed, pH, atmosphere, etc.)

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entity belongs to only one most appropriate category
                - Preserve exact values, units, and chemical names as in original text
                - For equipment, use specific names rather than general types (e.g., "Mettler Toledo AL204 Analytical Balance" instead of "balance")
                - Combine equipment with its directly related parameters as a single entity
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify entities from the following synthesis procedures text: {question}"
            ),
        ]
    )

    # Create extraction chain
    procedures_entities_chain = prompt | llm.with_structured_output(SynthesisProceduresEntities)
    return procedures_entities_chain

def characterization_methods_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Entity model with 3 core categories
    class CharacterizationEntities(BaseModel):
        """Extracted entities from catalyst characterization methods"""
        
        characterization_systems: List[str] = Field(
            default=[], 
            description="Complete characterization systems combining technique, instrument, and operational parameters (e.g., XRD using PANalytical X’pert-3 diffractometer with Cu Kα radiation at 40kV over 2θ range 10°-80°; H₂-TPR using micro fixed-bed reactor with TCD detector, 10°C/min ramping rate, and 25 mL/min H₂/Ar flow)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in catalyst characterization methods (Fischer–Tropsch synthesis).
                Extract all relevant entities from the text and combine them into a single category:
                1. Characterization systems: Complete descriptions that combine three elements as a single entity:
                   - The characterization technique/method
                   - The specific instrument/equipment used (including brand/model if specified)
                   - All associated operational parameters with units that belong to this technique and instrument

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must be a complete system combining technique + instrument + its parameters
                - Preserve exact terms, units, technical specifications, and model numbers as in original text
                - Maintain the natural association between parameters and their specific instrument/technique
                - Return simple lists without explanations, formatting, or additional information
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all characterization entities from the following text: {question}"
            ),
        ]
    )

    # Create extraction chain
    characterization_entities_chain = prompt | llm.with_structured_output(CharacterizationEntities)
    return characterization_entities_chain

def catalytic_evaluation_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Entity model with 3 core categories
    class CatalyticEvaluationEntities(BaseModel):
        """Extracted entities from catalyst activation and reaction conditions"""
        
        activation_conditions: List[str] = Field(
            default=[], 
            description="Activation process details including gases and parameters (e.g., 10% H₂/Ar mixture at 400°C for 6 hours, flow rate 50 mL/min; pure Ar purge at 150°C)"
        )
        
        reaction_conditions: List[str] = Field(
            default=[], 
            description="Reaction process details including gases and parameters (e.g., syngas (H₂/CO=2.0) at 250°C and 10 bar, GHSV 5000 mL/(gcat·h); N₂ atmosphere at 300°C, pressure 5 bar)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Fischer-Tropsch catalytic evaluation (activation and reaction conditions).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Activation conditions: Complete activation process descriptions combining gases (with compositions if specified) and their corresponding operational parameters (temperatures, pressures, times, flow rates with units)
                2. Reaction conditions: Complete reaction process descriptions combining gases (with compositions if specified) and their corresponding operational parameters (temperatures, pressures, flow rates, ratios, GHSV with units)

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must combine relevant gas and its associated parameters for the specific process
                - Preserve exact values, units, gas compositions, and process relationships as in original text
                - Focus exclusively on activation and reaction conditions (exclude characterization-related parameters)
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all catalytic evaluation entities from the following text: {question}"
            ),
        ]
    )

    # Create extraction chain
    catalytic_entities_chain = prompt | llm.with_structured_output(CatalyticEvaluationEntities)
    return catalytic_entities_chain

def results_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Entity model with 3 core categories
    class ResultsEntities(BaseModel):
        """Extracted entities from characterization results and catalyst performance data"""
        
        characterization_results: List[str] = Field(
            default=[], 
            description="Associated pairs of characterization indicators + their data/conclusions (e.g., BET surface area 85 m²/g, Fe₅C₂ crystal phase formation, particle size 15 nm, elemental valence of Fe as +3)"
        )
        
        performance_results: List[str] = Field(
            default=[], 
            description="Associated pairs of performance indicators + their data/trends (e.g., CO conversion 70%, CH₄ selectivity 12%, C₃⁺ selectivity increases with temperature, deactivation rate 0.5%/h)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Fischer-Tropsch catalyst results (characterization & performance).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY. Each entry must be a **complete, associated unit** (indicator + corresponding data/conclusion/trend) — do NOT extract isolated indicators or disconnected data.
                
                1. Characterization results: Combine "characterization indicator (property/metric)" + "its specific data/conclusion" (e.g., "BET surface area 85 m²/g" instead of separate "BET surface area" and "85 m²/g"; "Fe₅C₂ crystal phase formation" instead of separate "crystal phase" and "Fe₅C₂").
                
                2. Performance results: Combine "performance indicator (metric)" + "its specific data/trend" (e.g., "CO conversion 70%" instead of separate "CO conversion" and "70%"; "C₃⁺ selectivity increases with reaction time" instead of separate "C₃⁺ selectivity" and "increases with time").

                Guidelines:
                - Extract only explicitly mentioned associated units (no assumptions about unstated relationships)
                - Each entry must be a single logical unit (indicator + its matching data/conclusion)
                - Preserve exact values, units, chemical names (e.g., Fe₅C₂) and technical terms as in the original text
                - Include both quantitative (numerical data) and qualitative (conclusions/trends) associated pairs
                - Return simple lists without explanations, formatting, or isolated parameters
                - Do not output duplicate associated units.
                """,
            ),
            (
                "human",
                "Extract and classify all results entities from the following text: {question}"
            ),
        ]
    )

    # Create extraction chain
    results_entities_chain = prompt | llm.with_structured_output(ResultsEntities)
    return results_entities_chain

def comprehensive_short_text_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Comprehensive entity model with moderate categories
    class ComprehensiveEntities(BaseModel):
        """Extracted entities from short texts related to Fischer-Tropsch catalyst experiments"""
        
        methods_and_techniques: List[str] = Field(
            default=[], 
            description="Catalyst synthesis methods and characterization techniques (e.g., co-precipitation, XRD, hydrothermal method, H₂-TPR)"
        )
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with details (concentrations, compositions) (e.g., Fe(NO₃)₃·9H₂O, 0.1M NH₄OH, syngas (H₂/CO=2:1))"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Laboratory equipment combined with their operational parameters (e.g., Teflon-lined autoclave at 180°C, fixed-bed reactor under 10 bar, XRD diffractometer with 40kV voltage)"
        )
        
        performance_metrics: List[str] = Field(
            default=[], 
            description="Catalyst performance indicators with results (e.g., CO conversion 70%, CH₄ selectivity 15%, α factor 0.85)"
        )

    # Prompt template for comprehensive extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a comprehensive entity extractor for short texts on Fischer-Tropsch catalyst experiments.
                Extract all relevant entities and classify them into these 4 categories ONLY (reduced categories to avoid omission):
                
                1. Methods and techniques: Combine catalyst synthesis methods (e.g., co-precipitation) and characterization techniques (e.g., XRD)
                2. Chemical reagents: All chemical substances with concentrations, compositions, or ratios if specified
                3. Equipment with parameters: Pair lab equipment/apparatus with their directly associated operational parameters (temperature, pressure, voltage with units)
                4. Performance metrics: Catalyst performance indicators, including numerical results when provided (e.g., "CO conversion 70%" instead of separate "CO conversion" and "70%")

                Guidelines:
                - Extract all explicitly mentioned entities (avoid omission by reducing category boundaries)
                - Each entity belongs to the most appropriate single category
                - Preserve exact terms, units, chemical names, and technical details
                - For equipment, combine with its specific parameters (don't list them separately)
                - For performance metrics, include results/data with the indicator when available
                - Return concise lists without explanations or formatting
                - Do not output duplicates.
                """,
            ),
            (
                "human",
                "Extract and classify all entities from the following short text: {question}"
            ),
        ]
    )

    # Create extraction chain
    comprehensive_entities_chain = prompt | llm.with_structured_output(ComprehensiveEntities)
    return comprehensive_entities_chain

# 实体提取器映射配置
ENTITY_EXTRACTORS = {
    "unified_materials": {
        "chain": "reagent_entity_chain",
        "categories": ["reagents", "experimental_equipment", "common_lab_equipment"],
        "description": "材料相关实体提取器"
    },
    "synthesis_methods": {
        "chain": "synthesis_methods_entity_chain",
        "categories": ["synthesis_techniques", "chemical_substances", "experimental_factors"],
        "description": "合成方法实体提取器"
    },
    "synthesis_procedures": {
        "chain": "synthesis_procedures_entity_chain",
        "categories": ["chemical_reagents", "equipment_with_parameters"],
        "description": "合成步骤实体提取器"
    },
    "characterization_methods": {
        "chain": "characterization_methods_entity_chain",
        "categories": ["characterization_systems"],
        "description": "表征方法实体提取器"
    },
    "catalytic_evaluation": {
        "chain": "catalytic_evaluation_entity_chain",
        "categories": ["activation_conditions", "reaction_conditions"],
        "description": "催化评价实体提取器"
    },
    "results": {
        "chain": "results_entity_chain",
        "categories": ["characterization_results", "performance_results"],
        "description": "结果分析实体提取器"
    },
    "comprehensive_short_text": {
        "chain": "comprehensive_short_text_entity_chain",
        "categories": ["methods_and_techniques", "chemical_reagents", "equipment_with_parameters", "performance_metrics"],
        "description": "综合短文本实体提取器"
    }
}

def extract_and_print_entities(extractor_name, text, extractors_config, global_vars):
    """
    通用实体提取和打印函数
    
    参数:
        extractor_name: 提取器名称，对应ENTITY_EXTRACTORS中的键
        text: 要提取实体的文本
        extractors_config: 提取器配置字典(ENTITY_EXTRACTORS)
        global_vars: 全局变量字典，包含各种实体提取链
    """
    # 检查提取器是否存在
    if extractor_name not in extractors_config:
        print(f"错误: 提取器 '{extractor_name}' 不存在")
        return
    
    # 获取提取器配置
    config = extractors_config[extractor_name]
    print(f"===== {config['description']} =====")
    
    # 获取提取链
    try:
        extraction_chain = global_vars[config['chain']]
    except KeyError:
        print(f"错误: 无法找到提取链 '{config['chain']}'")
        return
    
    # 执行实体提取
    entities = extraction_chain.invoke({"question": text})
    
    # 打印每个类别的实体和长度
    for category in config['categories']:
        if hasattr(entities, category):
            entity_list = getattr(entities, category)
            print(f"\n{category}:")
            print(f"  数量: {len(entity_list)}")
            print(f"  实体: {entity_list}")
        else:
            print(f"\n警告: 实体类别 '{category}' 不存在于提取结果中")
    
    return entities

def is_json_file_empty(file_path):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return True  # 或根据需求返回False
    
    # 检查文件大小是否为0（无任何内容）
    if os.path.getsize(file_path) == 0:
        return True
    
    # 检查文件内容是否全为空白字符（空格、换行等）
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()  # 去除首尾空白
        return len(content) == 0

from langchain_openai import ChatOpenAI
from graph_utils.chatgpt.config.config import (
    OPENAI_CONFIG,
)
config = OPENAI_CONFIG
api_key = config['api_key']
base_url = config['base_url']
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_API_BASE"] = base_url
reagent_entity_chain = unified_materials_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
synthesis_methods_entity_chain = synthesis_methods_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
synthesis_procedures_entity_chain = synthesis_procedures_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
characterization_methods_entity_chain = characterization_methods_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
catalytic_evaluation_entity_chain = catalytic_evaluation_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
results_entity_chain = results_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))
comprehensive_short_text_entity_chain = comprehensive_short_text_entities_extractor(llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini"))

def process_split(index, small_split, is_last, reports, knowledge_graph, ENTITY_EXTRACTORS, num):
    def process_section(section_name, content):
        section_entities = []
        total, true = 0, 0

        sec = extract_and_print_entities(section_name, content, ENTITY_EXTRACTORS, globals())
        for idx in range(len(ENTITY_EXTRACTORS[section_name]['categories'])):
            section_entities += getattr(sec, ENTITY_EXTRACTORS[section_name]['categories'][idx])

        check_results = entity_consistency_check_best_practice_v2(
            entity_list=section_entities,
            knowledge_graph=knowledge_graph,
            protocol_section=content
        )

        for res in check_results:
            # 初始化res_dict为None，用于判断是否解析成功
            res_dict = None
            try:
                # 先检查res是否已经是字典格式
                if isinstance(res, dict):
                    # 如果res是字典，先尝试直接使用
                    res_dict = res
                    # 如果存在raw_response键，仍然使用其中的内容
                    if 'raw_response' in res_dict:
                        raw_res = res_dict['raw_response']
                        cleaned_res = raw_res.replace("```json", "").replace("```", "").strip()
                        res_dict = json.loads(cleaned_res)
                else:
                    # 否则按原始逻辑提取并解析
                    raw_res = res['raw_response']
                    cleaned_res = raw_res.replace("```json", "").replace("```", "").strip()
                    res_dict = json.loads(cleaned_res)
            except json.JSONDecodeError:
                print(f"JSON解析错误: 无法解析内容 - {cleaned_res if 'cleaned_res' in locals() else res}")
            except KeyError as e:
                print(f"键错误: 缺少'{e}'字段 in {res}")
            except Exception as e:
                print(f"处理响应时出错: {str(e)}")

            # 只有解析成功的情况下才进行判断
            if isinstance(res_dict, dict):
                # print(res_dict)
                if res_dict.get("valid"):
                    true += 1
                else:
                    # print(f"冲突信息: {res_dict.get('conflicts', '无冲突信息')}")
                    pass
                total += 1
            else:
                print(f"跳过无效响应: {res}")
                # 根据需求决定是否将无效响应计入total
                # total += 1  # 如果需要统计无效响应，取消注释这行

        return section_entities, total, true

    if not is_last:
        sections = [
            ("unified_materials", small_split[0].page_content),
            ("synthesis_methods", small_split[1].page_content),
            ("synthesis_procedures", small_split[2].page_content),
            ("characterization_methods", small_split[3].page_content),
            ("catalytic_evaluation", small_split[4].page_content),
            ("results", small_split[5].page_content)
        ]
    else:
        sections = [("comprehensive_short_text", reports[-1])]

    method_entities = []
    total_entities, true_entities = 0, 0

    # 并行执行
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_section, name, content): name for name, content in sections}
        for future in as_completed(futures):
            section_entities, total, true = future.result()
            method_entities.append(section_entities)
            total_entities += total
            true_entities += true

    return {
        'paper_id': num,  
        'method_index': index,
        'total_entities': total_entities,
        'true_entities': true_entities,
        'acc_rate': round(true_entities / total_entities, 4) if total_entities else 0
    }, method_entities

def main(num):
    md_text = ""
    base_path = "/mnt/d/Phd/practice/mof_pack/origin_paper/more_paper/"
    paths = []
    for i in range(125):
        paths.append([base_path+str(i+1)+".pdf",base_path+str(i+1)+"-si.pdf"])
    # for path_set in paths:
    # print(paths)
    # num = 1
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
    # doc_splits = split_documents_finer(md_text)
    if knowledge_graph.title == "None":
        knowledge_graph.title = "Paper "+str(num)
    # else:
    #     return 

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

    # entity_chain = knowledge_graph.entity_chain_generate(llm = knowledge_graph.graphllm)

    # # reagent_entity_chain = unified_materials_entities_extractor(llm = knowledge_graph.graphllm)
    reports = []
    reports_splits = []
    save_dirs = ["./papersavings/Paper_"+str(num)+".md",
                "./papersavings/pure/"+str(num)+".md",
                "./papersavings/pure_simple/"+str(num)+".md",
                "./papersavings/papersavings-gen/papersavings-qwen/Paper_"+str(num)+".md",
                "./papersavings/papersavings-gen/papersavings-ds/Paper_"+str(num)+".md",
                "/mnt/d/Phd/practice/mof_pack/papersavings/mmapis/"+str(num)+"-merge/blog.md"
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

    entities_in_articles = []
    article_results = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for idx, split in enumerate(reports_splits):
            futures.append(executor.submit(
                process_split,
                idx,
                split,
                split == reports_splits[-1],
                reports,
                knowledge_graph,
                ENTITY_EXTRACTORS,
                num
            ))

        for future in as_completed(futures):
            result, method_entities = future.result()
            article_results.append(result)
            entities_in_articles.append(method_entities)
            
    all_paper_result = []
    all_paper_entities = []
    if not is_json_file_empty("entities_acc_4o_mini_test.json"):
        with open("entities_acc_4o_mini.json", "r", encoding="utf-8") as f:
            result_list = json.load(f)
            all_paper_result=result_list
    if not is_json_file_empty("entities_acc_4o_mini_test_entities.json"):
        with open("entities_acc_4o_mini_test_entities.json", "r", encoding="utf-8") as f:
            result_list_entities = json.load(f)
            all_paper_entities=result_list_entities
            
    # 将两个列表组合成元组列表，每个元组包含(article_result, entity)
    combined = list(zip(article_results, entities_in_articles))

    # 按照article_result中的method_index排序
    combined_sorted = sorted(combined, key=lambda x: x[0]['method_index'])

    # 拆分回两个列表
    article_results_sorted, entities_in_articles_sorted = zip(*combined_sorted)

    # 如果需要列表类型而不是元组，可以转换
    article_results_sorted = list(article_results_sorted)
    entities_in_articles_sorted = list(entities_in_articles_sorted)        
    
    # **写入最终结果**
    with open("entities_acc_4o_mini_test.json", "w", encoding="utf-8") as f:
        # article_results = sorted(article_results, key=lambda x: x['method_index'])
        # all_paper_result.append(article_results)
        all_paper_result.append(article_results_sorted)
        json.dump(all_paper_result, f, ensure_ascii=False, indent=4)
    with open("entities_acc_4o_mini_test_entities.json", "w", encoding="utf-8") as f:
        all_paper_entities.append(entities_in_articles_sorted)
        json.dump(all_paper_entities, f, ensure_ascii=False, indent=4)

def check_paper_id_exists(data: list[list[dict]], paper_id: int) -> bool:
    """检查指定的paper_id是否存在于嵌套列表结构的JSON数据中"""
    # 遍历外层列表
    for paper_data in data:
        # 遍历内层列表中的每个字典
        for item in paper_data:
            if item.get("paper_id") == paper_id:
                return True
    return False

if __name__=="__main__":
    main(1)
    # for id in range(1, 126):
    #     if not is_json_file_empty("entities_acc_4o_mini_test.json"):
    #         with open("entities_acc_4o_mini_test.json", "r", encoding="utf-8") as f:
    #             result_list = json.load(f)
    #             if check_paper_id_exists(result_list, id):
    #                 print(f"{id}文章评估完成，skipping....")
    #                 continue
    #     print(f"开始评估{id}....")
    #     main(id)
    #     # break
