def unified_materials_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # 统一类别的实体模型：仅分三大类
    class UnifiedMaterialsEntities(BaseModel):
        """从文本中提取的材料相关实体，统一分为三大类"""
        
        reagents: List[str] = Field(
            default=[], 
            description="All chemical reagents, including metal precursors, organic linkers, modulators, solvents, acids/bases, structure-directing agents, surface modifiers, atmosphere gases and other chemical substances used in MOF experiments"
        )
        
        experimental_equipment: List[str] = Field(
            default=[], 
            description="All specific experimental equipment, including synthesis equipment, characterization equipment, activation equipment, reaction equipment, product analysis equipment and other equipment directly used in MOF experimental processes"
        )
        
        common_lab_equipment: List[str] = Field(
            default=[], 
            description="All common laboratory equipment, including drying equipment, calcination equipment, balances, stirrers, pumps, filtration apparatus and other general laboratory tools"
        )

    # 提示词专注于提取三大类实体
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in chemical experiments (Metal Organic Framework synthesis).
                Extract all relevant entities from the text and classify them into three categories ONLY:
                1. Reagents: All chemical substances used in MOF experiments, including but not limited to:
                   - Metal precursors (e.g., zinc nitrate, copper acetate)
                   - Organic linkers (e.g., terephthalic acid, 2-methylimidazole)
                   - Modulators (e.g., acetic acid, triethylamine)
                   - Solvents (e.g., DMF, ethanol, water)
                   - Structure-directing agents, surface modifiers, atmosphere gases, washing agents, etc.
                  
                2. Experimental Equipment: Specialized equipment directly involved in MOF experiment processes:
                   - Synthesis equipment (Teflon-lined autoclaves, microwave reactors, flow reactors)
                   - Characterization instruments (PXRD, SEM, TEM, BET, TGA, XPS, NMR, etc.)
                   - Activation equipment (vacuum ovens, tube furnaces, supercritical CO₂ dryers)
                   - Reaction equipment, product analysis instruments (GC, GC-MS), etc.
                  
                3. Common Lab Equipment: General laboratory tools for routine operations:
                   - Drying equipment, calcination equipment, balances, magnetic stirrers, pumps, filtration apparatus, etc.

                Guidelines:
                - Only include entities explicitly mentioned in the text (no assumptions)
                - Each entity should appear in only one most appropriate category
                - Return simple lists of entity names (include key attributes if critical, e.g., "N₂ (99.999% purity)", "100 mL Teflon-lined autoclave")
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
        """Extracted entities related to MOF synthesis methods (simplified 3 categories)"""
        
        synthesis_techniques: List[str] = Field(
            default=[], 
            description="Names of MOF synthesis methods/techniques (e.g., solvothermal method, hydrothermal method, microwave-assisted synthesis, mechanochemical synthesis, room-temperature synthesis)"
        )
        
        chemical_substances: List[str] = Field(
            default=[], 
            description="All chemical reagents with details (concentrations, formulas, amounts) (e.g., Zn(NO₃)₂·6H₂O, terephthalic acid (0.1M), acetic acid modulator, DMF solvent)"
        )
        
        experimental_factors: List[str] = Field(
            default=[], 
            description="Combined equipment with specific conditions (e.g., Teflon-lined autoclave at 120°C for 24 hours, microwave reactor at 150°C for 30 minutes, ball mill at 30 Hz for 1 hour)"
        )

    # Prompt template for simplified extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in MOF synthesis methods.
                Extract all relevant entities from the text and classify them into these 3 categories ONLY:
                1. Synthesis techniques: Names of MOF preparation methods/techniques
                2. Chemical substances: All reagents with concentrations/formulas/amounts if specified
                3. Experimental factors: Equipment combined with their specific conditions (temperature, pressure, time, frequency with units) as single entities

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

    # Entity model with 2 categories
    class SynthesisProceduresEntities(BaseModel):
        """Extracted entities from MOF synthesis procedures"""
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with quantities used in MOF preparation"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Specific equipment with their associated experimental parameters for MOF synthesis (e.g., Teflon-lined autoclave heated at 120°C for 24 hours, analytical balance (0.0001g precision), magnetic stirrer at 600 rpm for 20 minutes)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in MOF synthesis procedures.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Chemical reagents: All substances with quantities used in MOF preparation (metal salts, organic linkers, solvents, modulators, additives)
                2. Equipment with parameters: Specific equipment names (including models/specifications when mentioned) combined with their directly associated experimental parameters (temperature, time, speed, atmosphere, pressure, etc.)

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entity belongs to only one most appropriate category
                - Preserve exact values, units, and chemical names as in original text
                - For equipment, use specific names rather than general types (e.g., "Mettler Toledo AL204 Analytical Balance (0.1 mg)" instead of "balance")
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

    # Entity model with 1 core category
    class CharacterizationEntities(BaseModel):
        """Extracted entities from MOF characterization methods"""
        
        characterization_systems: List[str] = Field(
            default=[], 
            description="Complete characterization systems combining technique, instrument, and operational parameters for MOF analysis (e.g., PXRD using Bruker D8 Advance diffractometer with Cu Kα radiation at 40kV/40mA over 2θ range 5°-50°, step size 0.02°; BET surface area analysis using Micromeritics ASAP 2020 with N₂ adsorption at 77K, degassing at 150°C for 12h under vacuum)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in MOF characterization methods.
                Extract all relevant entities from the text and combine them into a single category:
                1. Characterization systems: Complete descriptions that combine three elements as a single entity:
                   - The characterization technique/method (e.g., PXRD, FTIR, BET, SEM, TEM, TGA, XPS, NMR)
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

    # Entity model with 2 core categories
    class CatalyticEvaluationEntities(BaseModel):
        """Extracted entities from MOF activation and application/performance evaluation conditions"""
        
        activation_conditions: List[str] = Field(
            default=[], 
            description="MOF activation process details including gases, solvents and parameters (e.g., activation at 150°C under vacuum for 12 hours; N₂ flow at 100 mL/min at 120°C; supercritical CO₂ drying at 40°C and 150 bar)"
        )
        
        reaction_conditions: List[str] = Field(
            default=[], 
            description="MOF application/performance evaluation details including gases, analytes and parameters (e.g., gas adsorption at 77K up to 1 bar; CO₂/N₂ mixture at 20 mL/min for breakthrough tests; catalytic reaction at 80°C, 1 bar H₂ pressure)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in MOF evaluation methods (activation and reaction_conditions.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Activation conditions: Complete activation process descriptions for MOFs combining gases/solvents (with compositions if specified) and their corresponding operational parameters (temperatures, pressures, times, flow rates, vacuum levels with units)
                2. reaction_conditions: Complete application/performance evaluation process descriptions for MOFs combining gases/analytes (with compositions if specified) and their corresponding operational parameters (temperatures, pressures, flow rates, concentrations, partial pressures with units)

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must combine relevant gas/solvent/analyte and its associated parameters for the specific process
                - Preserve exact values, units, compositions, and process relationships as in original text
                - Focus exclusively on activation and application/testing conditions (exclude characterization-related parameters)
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all MOF evaluation entities from the following text: {question}"
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

    # Entity model with 2 core categories
    class ResultsEntities(BaseModel):
        """Extracted entities from MOF characterization results and application performance data"""
        
        characterization_results: List[str] = Field(
            default=[], 
            description="Associated pairs of characterization indicators + their data/conclusions for MOFs (e.g., BET surface area 3200 m²/g, PXRD pattern matches MOF-5, pore size 1.1 nm, thermal stability up to 400°C, elemental composition Zn²⁺ and carboxylate groups)"
        )
        
        performance_results: List[str] = Field(
            default=[], 
            description="Associated pairs of performance indicators + their data/trends for MOF applications (e.g., CO₂ uptake 5.2 mmol/g at 1 bar, CO₂/N₂ selectivity 15, catalytic conversion 92% after 6h, cycling stability 95% after 10 cycles, response time 30 s for NH₃ detection)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in MOF results (characterization & application performance).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY. Each entry must be a **complete, associated unit** (indicator + corresponding data/conclusion/trend) — do NOT extract isolated indicators or disconnected data.
                
                1. Characterization results: Combine "characterization indicator (property/metric)" + "its specific data/conclusion" for MOFs (e.g., "BET surface area 3200 m²/g" instead of separate "BET surface area" and "3200 m²/g"; "PXRD pattern matches MOF-5" instead of separate "PXRD pattern" and "MOF-5").
                
                2. Performance results: Combine "performance indicator (metric)" + "its specific data/trend" for MOF applications (e.g., "CO₂ uptake 5.2 mmol/g at 1 bar" instead of separate "CO₂ uptake" and "5.2 mmol/g"; "CO₂/N₂ selectivity 15" instead of separate "selectivity" and "15").

                Guidelines:
                - Extract only explicitly mentioned associated units (no assumptions about unstated relationships)
                - Each entry must be a single logical unit (indicator + its matching data/conclusion)
                - Preserve exact values, units, chemical names and technical terms as in the original text
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
        """Extracted entities from short texts related to MOF experiments"""
        
        methods_and_techniques: List[str] = Field(
            default=[], 
            description="MOF synthesis methods and characterization techniques (e.g., solvothermal synthesis, PXRD, microwave-assisted synthesis, BET surface area analysis, mechanochemical synthesis)"
        )
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with details (concentrations, compositions, amounts) for MOF synthesis (e.g., Zn(NO₃)₂·6H₂O, terephthalic acid (0.1M), acetic acid modulator, DMF solvent, N₂ gas (99.999% purity))"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Laboratory equipment combined with their operational parameters for MOF experiments (e.g., Teflon-lined autoclave at 120°C for 24 hours, Bruker D8 Advance diffractometer with Cu Kα radiation, Micromeritics ASAP 2020 at 77K)"
        )
        
        performance_metrics: List[str] = Field(
            default=[], 
            description="MOF performance indicators with results (e.g., BET surface area 3200 m²/g, CO₂ uptake 5.2 mmol/g at 1 bar, CO₂/N₂ selectivity 15, thermal stability up to 400°C)"
        )

    # Prompt template for comprehensive extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a comprehensive entity extractor for short texts on MOF experiments.
                Extract all relevant entities and classify them into these 4 categories ONLY (reduced categories to avoid omission):
                
                1. Methods and techniques: Combine MOF synthesis methods (e.g., solvothermal, microwave-assisted) and characterization techniques (e.g., PXRD, BET, TGA)
                2. Chemical reagents: All chemical substances with concentrations, compositions, amounts, or ratios if specified for MOF synthesis
                3. Equipment with parameters: Pair lab equipment/apparatus with their directly associated operational parameters (temperature, pressure, voltage, radiation source with units)
                4. Performance metrics: MOF performance indicators, including numerical results when provided (e.g., "BET surface area 3200 m²/g" instead of separate "BET surface area" and "3200 m²/g")

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