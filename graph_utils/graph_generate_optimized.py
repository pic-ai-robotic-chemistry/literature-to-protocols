"""
知识图谱生成模块 - 优化重构版本
====================================

本模块对原有的 graph_generate_bak.py 进行了全面的重构和优化：

1. **解耦设计**: 将原有的单一大类拆分为多个专门的管理器类
2. **提升可读性**: 清晰的类结构和方法命名，详细的文档字符串
3. **错误处理**: 改进的异常处理和日志记录
4. **类型注解**: 完整的类型提示，提高代码质量
5. **向后兼容**: 保留原有的 Knowledge_Graph 类接口，确保现有代码可以正常运行

主要组件:
---------
- ConfigurationManager: 配置管理器，集中管理所有配置参数
- DocumentProcessor: 文档处理器，负责文档的分割、过滤和预处理
- GraphTransformerManager: 图谱转换管理器，负责LLM图谱转换器的创建和管理
- QueryManager: 查询管理器，负责图谱查询和检索功能
- ChainManager: 链管理器，负责各种推理链的创建和管理
- Knowledge_Graph: 主类（保持向后兼容），整合所有管理器功能

作者: 李晓晖
版本: 2.0 (优化重构版)
日期: 2025年10月
"""

from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Tuple, List, Optional, Dict, Any, Union
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Neo4j Graph导入 - 处理弃用警告
try:
    from langchain_neo4j import Neo4jGraph
except ImportError:
    # 如果新包不可用，回退到旧包但忽略警告
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from langchain_community.graphs import Neo4jGraph

from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.runnables import ConfigurableField, RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from .load_files import *
from .load_files import split_md_filtered
from langchain.schema import Document
from .chatgpt.config.config import (
    QWEN_CONFIG,
    OPENAI_CONFIG,
    DEEPSEEK_CONFIG,
    APPLICATION_PROMPTS,
)
import os
import time
import re
import logging
from langchain_community.graphs import Neo4jGraph
from tqdm import tqdm
import concurrent.futures
from string import ascii_letters, digits, whitespace, punctuation


class ConfigurationManager:
    """配置管理器 - 集中管理所有配置参数和环境设置"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 深度求索配置
        config = DEEPSEEK_CONFIG
        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.model_name = config["model_config"]["model"]
        
        # Neo4j配置
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
        os.environ["NEO4J_USERNAME"] = "neo4j"
        os.environ["NEO4J_PASSWORD"] = "test@123!"
        
        # 关键词过滤列表
        self.keywords = [
            "reference", "author", "supplementary reference", "supplementary data",
            "data availability", "acknowledgement", "funding", "conflict of interest",
            "competing interest", "author contributions", "references", "acknowledg",
            "declaration", "additional information", "online connect"
        ]
        
        # 应用提示词
        self.prompts = APPLICATION_PROMPTS
    
    def get_llm_models(self) -> Dict[str, ChatDeepSeek]:
        """获取LLM模型实例"""
        return {
            'graph': ChatDeepSeek(model="deepseek-chat", api_key=self.api_key, base_url=self.base_url, temperature=0),
            'reason': ChatDeepSeek(model="deepseek-reasoner", api_key=self.api_key, base_url=self.base_url),
            'mini': ChatDeepSeek(model="deepseek-chat", api_key=self.api_key, base_url=self.base_url, temperature=0)
        }


class DocumentProcessor:
    """文档处理器 - 负责文档的分割、过滤和预处理"""
    
    def __init__(self, config_manager: ConfigurationManager):
        """
        初始化文档处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.llm_models = config_manager.get_llm_models()
    
    def sanitize_query(self, query: str) -> str:
        """清理查询字符串，只保留ASCII字母、数字、空格和常用标点"""
        allowed_chars = set(ascii_letters + digits + whitespace + punctuation)
        # 额外允许Lucene查询语法所需的特殊字符
        lucene_special_chars = {'+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\'}
        allowed_chars.update(lucene_special_chars)
        
        # 过滤掉不允许的字符
        sanitized = ''.join(c for c in query if c in allowed_chars)
        
        # 处理Lucene特殊字符的转义
        for char in lucene_special_chars:
            if char in sanitized and char not in {'+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':'}:
                sanitized = sanitized.replace(char, '\\' + char)
        sanitized = re.sub(r'(?<![\\])/', r'\\/', sanitized)
        return sanitized
    
    def split_no_filtered_docs(self, path: List[str]) -> List[Document]:
        """分割未过滤的文档"""
        splits = []
        for p in path:
            splits += load_md_no_filtered_batch(p)
        
        # 过滤包含关键词的文档
        for i in range(len(splits), 0, -1):
            for key, value in splits[i-1].metadata.items():
                if any(k in value.lower() for k in self.config.keywords):
                    del splits[i-1]
                    break
        
        return splits
    
    def split_no_filtered_md(self, markdown: str) -> List[Document]:
        """分割未过滤的Markdown文档"""
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
        )
        splits = markdown_splitter.split_text(markdown)
        
        # 过滤包含关键词的文档
        for i in range(len(splits), 0, -1):
            for key, value in splits[i-1].metadata.items():
                if any(k in value.lower() for k in self.config.keywords):
                    del splits[i-1]
                    break
        
        # 移除长度过短的分割
        for index in range(len(splits) - 1, -1, -1):
            if len(splits[index].page_content) < 30:
                del splits[index]
        
        return splits
    
    def split_template(self, type_name: str) -> List[Document]:
        """分割模板文档"""
        splits = []
        if type_name == "MOFTemplate":
            for p in ["./template/MOF Framework Experiment Template/MOF Framework Experiment Template.md"]:
                splits += load_md_no_filtered_batch(p)
        elif type_name == "FTTemplate":
            for p in ["./template/FT/ft.md"]:
                splits += load_md_no_filtered_batch(p)
        
        # 过滤包含关键词的文档
        for i in range(len(splits), 0, -1):
            for key, value in splits[i-1].metadata.items():
                if any(k in value.lower() for k in self.config.keywords):
                    del splits[i-1]
                    break
        
        return splits
    
    def filter_template(self, content: Document, max_retries: int = 5, retry_interval: int = 1) -> str:
        """
        带报错重试机制的内容过滤函数
        
        Args:
            content: 待过滤的内容对象
            max_retries: 最大重试次数（默认5次）
            retry_interval: 重试间隔（秒，默认1秒）
        
        Returns:
            str: 过滤后的文本内容
        """
        message = [
            {"role": "system", "content": self.config.prompts["decompose_prompts"]["system_prompt"]},
            {"role": "user", "content": self.config.prompts["decompose_prompts"]["content_filter"].replace('{content}', content.page_content, 1)}
        ]
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                text = self.llm_models['reason'].invoke(message).content
                time.sleep(1)  # API调用间隔
                return text
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    print(f"第{attempt+1}次调用失败，{retry_interval}秒后重试... 错误信息: {str(e)}")
                    time.sleep(retry_interval)
                else:
                    print(f"已达到最大重试次数{max_retries}次，调用最终失败")
                    raise last_exception
        
        return ""
    
    def add_separator_before_tables(self, text: str) -> str:
        """在每个表格之前正确插入带####的标题分隔符"""
        lines = text.split('\n')
        modified_lines = []
        in_table = False
        current_table_start = None

        for i, line in enumerate(lines):
            stripped_line = line.lstrip()
            if stripped_line.startswith('|'):
                if not in_table:
                    current_table_start = len(modified_lines)
                    in_table = True
                modified_lines.append(line)
            else:
                if in_table:
                    in_table = False
                    title_lines = []
                    for j in range(i, len(lines)):
                        title_candidate = lines[j].strip()
                        if title_candidate.startswith('**') and 'Table' in title_candidate:
                            title_lines.append(f"#### {title_candidate}")
                        else:
                            break
                    if title_lines and current_table_start is not None:
                        modified_lines = (
                            modified_lines[:current_table_start] + 
                            title_lines + 
                            modified_lines[current_table_start:]
                        )
                        current_table_start = None
                modified_lines.append(line)
        
        if lines and lines[0].lstrip().startswith('|'):
            title_lines = []
            for j in range(len(lines)):
                if lines[j].strip().startswith('**') and 'Table' in lines[j].strip():
                    title_lines.append(f"#### {lines[j].strip()}")
                elif lines[j].lstrip().startswith('|') and j > 0:
                    break
            if title_lines and not any(l.startswith('####') for l in modified_lines[:len(title_lines)]):
                modified_lines = title_lines + modified_lines

        return '\n'.join(modified_lines)
    
    def split_long_docs_by_markdown(self, docs: List[Document]) -> Tuple[List[Document], List[int]]:
        """组合Markdown标题分割和字符数分割的文档处理流程"""
        new_docs = []
        table_indices = []
        text_splitter_markdown = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ])
        text_splitter_char = RecursiveCharacterTextSplitter(
            chunk_size=4096,
            chunk_overlap=512,
            separators=["\n\n", "\n", " ", ""]
        )

        for doc in docs:
            if len(doc.page_content) > 4096:
                # 1. 预处理：添加表格标题分隔符
                modified_content = self.add_separator_before_tables(doc.page_content)
                # 2. Markdown标题层级分割
                markdown_docs = text_splitter_markdown.split_text(modified_content)
                # 3. 对每个Markdown块进行字符数分割
                for markdown_doc in markdown_docs:
                    markdown_text = markdown_doc.page_content
                    char_splits = text_splitter_char.split_text(markdown_text)
                    for split_text in char_splits:
                        new_doc = Document(
                            page_content=split_text,
                            metadata={**doc.metadata, **markdown_doc.metadata}
                        )
                        new_docs.append(new_doc)
                        if "Table" in markdown_doc.metadata.get("Header 4", ""):
                            table_indices.append(len(new_docs) - 1)
            else:
                new_docs.append(doc)
        
        return new_docs, table_indices
    
    def split_by_custom_separator(self, docs: List[Document], separator: str = "\n\n") -> List[Document]:
        """按照指定的分隔符分割Document对象中的文本内容"""
        new_docs = []
        for doc in docs:
            split_texts = doc.page_content.split(separator)
            split_texts = [t for t in split_texts if t.strip()]  # 去除空字符串
            for text in split_texts:
                new_docs.append(Document(page_content=text, metadata=doc.metadata.copy()))
        return new_docs


class GraphTransformerManager:
    """图谱转换管理器 - 负责LLM图谱转换器的创建和管理"""
    
    def __init__(self, config_manager: ConfigurationManager, type_name: str):
        """
        初始化图谱转换管理器
        
        Args:
            config_manager: 配置管理器实例
            type_name: 类型名称
        """
        self.config = config_manager
        self.type_name = type_name
        self.llm_models = config_manager.get_llm_models()
        self.allowed_nodes, self.allowed_rels = self._setup_node_relationships()
        self.llm_transformer = self._create_transformer()
    
    def _setup_node_relationships(self) -> Tuple[List[str], List[str]]:
        """设置允许的节点和关系类型"""
        # 基础节点和关系
        allowed_nodes = [
            "description",
            "Equipment:Synthesis Equipment", "Equipment:Characterization Equipment", 
            "Equipment:Purification and Drying Equipment", "Equipment:Other",
            "Reagents:Solvents", "Reagents:Base or Acid Regulators", "Reagents:Gases", "Reagents:Other",
            "Characterization Methods:Thermogravimetric analysis(TGA)", "Characterization Methods:X-ray diffraction(XRD)",
            "Characterization Method:temperature-programmed desorption of ammonia (NH3-TPD)",
            "Characterization Method:Fourier-transform infrared spectroscopy (FTIR)",
            "Characterization Method:Scanning electron microscopy (SEM)",
            "Characterization Method:Transmission electron microscopy (TEM)",
            "Characterization Method:BET surface area analysis",
            "Characterization Method:Ultraviolet-visible spectroscopy (UV-Vis)",
            "reaction:temperature", "reaction:time", "reaction:solvent", "reaction:pressure",
            "reaction:atmosphere", "reaction:stirring rate", "reaction:other",
            "Purification:filtration", "Purification:Centrifugation", "Purification:Washing",
            "Purification:Column chromatography", "Purification:Recrystallization",
            "Purification:Distillation", "Purification:Extraction", "Purification:other",
            "Drying:temperature", "Drying:time", "Drying:atmosphere", "Drying:other",
            "Documents"
        ]
        
        allowed_rels = [
            "description", "mention",
            "is_used_by", "uses_material_from", "consumes", "produces", 
            "is_synthesized_from", "is_synthesized_of",
            "is_mixed_with", "is_dissolved_in", "is_filtered_from", "is_purification_of",
            "contains_chemical", "is_contained_in", "is_heated_in", "is_cooled_in", "is_stirred_in",
            "is_followed_by", "precedes", "is_part_of",
            "is_analyzed_by", "is_characterized_by", "is_characterization_of",
            "has_temperature", "has_pressure", "has_duration", "has_concentration",
            "has_property", "is_a", "has_value"
        ]
        
        # 根据类型添加特定的节点和关系
        if self.type_name == "FT Framework":
            allowed_nodes.extend([
                "Reagents:Promoter Precursors", "Reagents:Additive Precursors",
                "Reagents:Support Materials", "Reagents:Surface Modifiers", "Reagents:Reducing Agents",
                "Equipment:Fixed-bed Reactors", "Equipment:Slurry Reactors",
                "Equipment:Fluidized-bed Reactors", "Equipment:CO2 Analyzer",
                "reaction:H2_CO_ratio", "reaction:space_time_velocity",
                "reaction:gas hourly space velocity (GHSV)",
                "Activation:reduction_temperature", "Activation:reduction_gas", "Activation:reduction_time",
                "Results:alpha_value", "Results:C5+ selectivity", "Results:CO2_selectivity",
                "Results:olefin_to_paraffin_ratio",
                "Deactivation:carbon_deposition", "Deactivation:poisoning_elements",
                "Deactivation:deactivation_rate",
                "Characterization Methods:Operando Spectroscopy", "Characterization Methods:In-situ XRD",
                "Characterization Methods:Temperature-programmed reduction (TPR)",
                "Characterization Method:Gas chromatography (GC)",
                "Process:feedstock_composition", "Process:product_distribution",
                "Process:water_gas_shift_activity",
            ])
            
            allowed_rels.extend([
                "is_reduced_by", "is_promoted_by", "supports_catalyst", "is_loaded_with",
                "operates_under", "requires_H2_CO_ratio", "has_space_time_velocity",
                "exhibits_selectivity_for", "produces_product_distribution", "has_alpha_value",
                "undergoes_deactivation_due_to", "shows_carbon_deposition",
                "is_followed_by_separation", "requires_pretreatment", "is_optimized_for",
                "is_monitored_by", "undergoes_in_situ_characterization",
                "reacts_with", "is_catalyzed_by", "catalyzes",
            ])
        elif self.type_name == "MoF Framework":
            allowed_nodes.extend([
                "MOF Structure", "Pore Size", "Surface Area", "Adsorption Capacity",
                "Catalytic Activity", "Stability", "Functional Groups", "Synthesis Method",
                "Application", "Reagents:Organic Ligands", "Reagents:Metal Salts",
                "Characterization Method:Nuclear magnetic resonance (NMR)",
            ])
            
            allowed_rels.extend([
                "is_coordination_of", "has_metal_node", "has_organic_ligand", "is_assembled_from",
                "is_solvent热_synthetized", "has_pore_structure", "has_surface_area", "has_pore_size",
                "exhibits_adsorption_of", "is_used_for_catalysis", "is_used_for_separation",
                "is_used_for_storage", "is_functionalized_with", "is_sonicated_in",
                "is_analyzed_by_XRD", "is_analyzed_by_N2_adsorption", "is_analyzed_by_SEM",
                "is_precipitated_from", "is_distilled_from", "is_extracted_from", "is_purified_by",
            ])
        
        return allowed_nodes, allowed_rels
    
    def _create_transformer(self) -> LLMGraphTransformer:
        """创建LLM图谱转换器"""
        if self.type_name == "FT Framework":
            prompt = ChatPromptTemplate.from_messages([(
                "system",
                f"""# Knowledge Graph Instructions for GPT-4 (Fischer-Tropsch Synthesis Edition)

## 1. Overview  
You are designed to extract structured information for building a knowledge graph focused on Fischer-Tropsch synthesis experiments.  
- **Nodes**: Represent entities/concepts (e.g., catalysts, reaction conditions, products).  
- **Goal**: Keep the graph simple, focusing on catalyst development, reaction conditions, and product analysis.  

## 2. Node Labeling  
- **Consistency**: Use general labels (e.g., "catalyst" instead of "cobalt catalyst").  
- **Node IDs**: Use text-based identifiers (e.g., names from the text).  
{'- **Allowed node labels:**' + ", ".join(self.allowed_nodes) if self.allowed_nodes else ""}
{'- **Allowed relationship types:**' + ", ".join(self.allowed_rels) if self.allowed_rels else ""}

## 3. Numerical Data and Dates  
- Include numerical values (e.g., temperature, pressure) as node attributes.  
- **Format**: Key-value pairs (e.g., `activationTemperature: 350`).  
- **Naming**: Use camel case (e.g., `activationTemperature`).  

## 4. Coreference Resolution  
- Maintain consistency for entities mentioned multiple times (e.g., use "Temperature-Programmed Reduction" consistently).  

## 5. Relationship Direction  
- Use active voice for clarity.  
- Ensure direction reflects interactions (e.g., "Tubular Furnace - REDUCES -> Catalyst").  

## 6. Strict Compliance  
Adhere strictly to rules; non-compliance will result in termination.  

## 7. Chemistry-Specific Rules  
- **Catalyst components**: Reflect hierarchy (active phase, promoter, support).  
- **Synthesis relationships**: Use labels like "is_synthesized_from" or "is_supported_on".  
- **Reaction conditions**: Connect equipment to parameters (e.g., "operates_under_Temperature").  
- **Performance metrics**: Use relationships like "exhibits_selectivity_for".  

## 8. Example  
- **Text**: A cobalt-based catalyst on silica was prepared via impregnation. The precursor was reduced in a tubular furnace at 350°C under hydrogen for 2 hours. The catalyst showed 65% C5+ selectivity and an alpha value of 0.85.  

- **Nodes**:  
  - "Cobalt-Based Catalyst" (type: catalyst, supportMaterial: "silica", preparationMethod: "impregnation")  
  - "Reduction Condition" (type: reaction condition, temperature: 350, gas: "hydrogen", duration: "2h")  
  - "C5+ Hydrocarbons" (type: product, carbonRange: "C5+")  

- **Relationships**:  
  - "Reduction Condition" - PRODUCES -> "Cobalt-Based Catalyst"  
  - "Cobalt-Based Catalyst" - EXHIBITS_SELECTIVITY_FOR -> "C5+ Hydrocarbons"  

This example demonstrates correct node and relationship extraction for catalyst preparation, activation, and performance evaluation.
                """),
                ("human", "Use the given format to extract information from the following input: {input}"),
                ("human", "Tip: Make sure to answer in the correct format"),
            ])
        elif self.type_name == "MoF Framework":
            prompt = ChatPromptTemplate.from_messages([(
                "system",
                f"""# Knowledge Graph Instructions for GPT-4
## 1. Overview
You are a top algorithm designed to extract information in a structured format to build a knowledge graph.
- **Nodes** represent entities and concepts. They are similar to nodes in Wikipedia.
- The goal is to make the knowledge graph simple and clear, easy for a broad audience to access.

## 2. Node Labeling
- **Consistency**: Ensure that basic or primary types are used as node labels.
  - For example, when you identify an entity representing a reagent, always label it as **"reagents"**. Avoid using more specific terms like "organic ligands" or "solvents".
- **Node id**: Do not use integers as node ids. Node ids should be names found in the text or human-readable identifiers.
{'- **Allowed node labels:**' + ", ".join(self.allowed_nodes) if self.allowed_nodes else ""}
{'- **Allowed relationship types:**' + ", ".join(self.allowed_rels) if self.allowed_rels else ""}

## 3. Handling Numerical Data and Dates
- Numerical data (such as age or other relevant information) should be included as attributes or characteristics of the corresponding node.
- **Do not create separate nodes for dates/numbers**: Do not create separate nodes for dates or numbers. Always attach them as attributes or characteristics of the node.
- **Attribute format**: Attributes must exist in key-value pair form.
- **Quotes**: Never use escaped single quotes or double quotes in attribute values.
- **Naming convention**: Use camel case as attribute keys, e.g., `synthesisEquipment`.

## 4. Coreference Resolution
- **Maintain entity consistency**: Ensuring consistency when extracting entities is crucial.
If an entity (such as "X-ray diffraction") is mentioned multiple times in the text but referred to by different names or pronouns (e.g., "XRD", "X-ray diffraction"),
always use the most complete identifier of that entity throughout the knowledge graph. In this example, use "X-ray Diffraction" as the entity id.
Remember, the knowledge graph should be coherent and easy to understand, so maintaining consistency in entity references is crucial.

## 5. Relationship Direction and Voice
- **Active voice preference**: When extracting relationships, prioritize active voice constructions to ensure clarity and correct directionality.
- **Relationship direction**: Ensure that the direction of relationships accurately reflects the interaction between entities. The subject of the relationship should be the entity performing the action, and the object should be the entity receiving the action.
- **Example**: If the text states "The mixture was heated in an oven," the relationship should be "Oven - HEATS -> Mixture," not "Mixture - IS_HEATED_IN -> Oven."

## 6. Strict Compliance
Strictly adhere to the rules. Non-compliance will result in termination.

## 7. Chemistry-Specific Considerations
- **Chemical entities**: When dealing with chemical compounds, reagents, or experimental equipment, ensure that node labels and relationships accurately reflect their roles in the experiment.
- **Synthesis relationships**: For synthesis processes, clearly define relationships such as "is_synthesized_from" or "is_used_in_synthesis_of" to distinguish between reactants and products.
- **Analysis relationships**: For analytical techniques, use relationships like "is_analyzed_by" followed by the specific technique (e.g., "is_analyzed_by_XRD") to connect samples to their characterization methods.

## 8. Example
- **Text**: "The copper sulfate solution was prepared by dissolving copper sulfate pentahydrate in deionized water."
- **Nodes**:
  - "Copper Sulfate Solution" (type: solution)
  - "Copper Sulfate Pentahydrate" (type: reagent)
  - "Deionized Water" (type: reagent)
- **Relationships**:
  - "Copper Sulfate Pentahydrate" - DISSOLVES_IN -> "Copper Sulfate Solution"
  - "Deionized Water" - USED_IN_PREPARATION_OF -> "Copper Sulfate Solution"

This example illustrates how to correctly identify nodes and relationships in a chemical context, ensuring that the knowledge graph accurately represents the experimental process.
                """),
                ("human", "Use the given format to extract information from the following input: {input}"),
                ("human", "Tip: Make sure to answer in the correct format"),
            ])
        else:
            prompt = None
        
        return LLMGraphTransformer(
            llm=self.llm_models['graph'],
            node_properties=["description"],
            relationship_properties=["description"],
            prompt=prompt
        )


class QueryManager:
    """查询管理器 - 负责图谱查询和检索功能"""
    
    def __init__(self, config_manager: ConfigurationManager, graph: Neo4jGraph):
        """
        初始化查询管理器
        
        Args:
            config_manager: 配置管理器实例
            graph: Neo4j图谱实例
        """
        self.config = config_manager
        self.graph = graph
        self.llm_models = config_manager.get_llm_models()
    
    def generate_full_text_query(self, input_str: str) -> str:
        """生成全文搜索查询"""
        full_text_query = "(?i).*"
        words = [el for el in remove_lucene_chars(input_str).split() if el]
        for word in words[:-1]:
            full_text_query += f"{(word.lower())}.*"
        full_text_query += f"{words[-1].lower()}.*"
        return full_text_query.strip()
    
    def entity_chain_generate(self, llm) -> Any:
        """生成实体链"""
        class Entities(BaseModel):
            """识别实体信息"""
            names: List[str] = Field(
                ...,
                description="All chemical substances mentioned in the text, along with their relationships, including catalysis, solvents, atmosphere protection, etc."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are extracting chemical reagents, equipments, reaction, charactorization entities from the text."),
            ("human", "Use the given format to extract information from the following input: {question}"),
        ])

        return prompt | llm.with_structured_output(Entities)
    
    def node_chain_generate(self, llm, allowed_nodes: List[str]) -> Any:
        """生成节点链"""
        class Node_chain(BaseModel):
            """识别节点信息"""
            names: List[str] = Field(
                ...,
                description="Please filter out the key nodes (nodes) that might be mentioned in the text from the provided list of allowed nodes. Only list the nodes that are actually mentioned in the text, and disregard those that are not mentioned. "
                "{allowed_nodes}".format(allowed_nodes=allowed_nodes),
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are extracting chemical reagents, equipments, reaction, charactorization entities from the text."),
            ("human", "Use the given format to extract information from the following input: {question}"),
        ])

        return prompt | llm.with_structured_output(Node_chain)
    
    def structured_retriever(self, question: str, llm, title: str, paper_type: str, allowed_nodes: List[str]) -> str:
        """结构化检索器"""
        query_node = """MATCH (initialNode)<-[:MENTIONS]-(segment)
        WHERE ANY(label IN LABELS(initialNode) WHERE label =~ $query) AND segment.title = $title AND segment.paper_type = $paper_type
        CALL (initialNode, segment){
            WITH initialNode, segment
            MATCH (segment)-[:MENTIONS]->(otherNode)
            WHERE otherNode <> initialNode
            MATCH (a)-[r]->(b) WHERE (a = otherNode AND b = initialNode) OR (a = initialNode AND b = otherNode)
            WITH otherNode, initialNode, r
            ORDER BY otherNode.id, initialNode.id
            WITH otherNode, initialNode, COLLECT(DISTINCT type(r)) AS relTypes
            RETURN CASE
                WHEN otherNode.id < initialNode.id THEN otherNode.id + "-" + relTypes[0] + "->" + initialNode.id
                ELSE initialNode.id + "-" + relTypes[0] + "->" + otherNode.id
            END AS output
            UNION
            RETURN DISTINCT segment.text AS output
        }
        RETURN DISTINCT output
        LIMIT 25"""

        query_code = """CALL db.index.fulltext.queryNodes('entity', $query, {limit:3})
        YIELD node,score
        MATCH (node)<-[:MENTIONS]-(segment)
        WHERE segment.title = $title AND segment.paper_type = $paper_type
        CALL (node, segment){
            WITH node, segment
            MATCH (segment)-[:MENTIONS]->(otherNode)
            WHERE otherNode <> node
            MATCH (a)-[r]->(b) WHERE (a = otherNode AND b = node) OR (a = node AND b = otherNode)
            RETURN CASE
                WHEN otherNode = a THEN otherNode.id + "-" + type(r) + "->" + node.id
                ELSE node.id + "-" + type(r) + "->" + otherNode.id
            END AS output
            UNION
            RETURN DISTINCT segment.text AS output
        }
        RETURN DISTINCT output LIMIT 25"""
        
        entity_chain = self.entity_chain_generate(llm)
        node_chain = self.node_chain_generate(llm, allowed_nodes)
        result_list = []
        
        try:
            entities = entity_chain.invoke({"question": question})
            nodes = node_chain.invoke({"question": question})
            
            for node in nodes.names:
                try:
                    node = node.replace("\\","").replace("/","\\\\/").replace("}","\\}").replace("~","\\~").replace("{","\\{").replace("[","\\[").replace("]","\\]").replace("(","\\(").replace(")","\\)").replace("+","\\+").replace("-","\\-").replace(":","\\:").replace(";","\\;").replace("!","\\!").replace("?","\\?").replace("*","\\*")
                    response = self.graph.query(
                        query_node,
                        {"query": self.generate_full_text_query(node),
                        "title": title, 
                        "paper_type": paper_type}
                    )
                    result_list += [el['output'] for el in response]
                    result_list = list(set(result_list))
                except Exception as e:
                    logging.error(f"Error processing node '{node}': {e}")
                
            for entity in entities.names:
                try:
                    entity = entity.replace("\\","").replace("/","\\/").replace("}","\\}").replace("~","\\~").replace("{","\\{").replace("[","\\[").replace("]","\\]").replace("(","\\(").replace(")","\\)").replace("+","\\+").replace("-","\\-").replace(":","\\:").replace(";","\\;").replace("!","\\!").replace("?","\\?").replace("*","\\*")
                    response = self.graph.query(
                        query_code,
                        {"query": entity,
                        "title": title,
                        "paper_type": paper_type}
                    )
                    result_list += [el['output'] for el in response]
                    result_list = list(set(result_list))
                except Exception as e:
                    logging.error(f"Error processing entity '{entity}': {e}")
        except Exception as e:
            logging.error(f"Error in structured_retriever: {e}")
        
        return "\n".join(result_list)
    
    def retriever(self, question: str, llm, title: str, paper_type: str, allowed_nodes: List[str]) -> str:
        """检索器"""
        structured_data = self.structured_retriever(question, llm, title, paper_type, allowed_nodes)
        return f"""Structured data:\n{structured_data}"""


class ChainManager:
    """链管理器 - 负责各种推理链的创建和管理"""
    
    def __init__(self, config_manager: ConfigurationManager, query_manager: QueryManager, 
                 title: str, paper_type: str, allowed_nodes: List[str]):
        """
        初始化链管理器
        
        Args:
            config_manager: 配置管理器实例
            query_manager: 查询管理器实例
            title: 标题
            paper_type: 论文类型
            allowed_nodes: 允许的节点列表
        """
        self.config = config_manager
        self.query_manager = query_manager
        self.llm_models = config_manager.get_llm_models()
        self.title = title
        self.paper_type = paper_type
        self.allowed_nodes = allowed_nodes
    
    def search_query(self, llm) -> Any:
        """搜索查询链"""
        _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question,
in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

        def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
            buffer = []
            for human, ai in chat_history:
                buffer.append(HumanMessage(content=human))
                buffer.append(AIMessage(content=ai))
            return buffer

        _search_query = RunnableBranch(
            (
                RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                    run_name="HasChatHistoryCheck"
                ),
                RunnablePassthrough.assign(
                    chat_history=lambda x: _format_chat_history(x["chat_history"])
                )
                | CONDENSE_QUESTION_PROMPT
                | llm
                | StrOutputParser(),
            ),
            RunnableLambda(lambda x : x["question"]),
        )
        return _search_query
    
    def create_chain(self, llm_type: str) -> Any:
        """创建推理链"""
        template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            RunnableParallel({
                "context": (self.search_query(llm=self.llm_models['mini']) | 
                           (lambda q: self.query_manager.retriever(
                               question=q, 
                               llm=self.llm_models['mini'], 
                               title=self.title, 
                               paper_type=self.paper_type, 
                               allowed_nodes=self.allowed_nodes
                           ))),
                "question": RunnablePassthrough(),
            })
            | prompt
            | self.llm_models[llm_type]
            | StrOutputParser()
        )
        return chain


def concurrent_process(contents: List[Any], function: callable, max_workers: int = 5) -> List[Any]:
    """并发处理函数"""
    output_text = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(function, c) for c in contents]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            output_text.append(future.result())
    return output_text


class Knowledge_Graph:
    """
    知识图谱主类 - 保持向后兼容性
    
    这个类整合了所有管理器功能，保持与原有代码的接口兼容性
    """
    
    def __init__(self, markdown: Optional[str] = None, path: Optional[List[str]] = None, 
                 filtered: bool = True, type_name: Optional[str] = None):
        """
        初始化知识图谱
        
        Args:
            markdown: Markdown文本内容
            path: 文件路径列表
            filtered: 是否过滤（保留参数但未使用）
            type_name: 类型名称
        """
        # 初始化管理器
        self.config_manager = ConfigurationManager()
        self.doc_processor = DocumentProcessor(self.config_manager)
        
        # 获取LLM模型
        llm_models = self.config_manager.get_llm_models()
        self.graphllm = llm_models['graph']
        self.reasonllm = llm_models['reason']
        self.minillm = llm_models['mini']
        
        # 初始化图谱
        self.graph = Neo4jGraph()
        
        # 设置基本属性
        self.path = path
        self.type_name = type_name or ""
        self.markdown = markdown
        self.splits = []
        
        # 处理文档分割
        if "Template" in self.type_name:
            self.splits = self.doc_processor.split_template(self.type_name)
            self.example_dict = [
                "reagents_questions", "specific_equipment_questions", "common_equipment_questions",
                "synthesis_method_questions", "reagents_preparation_questions", "detailed_steps_questions",
                "characterization_questions", "activation_questions", "reaction_questions",
                "characterization_results_questions", "catalyst_performance_questions"
            ]
        elif self.path:
            self.splits = self.doc_processor.split_no_filtered_docs(self.path)
        elif self.markdown:
            self.splits = self.doc_processor.split_no_filtered_md(self.markdown)
        else:
            print(f"Warning: Knowledge_Graph initialized without path or markdown content (type_name: {self.type_name})")
            self.splits = []
        
        # 设置标题
        if self.markdown:
            self.title = self.minillm.invoke(
                "Please extract the article titles from the following text, making sure to distinguish them from journal names. Output only the article titles.\n\n"
                "Article titles are the specific content of an article, while journal names are the publications that carry the articles. When screening, carefully differentiate between the two to ensure only article titles are extracted, excluding journal names or other information. You should know that the title should not be too long or too short,and the extracted title does not need to be marked with double quotation marks, if you found there is no title in the text, please return \"None\".\n\n"
                f"Text:\n<text>\n{self.markdown[:500]}\n</text>\nOutput:"
            ).content.strip()
        elif self.splits and len(self.splits) > 0:
            for k, v in self.splits[0].metadata.items():
                self.title = v
                break
        else:
            self.title = "None"
        
        # 为所有splits设置title和paper_type
        if self.splits:
            for doc in self.splits:
                doc.metadata['title'] = self.title
                doc.metadata['paper_type'] = self.type_name
        
        # 初始化图谱转换管理器
        self.graph_transformer_manager = GraphTransformerManager(self.config_manager, self.type_name)
        self.llm_transformer = self.graph_transformer_manager.llm_transformer
        
        # 初始化查询管理器
        self.query_manager = QueryManager(self.config_manager, self.graph)
        
        # 初始化链管理器
        self.chain_manager = ChainManager(
            self.config_manager, 
            self.query_manager, 
            self.title, 
            self.type_name, 
            self.graph_transformer_manager.allowed_nodes
        )
        
        # 创建推理链
        self.reason_chain = self.chain_manager.create_chain('reason')
        self.mini_chain = self.chain_manager.create_chain('mini')
        self.graph_chain = self.chain_manager.create_chain('graph')
    
    def paper_type(self):
        """论文类型设置（向后兼容方法）"""
        # 这个方法在新架构中已经在__init__中处理了
        pass
    
    def filter_content(self, chunk: bool = True) -> List[Document]:
        """过滤内容"""
        self.splits, table_indices = self.doc_processor.split_long_docs_by_markdown(self.splits)
        no_table_splits = [
            doc for idx, doc in enumerate(self.splits) 
            if idx not in table_indices
        ]
        
        output_text = concurrent_process(no_table_splits, self.doc_processor.filter_template)
        
        for output, content in zip(output_text, no_table_splits):
            content.page_content = output.replace("Filtered Text:", "")
        
        table_docs = [self.splits[idx] for idx in table_indices]
        self.splits = no_table_splits + table_docs
        
        # 移除长度过短的分割
        for index in range(len(self.splits) - 1, -1, -1):
            if len(self.splits[index].page_content) < 30:
                del self.splits[index]
        
        if chunk:
            self.splits = split_md_filtered(self.splits)
        
        return self.splits
    
    def generate_graph(self) -> Neo4jGraph:
        """生成图谱"""
        logging.info("Converting Documents to Graph...")
        documents = self.llm_transformer.convert_to_graph_documents(self.splits)
        logging.info("Converting Documents to Graph...Complete!")
        logging.info("Adding Documents to Graph...")
        self.graph.add_graph_documents(
            documents,
            baseEntityLabel=True,
            include_source=True
        )
        logging.info("Adding Documents to Graph...Complete!")
        return self.graph
    
    def reason_answer(self, question: str) -> str:
        """推理回答"""
        return self.reason_chain.invoke({"question": question})
    
    def mini_answer(self, question: str) -> str:
        """迷你回答"""
        return self.mini_chain.invoke({"question": question})
    
    def graph_answer(self, question: str) -> str:
        """图谱回答"""
        return self.graph_chain.invoke({"question": question})
    
    def get_knowledge_graph(self, theme_id: str) -> str:
        """获取知识图谱"""
        try:
            result = self.graph.query("""
                MATCH (t:MindMap {id: $theme_id})-[:HAS_PRIMARY]->(p:MindMap)
                OPTIONAL MATCH (p)-[:HAS_SECONDARY]->(s:MindMap)
                OPTIONAL MATCH (s)-[:HAS_TERTIARY]->(r:MindMap)
                RETURN t, p, s, r
            """, {"theme_id": theme_id})

            knowledge_graph = []
            for record in result:
                knowledge_graph.append({
                    "theme": record["t"],
                    "primary": record["p"],
                    "secondary": record["s"],
                    "tertiary": record["r"]
                })
            
            formatted_graph = []
            for record in knowledge_graph:
                theme_id = record["theme"]["id"]
                primary_id = record["primary"]["id"] if record["primary"] else "无"
                secondary_id = record["secondary"]["id"] if record["secondary"] else "无"
                tertiary_id = record["tertiary"]["id"] if record["tertiary"] else "无"
                formatted_graph.append(f"{theme_id} -> {primary_id} -> {secondary_id} -> {tertiary_id}")

            return "\n".join(formatted_graph)
        except Exception as e:
            print(f"查询知识图谱时出错: {e}")
            return ""


# 保留原有的辅助函数以确保向后兼容性
def sanitize_query(query: str) -> str:
    """清理查询字符串（向后兼容函数）"""
    processor = DocumentProcessor(ConfigurationManager())
    return processor.sanitize_query(query)


if __name__ == "__main__":
    # 测试代码
    graph = Knowledge_Graph(path=["/mnt/d/Phd/practice/origin_paper/2023JACS_HWT/2023JACS_HWT.md"])
    graph.generate_graph()
    print("知识图谱优化版本测试完成！")
