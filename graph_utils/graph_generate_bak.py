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
from typing import Tuple, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
# Neo4j Graph导入 - 处理弃用警告
try:
    from langchain_neo4j import Neo4jGraph
except ImportError:
    # 如果新包不可用，回退到旧包但忽略警告
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from langchain_community.graphs import Neo4jGraph

# from langchain.document_loaders import WikipediaLoader
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j import GraphDatabase
# from yfiles_jupyter_graphs import GraphWidget
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.runnables import ConfigurableField, RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from .load_files import *
from langchain.schema import Document
from .chatgpt.config.config import (
    QWEN_CONFIG,
    OPENAI_CONFIG,
    DEEPSEEK_CONFIG,
)
import os, time, re
import logging
from langchain_community.graphs import Neo4jGraph
from tqdm import tqdm
import concurrent.futures
# os.environ["OPENAI_API_KEY"] = OPENAI_CONFIG["api_key"]
# os.environ["OPENAI_API_KEY"] = QWEN_CONFIG["api_key"]
config = DEEPSEEK_CONFIG
api_key = config['api_key']
base_url = config['base_url']
model_name = config["model_config"]["model"]
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
from string import ascii_letters, digits, whitespace, punctuation

def sanitize_query(query):
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


def concurrent_process(contents, function, max_workers=5):
    output_text = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(function, c) for c in contents]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            output_text.append(future.result())
    return output_text

class Knowledge_Graph():
    def __init__(self, markdown=None, path=None, filtered=True,type_name=None):
        
        API_SECRET_KEY = api_key 
        BASE_URL = base_url
        

        from langchain_deepseek import ChatDeepSeek
        # self.graphllm = ChatDeepSeek(model="deepseek-chat", api_key=api_key, base_url=base_url, temperature=0)
        # self.reasonllm = ChatDeepSeek(model="deepseek-reasoner", api_key=api_key, base_url=base_url)
        # self.minillm = ChatDeepSeek(model="deepseek-chat", api_key=api_key, base_url=base_url, temperature=0)
        
        
        self.graphllm = ChatOpenAI(temperature=0, model_name="gpt-4.1-2025-04-14")
        self.reasonllm = ChatOpenAI(model_name="o3-mini")
        self.minillm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        
        
        self.evalllm = ChatOpenAI(temperature=0.75, model_name="gpt-4o-mini",n=20)
        self.evalllm2 = ChatOpenAI(temperature=0.75, model_name="gpt-4o-mini")
        # self.minillm = ChatOpenAI(temperature=0, model_name="gpt-4.1-mini-2025-04-14")
        self.graph = Neo4jGraph()
        # self.vector_index = Neo4jVector.from_existing_graph(
        #     OpenAIEmbeddings(),
        #     search_type="hybrid",
        #     node_label="Document",
        #     # text_node_properties=["text"],
        #     text_node_properties=["title", "content"],
        #     embedding_node_property="embedding"
        # )
        self.keywords=["reference","author","supplementary reference","supplementary data","data availability","acknowledgement","funding","conflict of interest","competing interest","author contributions","references","acknowledg","declaration", "additional information","online connect"]
        self.path = path
        self.type_name = type_name or ""  # 确保type_name不为None
        self.markdown = markdown
        
        # 初始化splits属性，确保总是存在
        self.splits = []
        
        # self.filtered = filtered
        if "Template" in self.type_name:
            self.splits = self.split_template(self.type_name)
            self.example_dict = ["reagents_questions",
                            "specific_equipment_questions",
                            "common_equipment_questions",
                            "synthesis_method_questions",
                            "reagents_preparation_questions",
                            "detailed_steps_questions",
                            "characterization_questions",
                            "activation_questions",
                            "reaction_questions",
                            "characterization_results_questions",
                            "catalyst_performance_questions"]
        # elif self.path and self.filtered:
        #     self.splits = self.split_docs()
        elif self.path:
            self.splits=self.split_no_filtered_docs()
        # elif self.markdown and self.filtered:
        #     self.splits = self.split_docs()
        elif self.markdown:
            self.splits=self.split_no_filtered_md()
        else:
            # 如果既没有path也没有markdown，创建空的splits列表
            print(f"Warning: Knowledge_Graph initialized without path or markdown content (type_name: {self.type_name})")
            self.splits = []
            
        # for k, v in self.splits[0].metadata.items():
        #     self.title = v
            
        #     break
        if self.markdown:
            self.title = self.minillm.invoke("Please extract the article titles from the following text, making sure to distinguish them from journal names. Output only the article titles.\n\nArticle titles are the specific content of an article, while journal names are the publications that carry the articles. When screening, carefully differentiate between the two to ensure only article titles are extracted, excluding journal names or other information. You should know that the title should not be too long or too short,and the extracted title does not need to be marked with double quotation marks, if you found there is no title in the text, please return \"None\".\n\nText:\n<text>\n{}\n</text>\nOutput:".format(self.markdown[:500])).content.strip()
        
            # import pdb; pdb.set_trace()
        elif self.splits and len(self.splits) > 0:
            # 只有当splits非空时才尝试从中提取title
            for k, v in self.splits[0].metadata.items():
                self.title = v
                break
        else:
            # 如果没有splits，设置默认title
            self.title = "None"
            
        # 只有当splits非空时才设置title metadata
        if self.splits:
            for doc in self.splits:
                doc.metadata['title']=self.title
        self.paper_type()
        self.reason_chain = self.mix_reason_chain()
        self.mini_chain = self.mix_mini_chain()
        self.graph_chain = self.mix_graph_chain()
            
    def paper_type(self):
        """
        ### 实验操作与物质的关系
        - **is_used_by**：表示某个物质或设备被某个实验步骤或过程所使用。
        - **uses_material_from**：表示某个实验步骤或过程使用了来自某个节点的物质。
        - **consumes**：表示某个实验步骤或过程消耗了某个物质。
        - **produces**：表示某个实验步骤或过程产生了某个物质。
        - **is_synthesized_from**：表示某个物质是由某个实验步骤或过程合成的。
        - **is_synthesis_of**：表示某个实验步骤或过程是合成某个物质的过程。

        ### 物质之间的关系
        - **is_mixed_with**：表示某个物质与另一个物质被混合在一起。
        - **is_dissolved_in**：表示某个物质溶解在另一个物质中。
        - **is_precipitated_from**：表示某个物质从某个溶液中沉淀出来。
        - **is_filtered_from**：表示某个物质从某个混合物中过滤出来。
        - **is_distilled_from**：表示某个物质从某个混合物中蒸馏出来。
        - **is_extracted_from**：表示某个物质从某个混合物中萃取出来。
        - **is_purified_by**：表示某个物质通过某个过程被纯化。
        - **is_purification_of**：表示某个过程是纯化某个物质的过程。

        ### 实验设备与物质的关系
        - **contains_chemical**：表示某个设备或容器包含某个化学物质。
        - **is_contained_in**：表示某个化学物质被包含在某个设备或容器中。
        - **is_heated_in**：表示某个物质在某个设备中被加热。
        - **is_cooled_in**：表示某个物质在某个设备中被冷却。
        - **is_stirred_in**：表示某个物质在某个设备中被搅拌。
        - **is_sonicated_in**：表示某个物质在某个设备中被超声处理。

        ### 实验步骤之间的关系
        - **is_followed_by**：表示某个实验步骤紧接着另一个实验步骤。
        - **precedes**：表示某个实验步骤在另一个实验步骤之前。
        - **is_part_of**：表示某个实验步骤是某个更大实验过程的一部分。

        ### 物质与反应的关系
        - **reacts_with**：表示某个物质与另一个物质发生反应。
        - **is_catalyzed_by**：表示某个反应由某个催化剂催化。
        - **catalyzes**：表示某个催化剂催化某个反应。

        ### 物质与分析的关系
        - **is_analyzed_by**：表示某个物质通过某个分析方法被分析。
        - **is_characterized_by**：表示某个物质通过某个表征方法被表征。
        - **is_characterization_of**：表示某个表征方法是对某个物质的表征。

        ### 物质与条件的关系
        - **has_temperature**：表示某个实验步骤或过程具有某个温度条件。
        - **has_pressure**：表示某个实验步骤或过程具有某个压力条件。
        - **has_duration**：表示某个实验步骤或过程具有某个持续时间。
        - **has_concentration**：表示某个溶液具有某个浓度。

        ### 物质与属性的关系
        - **has_property**：表示某个物质具有某个属性。
        - **is_a**：表示某个物质是一种特定类型的物质。
        - **has_value**：表示某个属性具有某个具体的数值。"""
        self.allowed_rels=["description",
                        "mention",
                        "is_used_by","uses_material_from","consumes","produces","is_synthesized_from","is_synthesized_of",
                        "is_mixed_with","is_dissolved_in","is_filtered_from","is_purification_of",
                        "contains_chemical","is_contained_in","is_heated_in","is_cooled_in","is_stirred_in",
                        "is_followed_by","precedes","is_part_of",
                        "is_analyzed_by","is_characterized_by","is_characterization_of",
                        "has_temperature","has_pressure","has_duration","has_concentration",
                        "has_property","is_a","has_value"]
        """
        ### Equipment（设备）
        - **Synthesis Equipment**：合成设备，如反应釜、烧瓶、冷凝管等。
        - **Characterization Equipment**：表征设备，如X射线衍射仪（XRD）、热重分析仪（TGA）、扫描电子显微镜（SEM）等。
        - **Purification and Drying Equipment**：纯化和干燥设备，如旋转蒸发仪、真空干燥箱、离心机等。
        - **Other Equipment**：其他设备，如天平、量筒、移液枪等。

        ### Reagents（试剂）
        - **Metal Salts**：金属盐，如硫酸铜（CuSO₄）、氯化锌（ZnCl₂）等。
        - **Organic Ligands**：有机配体，如乙二胺四乙酸（EDTA）、邻菲咯啉（phen）等。
        - **Solvents**：溶剂，如甲醇（CH₃OH）、乙醇（C₂H₅OH）、水（H₂O）等。
        - **Base or Acid Regulators**：酸碱调节剂，如氢氧化钠（NaOH）、盐酸（HCl）等。
        - **Gases**：气体，如氮气（N₂）、氢气（H₂）、氧气（O₂）等。
        - **Other Reagents**：其他试剂，如催化剂、指示剂等。

        ### Characterization Methods（表征方法）
        - **Thermogravimetric analysis (TGA)**：热重分析。
        - **X-ray diffraction (XRD)**：X射线衍射。
        - **Gas chromatography (GC)**：气相色谱。
        - **Temperature-programmed desorption of ammonia (NH3-TPD)**：氨温度程序脱附。
        - **Fourier-transform infrared spectroscopy (FTIR)**：傅里叶变换红外光谱。
        - **Scanning electron microscopy (SEM)**：扫描电子显微镜。
        - **Transmission electron microscopy (TEM)**：透射电子显微镜。
        - **BET surface area analysis**：比表面积分析。
        - **Ultraviolet-visible spectroscopy (UV-Vis)**：紫外-可见光谱。
        - **Nuclear magnetic resonance (NMR)**：核磁共振。

        ### Reaction Conditions（反应条件）
        - **Temperature**：温度，如反应温度为100°C。
        - **Time**：时间，如反应时间为2小时。
        - **Solvent**：溶剂，如反应在乙醇中进行。
        - **Pressure**：压力，如反应在常压或高压下进行。
        - **Atmosphere**：气氛，如反应在氮气保护下进行。
        - **Stirring rate**：搅拌速率，如反应过程中搅拌速率为500rpm。
        - **Other Conditions**：其他条件，如光照、微波等。

        ### Purification Methods（纯化方法）
        - **Filtration**：过滤。
        - **Centrifugation**：离心。
        - **Washing**：洗涤。
        - **Column chromatography**：柱层析。
        - **Recrystallization**：重结晶。
        - **Distillation**：蒸馏。
        - **Extraction**：萃取。
        - **Other Purification Methods**：其他纯化方法，如超滤、透析等。

        ### Drying Conditions（干燥条件）
        - **Temperature**：温度，如干燥温度为80°C。
        - **Time**：时间，如干燥时间为12小时。
        - **Atmosphere**：气氛，如在真空或惰性气体氛围下干燥。
        - **Other Conditions**：其他条件，如微波干燥、冷冻干燥等。"""
        self.allowed_nodes=["description",
                        "Equipment:Synthesis Equipment","Equipment:Characterization Equipment","Equipment:Purification and Drying Equipment","Equipment:Other",
                        "Reagents:Solvents","Reagents:Base or Acid Regulators","Reagents:Gases","Reagents:Other",
                        "Characterization Methods:Thermogravimetric analysis(TGA) ","Characterization Methods:X-ray diffraction(XRD)", "Characterization Method:temperature-programmed desorption of ammonia (NH3-TPD) ","Characterization Method:Fourier-transform infrared spectroscopy (FTIR)","Characterization Method:Scanning electron microscopy (SEM)","Characterization Method:Transmission electron microscopy (TEM)","Characterization Method:BET surface area analysis","Characterization Method:Ultraviolet-visible spectroscopy (UV-Vis)",
                        "reaction:temperature","reaction:time","reaction:solvent","reaction:pressure","reaction:atmosphere","reaction:stirring rate","reaction:other",
                        "Purification:filtration","Purification:Centrifugation","Purification:Washing","Purification:Column chromatography","Purification:Recrystallization","Purification:Distillation","Purification:Extraction","Purification:other",
                        "Drying:temperature","Drying:time","Drying:atmosphere","Drying:other",
                        "Documents"]
        for doc in self.splits:
            doc.metadata['paper_type']=self.type_name
        if self.type_name == "FT Framework":
            # 费托合成专属节点属性扩展
            self.allowed_nodes.extend([
                # 催化剂前驱体特性
                "Reagents:Promoter Precursors",  # 助剂前驱体（如碱金属、稀土元素）
                "Reagents:Additive Precursors",  # 助剂前驱体（如碱金属、稀土元素）
                "Reagents:Support Materials",    # 载体材料（如γ-Al2O3、SiO2）
                "Reagents:Surface Modifiers",    # 载体材料（如γ-Al2O3、SiO2）
                "Reagents:Reducing Agents",      # 还原剂（如H2、NH3）
                
                # 特殊设备节点
                "Equipment:Fixed-bed Reactors",  # 固定床反应器
                "Equipment:Slurry Reactors",     # 浆液床反应器
                "Equipment:Fluidized-bed Reactors", # 流化床反应器
                "Equipment:CO2 Analyzer",        # 二氧化碳分析仪
                
                # 反应条件细化
                "reaction:H2_CO_ratio",          # 氢碳比(H2/CO)
                "reaction:space_time_velocity",  # 空间时间速度(STV)
                "reaction:gas hourly space velocity (GHSV)", # 气时体积速度
                
                # 催化剂活化特性
                "Activation:reduction_temperature", # 还原温度
                "Activation:reduction_gas",         # 还原气体
                "Activation:reduction_time",        # 还原时间
                
                # 产物分析指标
                "Results:alpha_value",              # α值（链增长概率）
                "Results:C5+ selectivity",          # C5+选择性
                "Results:CO2_selectivity",          # CO2选择性
                "Results:olefin_to_paraffin_ratio", # 烯烃/烷烃比
                
                # 催化剂失活分析
                "Deactivation:carbon_deposition",   # 碳沉积量
                "Deactivation:poisoning_elements",  # 毒化元素
                "Deactivation:deactivation_rate",   # 失活速率
                
                # 原位表征方法
                "Characterization Methods:Operando Spectroscopy", # 原位光谱
                "Characterization Methods:In-situ XRD",           # 原位XRD
                "Characterization Methods:Temperature-programmed reduction (TPR)", # 程序升温还原
                "Characterization Method:Gas chromatography (GC)",
                
                # 工艺参数
                "Process:feedstock_composition",    # 原料组成
                "Process:product_distribution",     # 产物分布
                "Process:water_gas_shift_activity", # 水煤气变换活性
            ])  
            # 费托合成专属关系扩展
            self.allowed_rels.extend([
                # 催化剂相关关系
                "is_reduced_by",                  # 催化剂被还原条件激活
                "is_promoted_by",                 # 催化剂被助剂促进
                "supports_catalyst",              # 载体支撑催化剂
                "is_loaded_with",                 # 催化剂负载于载体
                
                # 反应条件关系
                "operates_under",                 # 反应器在特定条件下运行
                "requires_H2_CO_ratio",           # 反应需要特定氢碳比
                "has_space_time_velocity",        # 反应具有特定时空速度
                
                # 产物与性能关系
                "exhibits_selectivity_for",       # 催化剂对特定产物的选择性
                "produces_product_distribution",  # 生成特定产物分布
                "has_alpha_value",                # 具有特定α值（链增长概率）
                
                # 失活机制关系
                "undergoes_deactivation_due_to",  # 催化剂因...失活
                "shows_carbon_deposition",        # 表现出碳沉积
                
                # 工艺流程关系
                "is_followed_by_separation",      # 反应后接分离步骤
                "requires_pretreatment",          # 需要预处理步骤
                "is_optimized_for",               # 工艺针对...优化
                
                # 原位表征关系
                "is_monitored_by",                # 反应过程被...监测
                "undergoes_in_situ_characterization", # 进行原位表征
                
                "reacts_with","is_catalyzed_by","catalyzes",
            ])
            self.llm_transformer = LLMGraphTransformer(
                llm=self.graphllm,
                # allowed_nodes=self.allowed_nodes,
                # allowed_relationships=self.allowed_rels,
                # node_properties=["description","Equipment", "Reagents","Characterization Methods"],
                # relationship_properties=["description","Reaction","Characterization Methods","Purification","Drying"],
                node_properties=["description"],
                relationship_properties=["description"],
                prompt=ChatPromptTemplate.from_messages([(
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
        ]),
            )
        elif self.type_name == "MoF Framework":
            """
            ### MOF Specific Nodes（MOF特有节点）
            - **MOF Structure**：MOF结构，如HKUST-1、MOF-5、UiO-66等。
            - **Pore Size**：孔径大小，如MOF的孔径为3.8nm。
            - **Surface Area**：比表面积，如MOF的比表面积为1000m²/g。
            - **Adsorption Capacity**：吸附容量，如MOF对二氧化碳的吸附容量为5.2mmol/g。
            - **Catalytic Activity**：催化活性，如MOF在某催化反应中的转化率为85%。
            - **Stability**：稳定性，如MOF在水中的稳定性测试结果。
            - **Functional Groups**：功能基团，如MOF表面修饰的氨基、羧基等。
            - **Synthesis Method**：合成方法，如溶剂热法、微波辅助合成法等。
            - **Application**：应用，如气体存储、催化、分离等。"""
            self.allowed_nodes+=[
                "MOF Structure","Pore Size","Surface Area","Adsorption Capacity","Catalytic Activity","Stability","Functional Groups","Synthesis Method","Application", "Reagents:Organic Ligands","Reagents:Metal Salts", "Characterization Method:Nuclear magnetic resonance (NMR)",
            ]
            """
            ### MOF合成相关
            - **is_coordination_of**：表示金属节点与有机配体之间的配位关系，这是MOF合成的核心。
            - **has_metal_node**：用于描述MOF结构中包含的金属节点类型。
            - **has_organic_ligand**：用于描述MOF结构中包含的有机配体类型。
            - **is_assembled_from**：表示MOF是由特定的金属节点和有机配体组装而成。
            - **is_solvent热_synthetized**：表示MOF是通过溶剂热法合成的。

            ### MOF结构与性质相关
            - **has_pore_structure**：描述MOF具有特定的孔隙结构。
            - **has_surface_area**：表示MOF具有特定的比表面积。
            - **has_pore_size**：描述MOF孔隙的大小。
            - **exhibits_adsorption_of**：表示MOF对特定物质具有吸附性能。

            ### MOF应用相关
            - **is_used_for_catalysis**：表示MOF被用于催化反应。
            - **is_used_for_separation**：表示MOF被用于物质分离。
            - **is_used_for_storage**：表示MOF被用于气体存储等应用。
            - **is_functionalized_with**：表示MOF经过特定的功能化修饰以增强其性能。

            ### MOF表征相关
            - **is_analyzed_by_XRD**：表示MOF通过X射线衍射进行结构分析。
            - **is_analyzed_by_N2_adsorption**：表示MOF通过氮气吸附-脱附等温线进行孔隙结构分析。
            - **is_analyzed_by_SEM**：表示MOF通过扫描电子显微镜进行形貌观察。"""
            
            self.allowed_rels+=[
                "is_coordination_of","has_metal_node","has_organic_ligand","is_assembled_from","is_solvent热_synthetized",
                "has_pore_structure","has_surface_area","has_pore_size","exhibits_adsorption_of",
                "is_used_for_catalysis","is_used_for_separation","is_used_for_storage","is_functionalized_with","is_sonicated_in",
                "is_analyzed_by_XRD","is_analyzed_by_N2_adsorption","is_analyzed_by_SEM","is_precipitated_from","is_distilled_from","is_extracted_from","is_purified_by",
            ]
            
            """old prompt## 1. Overview
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
## 5. Strict Compliance
Strictly adhere to the rules. Non-compliance will result in termination."""
            self.llm_transformer = LLMGraphTransformer(
                llm=self.graphllm,
                # node_properties=["description","Equipment", "Reagents","Characterization Methods"],
                # relationship_properties=["description","Reaction","Characterization Methods","Purification","Drying"],
                node_properties=["description"],
                relationship_properties=["description"],
                prompt=ChatPromptTemplate.from_messages([(
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
        ]),
            )
        else:
            self.llm_transformer = LLMGraphTransformer(
                llm=self.graphllm,
                # node_properties=["description","Equipment", "Reagents","Characterization Methods"],
                # relationship_properties=["description","Reaction","Characterization Methods","Purification","Drying"],
                node_properties=["description"],
                relationship_properties=["description"],)
        
    # def split_docs(self):
    #     splits = []
    #     for p in self.path:
    #         splits += load_md_filtered_batch(p)
    #     for i in range(len(splits),0,-1):
    #         for key, value in splits[i-1].metadata.items():
    #             if any(k in value.lower() for k in self.keywords):
    #                 # print(i)
    #                 del splits[i-1]
        
    #     llm = llm_tools(api_key=SPLIT_CONFIG['api_key'], 
    #                     base_url=SPLIT_CONFIG['base_url'], 
    #                     organization=SPLIT_CONFIG['organization'], 
    #                     model_config=SPLIT_CONFIG["model_config"], 
    #                     proxy=GENERAL_CONFIG["proxy"])
    #     input_text = []
    #     for content in splits:
    #         input_text.append(content.page_content)
    #     output_text = llm.batch_filter(input_text)
        
    #     for output, content in zip(output_text, splits):
    #         content.page_content = output
    #     self.splits = split_md_filtered(splits)
    #     return self.splits
    
        
    def filter_template(self, content, max_retries=5, retry_interval=1):
        """带报错重试机制的内容过滤函数
        
        Args:
            content: 待过滤的内容对象
            max_retries: 最大重试次数（默认3次）
            retry_interval: 重试间隔（秒，默认1秒）
        
        Returns:
            str: 过滤后的文本内容
        
        Raises:
            Exception: 超过最大重试次数后仍失败时抛出最后一次异常
        """
        message = [
            {"role": "system", "content": APPLICATION_PROMPTS["decompose_prompts"]["system_prompt"]},
            {"role": "user", "content": APPLICATION_PROMPTS["decompose_prompts"]["content_filter"].replace('{content}', content.page_content, 1)}
        ]
        
        last_exception = None  # 记录最后一次异常
        
        for attempt in range(max_retries + 1):  # 0到max_retries共max_retries+1次尝试
            try:
                text = self.reasonllm.invoke(message).content
                time.sleep(1)  # 保留原有的API调用间隔
                return text  # 成功返回
            
            except Exception as e:
                last_exception = e  # 记录异常
                if attempt < max_retries:
                    print(f"第{attempt+1}次调用失败，{retry_interval}秒后重试... 错误信息: {str(e)}")
                    time.sleep(retry_interval)  # 等待重试
                else:
                    print(f"已达到最大重试次数{max_retries}次，调用最终失败")
                    raise last_exception  # 抛出最后一次异常
        
        # 理论上不会执行到这里（循环内已处理所有情况）
        return ""
    def split_by_custom_separator(self, docs, separator="\n\n"):
        """
        按照指定的分隔符分割Document对象中的文本内容，生成一个新的Document列表。

        Args:
            docs (list[Document]): 需要分割的Document对象列表。
            separator (str, optional): 分隔符。默认为"\n\n"。

        Returns:
            list[Document]: 分割后的Document对象列表。
        """
        new_docs = []
        for doc in docs:
            split_texts = doc.page_content.split(separator)
            split_texts = [t for t in split_texts if t.strip()]  # 去除空字符串
            for text in split_texts:
                new_docs.append(Document(page_content=text, metadata=doc.metadata.copy()))
        return new_docs
    
    def add_separator_before_tables(self, text):
        """
        在每个表格之前正确插入带####的标题分隔符，确保标题紧邻表格上方
        """
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

    def split_long_docs_by_markdown(self, docs):
        """
        组合Markdown标题分割和字符数分割的文档处理流程
        """
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
                # 2. Markdown标题层级分割（返回的是Document对象列表）
                markdown_docs = text_splitter_markdown.split_text(modified_content)
                # 3. 对每个Markdown块提取文本并进行字符数分割
                for markdown_doc in markdown_docs:
                    # 提取纯文本内容
                    markdown_text = markdown_doc.page_content
                    char_splits = text_splitter_char.split_text(markdown_text)
                    # 将字符分割结果包装为Document对象（保留原元数据）
                    for split_text in char_splits:
                        new_doc = Document(
                            page_content=split_text,
                            metadata={**doc.metadata, **markdown_doc.metadata}  # 保留标题分割的元数据
                        )
                        new_docs.append(new_doc)
                        if "Table" in markdown_doc.metadata.get("Header 4", ""):
                            table_indices.append(len(new_docs) - 1)
            else:
                new_docs.append(doc)
        
        return new_docs, table_indices
    
    def filter_content(self, chunk = True):
        # llm = llm_tools(api_key=SPLIT_CONFIG['api_key'], 
        #                 base_url=SPLIT_CONFIG['base_url'], 
        #                 organization=SPLIT_CONFIG['organization'], 
        #                 model_config=SPLIT_CONFIG["model_config"], 
        #                 proxy=GENERAL_CONFIG["proxy"])
        
        # input_text = []
        self.splits, table_indices = self.split_long_docs_by_markdown(self.splits)
        no_table_splits = [
            doc for idx, doc in enumerate(self.splits) 
            if idx not in table_indices  # 保留索引不在 table_indices 中的文档
        ]
        output_text = []
        # for content in self.splits:
        #     # input_text.append(content.page_content)
        #     message = [{"role":"system","content":APPLICATION_PROMPTS["decompose_prompts"]["system_prompt"]},
        #             {"role":"user","content":APPLICATION_PROMPTS["decompose_prompts"]["content_filter"].replace('{content}', content.page_content, 1)}
        #             ]
            # output_text.append(self.llm.invoke(message))
        output_text = concurrent_process(no_table_splits, self.filter_template)
        # output_text = llm.batch_filter(input_text)
        
        for output, content in zip(output_text,no_table_splits):
            content.page_content = output.replace("Filtered Text:","")
        
        table_docs = [self.splits[idx] for idx in table_indices]
        self.splits = no_table_splits + table_docs
        for index in range(len(self.splits) - 1, -1, -1):  # 从后向前遍历
            if len(self.splits[index].page_content) < 30:
                # print(self.splits[index].page_content)
                del self.splits[index]
        if chunk:
            self.splits = split_md_filtered(self.splits)
        return self.splits
    
    def split_no_filtered_docs(self):
        splits = []
        for p in self.path:
            splits += load_md_no_filtered_batch(p)
        for i in range(len(splits),0,-1):
            for key, value in splits[i-1].metadata.items():
                if any(k in value.lower() for k in self.keywords):
                    # print(i)
                    del splits[i-1]
        self.splits = splits
        # self.splits = split_md_filtered(splits)
        return self.splits
    
    def split_no_filtered_md(self):    
        
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            # strip_headers = False
            )
        splits = markdown_splitter.split_text(self.markdown)
        for i in range(len(splits),0,-1):
            for key, value in splits[i-1].metadata.items():
                if any(k in value.lower() for k in self.keywords):
                    # print(i)
                    del splits[i-1]
                    break
        self.splits = splits
        for index in range(len(self.splits) - 1, -1, -1):  # 从后向前遍历
            if len(self.splits[index].page_content) < 30:
                # print(self.splits[index].page_content)
                del self.splits[index]
        # self.splits = split_md_filtered(splits)
        return self.splits
    
    def split_template(self, type_name):
        splits = []
        if type_name=="MOFTemplate":
            for p in ["./template/MOF Framework Experiment Template/MOF Framework Experiment Template.md"]:
                splits += load_md_no_filtered_batch(p)
            for i in range(len(splits),0,-1):
                for key, value in splits[i-1].metadata.items():
                    if any(k in value.lower() for k in self.keywords):
                        # print(i)
                        del splits[i-1]
            self.splits = splits
            # self.splits = split_md_filtered(splits)
        elif type_name=="FTTemplate":
            for p in ["./template/FT/ft.md"]:
                splits += load_md_no_filtered_batch(p)
            for i in range(len(splits),0,-1):
                for key, value in splits[i-1].metadata.items():
                    if any(k in value.lower() for k in self.keywords):
                        # print(i)
                        del splits[i-1]
            self.splits = splits
            # self.splits = split_md_filtered(splits)
        return self.splits
        
    def generate_graph(self):
        logging.info("Converting Documnets to Graph...")
        documents = self.llm_transformer.convert_to_graph_documents(self.splits)
        logging.info("Converting Documnets to Graph...Complete!")
        logging.info("Adding Documents to Graph...")
        self.graph.add_graph_documents(
            documents,
            baseEntityLabel=True,
            include_source=True
        )
        logging.info("Adding Documents to Graph...Complete!")
        return self.graph
    
    def node_chain_generate(self, llm):
        class Node_chain(BaseModel):
            """Identifying information about node."""

            names: List[str] = Field(
                ...,
                description="Please filter out the key nodes (nodes) that might be mentioned in the text from the provided list of allowed nodes. Only list the nodes that are actually mentioned in the text, and disregard those that are not mentioned. "
                "{allowed_nodes}".format(allowed_nodes=self.allowed_nodes),
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are extracting chemical reagents, equipments, reaction, charactorization entities from the text.",
                ),
                (
                    "human",
                    "Use the given format to extract information from the following "
                    "input: {question}",
                ),
            ]
        )

        node_chain = prompt | llm.with_structured_output(Node_chain)
        return node_chain
    
    def entity_chain_generate(self, llm):
        # Retriever

        # self.graph.query(
        #     "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

        # Extract entities from text
        class Entities(BaseModel):
            """Identifying information about entities."""

            names: List[str] = Field(
                ...,
                description="All chemical substances mentioned in the text, along with their relationships, including catalysis, solvents, atmosphere protection, etc."
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
            "You are extracting chemical reagents, equipments, reaction, charactorization entities from the text.",
                ),
                (
                    "human",
                    "Use the given format to extract information from the following "
                    "input: {question}",
                ),
            ]
        )

        entity_chain = prompt | llm.with_structured_output(Entities)
        return entity_chain
    
    def generate_full_text_query(self, input: str) -> str:
        """
        Generate a full-text search query for a given input string.

        This function constructs a query string suitable for a full-text search.
        It processes the input string by splitting it into words and appending a
        similarity threshold (~2 changed characters) to each word, then combines
        them using the AND operator. Useful for mapping entities from user questions
        to database values, and allows for some misspelings.
        """
        # full_text_query = ""
        # words = [el for el in remove_lucene_chars(input).split() if el]
        # for word in words[:-1]:
        #     full_text_query += f" {word}~2 AND"
        # full_text_query += f" {words[-1]}~2"
        # return full_text_query.strip()
        
        full_text_query = "(?i).*"
        words = [el for el in remove_lucene_chars(input).split() if el]
        for word in words[:-1]:
            full_text_query += f"{(word.lower())}.*"
        full_text_query += f"{words[-1].lower()}.*"
        return full_text_query.strip()

    # Fulltext index query
    def structured_retriever(self, question: str, llm) -> str:
        """
        Collects the neighborhood of entities mentioned
        in the question
        """
        
        query_node="""  MATCH (initialNode)<-[:MENTIONS]-(segment)
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

        query_code="""CALL db.index.fulltext.queryNodes('entity', $query, {limit:3})
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
        RETURN DISTINCT output LIMIT 25
        """
        entity_chain = self.entity_chain_generate(llm)
        node_chain = self.node_chain_generate(llm)
        result = ""
        result_list = []
        entities = entity_chain.invoke({"question": question})
        nodes = node_chain.invoke({"question": question})
        for node in nodes.names:
            try:
                node = sanitize_query(node)
                node = node.replace("/","\\\\/").replace("}","\\}").replace("~","\\~").replace("{","\\{").replace("[","\\[").replace("]","\\]").replace("(","\\(").replace(")","\\)").replace("+","\\+").replace("-","\\-").replace(":","\\:").replace(";","\\;").replace("!","\\!").replace("?","\\?").replace("*","\\*")
                response = self.graph.query(
                    query_node,
                    {"query": self.generate_full_text_query(node),
                    "title": self.title, 
                    "paper_type": self.type_name}
                    # {"query": node},
                )
                # result += "\n".join([el['output'] for el in response])+'\n'
                result_list += [el['output'] for el in response]
                result_list = list(set(result_list))
            except Exception as e:
                logging.error(f"Error processing node '{node}': {e}")
            
        for entity in entities.names:
            try:
                # entity = sanitize_query(entity)
                entity = entity.replace("\\","").replace("/","\\/").replace("}","\\}").replace("~","\\~").replace("{","\\{").replace("[","\\[").replace("]","\\]").replace("(","\\(").replace(")","\\)").replace("+","\\+").replace("-","\\-").replace(":","\\:").replace(";","\\;").replace("!","\\!").replace("?","\\?").replace("*","\\*")
                response = self.graph.query(
                    query_code,
                    # {"query": self.generate_full_text_query(entity)},
                    {"query": entity,
                    "title": self.title,
                    "paper_type": self.type_name}
                )
                # result += "\n".join([el['output'] for el in response])+'\n'
                result_list += [el['output'] for el in response]
                result_list = list(set(result_list))
            except Exception as e:
                logging.error(f"Error processing entity '{entity}': {e}")
        result = "\n".join(result_list)
        return result
    
    def retriever(self, question: str, llm):
        # print(f"Search query: {question}")
        structured_data = self.structured_retriever(question, llm)
        # unstructured_data = [el.page_content for el in self.vector_index.similarity_search(query=question, k=10)]
        final_data = f"""Structured data:
    {structured_data}
        """
        return final_data
    
    def search_query(self, llm):
        # Condense a chat history and follow-up question into a standalone question
        _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question,
in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

        def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
            buffer = []
            for human, ai in chat_history:
                buffer.append(HumanMessage(content=human))
                buffer.append(AIMessage(content=ai))
            return buffer

        _search_query = RunnableBranch(
            # If input includes chat_history, we condense it with the follow-up question
            (
                RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                    run_name="HasChatHistoryCheck"
                ),  # Condense follow-up question and chat into a standalone_question
                RunnablePassthrough.assign(
                    chat_history=lambda x: _format_chat_history(x["chat_history"])
                )
                | CONDENSE_QUESTION_PROMPT
                | llm
                | StrOutputParser(),
            ),
            # Else, we have no chat history, so just pass through the question
            RunnableLambda(lambda x : x["question"]),
        )
        return _search_query
    
    def mix_reason_chain(self):
        template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            RunnableParallel(
                {
                    "context": (self.search_query(llm=self.minillm) | 
                           (lambda q: self.retriever(question=q, llm=self.minillm))),
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.reasonllm
            | StrOutputParser()
        )
        return chain
    
    def mix_mini_chain(self):
        template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            RunnableParallel(
                {
                    "context": (self.search_query(llm=self.minillm) | 
                           (lambda q: self.retriever(question=q, llm=self.minillm))),
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.minillm
            | StrOutputParser()
        )
        return chain
    def mix_graph_chain(self):
        template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            RunnableParallel(
                {
                    "context": (self.search_query(llm=self.minillm) | 
                           (lambda q: self.retriever(question=q, llm=self.minillm))),
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.graphllm
            | StrOutputParser()
        )
        return chain
    
    def reason_answer(self, question):
        return self.reason_chain.invoke({"question": question})
    
    def mini_answer(self, question):
        return self.mini_chain.invoke({"question": question})
    
    def graph_answer(self, question):
        return self.graph_chain.invoke({"question": question})
    
    def many_question(self, questions):
        question_chains = {}
        for i in range(len(questions)):
            question_chains[f"question_{i}"] = self.mixure_chain
        map_chain = RunnableParallel(**question_chains)
        questions = {
            f"question_{i}": {"question": questions[i]} for i in range(1, 11)
        }
        response = map_chain.invoke(questions)
        return response
    
    def get_knowledge_graph(self, theme_id):
        try:
            # 查询知识图谱
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
            # 格式化返回数据为字符串
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
        finally:
            pass
    
if __name__ == "__main__":
    graph = Knowledge_Graph(["/mnt/d/Phd/practice/origin_paper/2023JACS_HWT/2023JACS_HWT.md"])
    graph.generate_graph()
    print(graph.question("'## 4. Characterization Methods\n\nThe characterization of USTC-9 involved a suite of techniques to determine its structural integrity and efficacy as a catalyst. Single-crystal X-ray diffraction, particularly with synchrotron radiation at 173 K, provided vital insights into the crystalline structure and confirmed the enhanced arrangement of TmCPP-M linkers within the pores. Complementary techniques such as nitrogen sorption isotherms revealed type I microporous characteristics, quantifying BET surface areas of 2294 m²/g for USTC-9(Fe) and 2067 m²/g for USTC-9(In).\n\nThermogravimetric analysis assessed thermal stability, showing frameworks retained integrity up to 330 °C. Additionally, NH3 temperature-programmed desorption (TPD) measured Lewis acidity, indicating USTC-9(Fe) shows higher acid strength compared to USTC-9(In). The combination of these methods demonstrated advantageously dense, self-supporting structures and robust coordination bonds, bolstering claims regarding USTC-9’s stability and catalytic potential in CO2 cycloaddition reactions.'"))
