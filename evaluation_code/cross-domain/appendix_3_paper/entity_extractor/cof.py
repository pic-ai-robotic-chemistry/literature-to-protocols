def unified_materials_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # 统一类别的实体模型：仅分三大类
    class UnifiedMaterialsEntities(BaseModel):
        """从文本中提取的材料相关实体，统一分为三大类"""
        
        reagents: List[str] = Field(
            default=[], 
            description="All chemical reagents, including monomers (linkers and nodes), catalysts/initiators, solvents, modulators/additives, acid/base regulators, templating agents, surface modifiers, atmosphere gases, washing agents and other chemical substances used in COF synthesis experiments"
        )
        
        experimental_equipment: List[str] = Field(
            default=[], 
            description="All specific experimental equipment, including synthesis equipment (autoclaves, sealed tubes), characterization equipment (PXRD, FTIR, SEM, BET), activation equipment, reaction equipment, product analysis equipment and other equipment directly used in COF synthesis and analysis processes"
        )
        
        common_lab_equipment: List[str] = Field(
            default=[], 
            description="All common laboratory equipment, including drying equipment (ovens, freeze dryers), calcination equipment (muffle furnaces), balances, magnetic stirrers, filtration apparatus, pumps and other general laboratory tools"
        )

    # 提示词专注于提取三大类实体
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in chemical experiments (Covalent Organic Framework synthesis).
                Extract all relevant entities from the text and classify them into three categories ONLY:
                1. Reagents: All chemical substances used in COF experiments, including but not limited to:
                   - Monomers (aldehyde linkers, amine nodes, boronic acids)
                   - Catalysts/initiators (acetic acid, p-toluenesulfonic acid, Lewis acids/bases)
                   - Solvents (dioxane, mesitylene, DMF, THF)
                   - Modulators/additives (water, surfactants, modulators)
                   - Acid/base regulators, templating agents, surface modifiers
                   - Atmosphere gases (N₂, Ar), washing agents (ethanol, acetone), etc.
                  
                2. Experimental Equipment: Specialized equipment directly involved in COF experiment processes:
                   - Synthesis equipment (Teflon-lined autoclaves, sealed tubes, microwave reactors)
                   - Characterization instruments (PXRD, FTIR, solid-state NMR, SEM/TEM, BET analyzer)
                   - Activation equipment (vacuum ovens, tube furnaces)
                   - Reaction equipment, product analysis instruments (HPLC, GC-MS), etc.
                  
                3. Common Lab Equipment: General laboratory tools for routine operations:
                   - Drying equipment (ovens, freeze dryers), calcination equipment (muffle furnaces)
                   - Balances, magnetic stirrers, pumps, filtration apparatus, ultrasonic cleaners, etc.

                Guidelines:
                - Only include entities explicitly mentioned in the text (no assumptions)
                - Each entity should appear in only one most appropriate category
                - Return simple lists of entity names (include key attributes if critical, e.g., "N₂ (99.999% purity)")
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
        """Extracted entities related to COF synthesis methods (simplified 3 categories)"""
        
        synthesis_techniques: List[str] = Field(
            default=[], 
            description="Names of COF synthesis methods/techniques (e.g., solvothermal method, room-temperature synthesis, microwave-assisted synthesis, interfacial synthesis, mechanochemical synthesis)"
        )
        
        chemical_substances: List[str] = Field(
            default=[], 
            description="All chemical reagents with details (concentrations, formulas, amounts) used in COF synthesis (e.g., 1,3,5-triformylbenzene (0.1 mmol), acetic acid (6 M), dioxane/mesitylene mixture (5:1))"
        )
        
        experimental_factors: List[str] = Field(
            default=[], 
            description="Combined equipment with specific conditions for COF synthesis (e.g., Teflon-lined autoclave at 120°C for 72 hours, sealed glass tube under N₂ atmosphere, microwave reactor at 150°C for 30 minutes)"
        )

    # Prompt template for simplified extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in COF synthesis methods.
                Extract all relevant entities from the text and classify them into these 3 categories ONLY:
                1. Synthesis techniques: Names of COF preparation methods/techniques
                2. Chemical substances: All reagents with concentrations/formulas/amounts if specified
                3. Experimental factors: Equipment combined with their specific conditions (temperature, pressure, time, atmosphere with units) as single entities

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
        """Extracted entities from COF synthesis procedures"""
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with quantities used in COF preparation (e.g., 0.10g 1,3,5-triformylbenzene, 10mL dioxane, 0.5mL acetic acid (6M))"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Specific equipment with their associated experimental parameters for COF synthesis (e.g., Teflon-lined autoclave heated at 120°C for 72 hours, analytical balance (0.0001g precision), magnetic stirrer at 600 rpm for 1 hour)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in COF synthesis procedures.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Chemical reagents: All substances with quantities used in COF preparation (monomers, solvents, catalysts, additives)
                2. Equipment with parameters: Specific equipment names (including models/specifications when mentioned) combined with their directly associated experimental parameters (temperature, time, speed, atmosphere, etc.)

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
        """Extracted entities from COF characterization methods"""
        
        characterization_systems: List[str] = Field(
            default=[], 
            description="Complete characterization systems combining technique, instrument, and operational parameters for COF analysis (e.g., PXRD using Bruker D8 Advance diffractometer with Cu Kα radiation at 40kV/40mA over 2θ range 2°-30°, step size 0.02°; BET surface area analysis using Micromeritics ASAP 2020 with N₂ adsorption at 77K, degassing at 120°C for 12h under vacuum)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in COF characterization methods.
                Extract all relevant entities from the text and combine them into a single category:
                1. Characterization systems: Complete descriptions that combine three elements as a single entity:
                   - The characterization technique/method (e.g., PXRD, FTIR, BET, SEM, TEM, TGA)
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
        """Extracted entities from COF activation and application/testing conditions"""
        
        activation_conditions: List[str] = Field(
            default=[], 
            description="COF activation process details including solvents, gases and parameters (e.g., activation at 120°C under vacuum for 12 hours; solvent exchange with acetone for 24 hours; N₂ gas flow at 100 mL/min for thermal activation)"
        )
        
        reaction_conditions: List[str] = Field(
            default=[], 
            description="COF application/testing process details including gases, analytes and parameters (e.g., CO₂ adsorption at 0.15 bar partial pressure, 298K; catalytic reaction at 80°C, 1 bar H₂ pressure; gas separation test with 20 mL/min flow rate, H₂/CO₂ mixture)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in COF evaluation methods (activation and reaction_conditions).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Activation conditions: Complete activation process descriptions for COFs combining solvents/gases and their corresponding operational parameters (temperatures, pressures, times, flow rates, vacuum levels with units)
                2. reaction_conditions: Complete application/testing process descriptions for COFs combining gases/analytes (with compositions if specified) and their corresponding operational parameters (temperatures, pressures, flow rates, concentrations, partial pressures with units)

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must combine relevant solvent/gas/analyte and its associated parameters for the specific process
                - Preserve exact values, units, compositions, and process relationships as in original text
                - Focus exclusively on activation and reaction_conditions (exclude characterization-related parameters)
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all COF evaluation entities from the following text: {question}"
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
        """Extracted entities from COF characterization results and application performance data"""
        
        characterization_results: List[str] = Field(
            default=[], 
            description="Associated pairs of characterization indicators + their data/conclusions for COFs (e.g., BET surface area 1120 m²/g, PXRD pattern matches AA stacking model, pore size 2.1 nm, thermal stability up to 410°C, elemental composition C:68.2 wt%, H:4.9 wt%, N:12.1 wt%)"
        )
        
        performance_results: List[str] = Field(
            default=[], 
            description="Associated pairs of performance indicators + their data/trends for COF applications (e.g., CO₂ uptake 120 cm³/g at 273K, CO₂/N₂ selectivity 35, catalytic conversion 92% after 6h, recyclability 95% after 10 cycles, fluorescence quenching efficiency 85% at 10 ppm)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in COF results (characterization & application performance).
                Extract all relevant entities from the text and classify them into these 2 categories ONLY. Each entry must be a **complete, associated unit** (indicator + corresponding data/conclusion/trend) — do NOT extract isolated indicators or disconnected data.
                
                1. Characterization results: Combine "characterization indicator (property/metric)" + "its specific data/conclusion" for COFs (e.g., "BET surface area 1120 m²/g" instead of separate "BET surface area" and "1120 m²/g"; "PXRD pattern matches AA stacking model" instead of separate "PXRD pattern" and "AA stacking").
                
                2. Performance results: Combine "performance indicator (metric)" + "its specific data/trend" for COF applications (e.g., "CO₂ uptake 120 cm³/g at 273K" instead of separate "CO₂ uptake" and "120 cm³/g"; "CO₂/N₂ selectivity 35" instead of separate "selectivity" and "35").

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
        """Extracted entities from short texts related to COF experiments"""
        
        methods_and_techniques: List[str] = Field(
            default=[], 
            description="COF synthesis methods and characterization techniques (e.g., solvothermal synthesis, PXRD, room-temperature synthesis, BET analysis, microwave-assisted synthesis)"
        )
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with details (concentrations, compositions, amounts) for COF synthesis (e.g., 1,3,5-triformylbenzene (0.1 mmol), acetic acid (6 M), dioxane/mesitylene mixture (5:1 v/v))"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Laboratory equipment combined with their operational parameters for COF experiments (e.g., Teflon-lined autoclave at 120°C for 72 hours, Bruker D8 Advance diffractometer with Cu Kα radiation, Micromeritics ASAP 2020 at 77K)"
        )
        
        performance_metrics: List[str] = Field(
            default=[], 
            description="COF performance indicators with results (e.g., BET surface area 1120 m²/g, CO₂ uptake 120 cm³/g at 273K, CO₂/N₂ selectivity 35, thermal stability up to 410°C)"
        )

    # Prompt template for comprehensive extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a comprehensive entity extractor for short texts on COF experiments.
                Extract all relevant entities and classify them into these 4 categories ONLY (reduced categories to avoid omission):
                
                1. Methods and techniques: Combine COF synthesis methods (e.g., solvothermal, room-temperature) and characterization techniques (e.g., PXRD, BET)
                2. Chemical reagents: All chemical substances with concentrations, compositions, amounts, or ratios if specified for COF synthesis
                3. Equipment with parameters: Pair lab equipment/apparatus with their directly associated operational parameters (temperature, pressure, voltage, radiation source with units)
                4. Performance metrics: COF performance indicators, including numerical results when provided (e.g., "BET surface area 1120 m²/g" instead of separate "BET surface area" and "1120 m²/g")

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

