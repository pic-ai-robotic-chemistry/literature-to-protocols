def unified_materials_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Unified entity model with three core categories
    class UnifiedMaterialsEntities(BaseModel):
        """Extracted material-related entities, categorized into three unified classes"""
        
        reagents: List[str] = Field(
            default=[], 
            description="All chemical substances and compositional elements used in catalyst/electrode materials, including nominal chemical formulas, dopants, solid solutions, defect types, and other compositional entities"
        )
        
        experimental_equipment: List[str] = Field(
            default=[], 
            description="All characterization instruments and analytical equipment used to determine material properties, including XRD for crystal structure, UV-Vis/DRS for band gap, SEM/TEM for morphology, XPS for chemical composition, BET for surface area, and other material characterization tools"
        )
        
        common_lab_equipment: List[str] = Field(
            default=[], 
            description="All general laboratory apparatus and synthesis equipment used in material preparation, including reactors, furnaces, substrate materials, electrodes, and other experimental setup components"
        )

    # Prompt focused on extracting three categories of entities
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in electrochemical materials (Overall Water Splitting catalysts/electrodes).
                Extract all relevant entities from the text and classify them into three categories ONLY:
                1. Reagents: All chemical substances and compositional entities, including but not limited to:
                   - Nominal chemical formulas (e.g., SrTiO₃, Co-doped FeOOH)
                   - Dopants, solid solutions, defect concentrations
                   - Substitution elements, engineered vacancies, compositional ratios
                  
                2. Experimental Equipment: Specialized characterization instruments directly used to determine material properties:
                   - Crystal structure analysis equipment (XRD, TEM with lattice analysis)
                   - Electronic property instruments (UV-Vis/DRS for band gap, Mott-Schottky for band positions)
                   - Morphological analysis tools (SEM, TEM, HRTEM)
                   - Surface and chemical analysis (XPS, BET surface area analyzer)
                  
                3. Common Lab Equipment: General laboratory apparatus for material synthesis and testing:
                   - Synthesis reactors, furnaces, deposition systems
                   - Electrode substrates (FTO, ITO, carbon paper, nickel foam)
                   - Measurement cells, reaction vessels, sample preparation tools

                Guidelines:
                - Only include entities explicitly mentioned in the text (no assumptions)
                - Each entity should appear in only one most appropriate category
                - Return simple lists of entity names (include key attributes if critical, e.g., "SrTiO₃ (perovskite structure)", "5 at.% Ni doping")
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

    # Create extraction chain
    unified_entities_chain = prompt | llm.with_structured_output(UnifiedMaterialsEntities)
    return unified_entities_chain
def synthesis_methods_entities_extractor(llm):
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import List
    from langchain_core.prompts import ChatPromptTemplate

    # Simplified entity model with 3 core categories
    class SynthesisMethodEntities(BaseModel):
        """Extracted entities related to Overall Water Splitting catalyst/electrode synthesis and processing methods (simplified 3 categories)"""
        
        synthesis_techniques: List[str] = Field(
            default=[], 
            description="Names of catalyst/electrode preparation methods/techniques (e.g., sol-gel synthesis, hydrothermal method, incipient wetness impregnation, photodeposition, calcination)"
        )
        
        chemical_substances: List[str] = Field(
            default=[], 
            description="All chemical precursors and reagents with details (concentrations, formulas, amounts) (e.g., Sr(NO₃)₂, Ti(OiPr)₄, 0.1 M Co(NO₃)₂·6H₂O, 2 wt.% CoOₓ loading)"
        )
        
        experimental_factors: List[str] = Field(
            default=[], 
            description="Combined equipment with specific processing conditions (e.g., muffle furnace at 800°C for 4 h in static air, tube furnace under 10% H₂/Ar flow at 500°C, photodeposition under 300 W Xe lamp for 30 minutes)"
        )

    # Prompt template for simplified extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Overall Water Splitting catalyst/electrode synthesis and post-processing methods.
                Extract all relevant entities from the text and classify them into these 3 categories ONLY:
                1. Synthesis techniques: Names of preparation methods/techniques including synthesis, post-treatments, and functionalization
                2. Chemical substances: All chemical precursors and reagents with concentrations/formulas/amounts/loadings if specified
                3. Experimental factors: Equipment combined with their specific processing conditions (temperature, pressure, time, atmosphere, flow rate with units) as single entities

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
        """Extracted entities from Overall Water Splitting catalyst/electrode characterization methods and settings"""
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Specific characterization instruments with models and specifications for OWS materials analysis (e.g., Bruker D8 ADVANCE diffractometer, Shimadzu UV-3600i Plus spectrophotometer with ISR-603 integrating sphere, Horiba LabRAM HR Raman system)"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Characterization measurement parameters and conditions for OWS materials analysis (e.g., Cu Kα radiation at 40 kV/40 mA, 2θ range 10°-80° with 0.02° step, BaSO₄ reflectance standard, ultra-high vacuum < 5×10⁻⁹ mbar)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Overall Water Splitting catalyst/electrode characterization methods and settings.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Characterization instruments: Specific instruments with models/specifications for OWS materials analysis
                2. Measurement parameters: Characterization parameters and conditions including instrument settings, test parameters, calibration standards, and data analysis methods

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entity belongs to only one most appropriate category
                - Preserve exact values, units, technical specifications, and chemical names as in original text
                - For instruments, use specific names with models rather than general types (e.g., "Bruker D8 ADVANCE diffractometer" instead of "XRD")
                - For parameters, include all associated conditions and settings as a single entity
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify entities from the following characterization methods text: {question}"
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
        """Extracted entities from Overall Water Splitting photocatalyst system architecture"""
        
        characterization_systems: List[str] = Field(
            default=[], 
            description="Complete OWS photocatalyst system descriptions combining configuration, components, and operational parameters (e.g., Z-scheme system with SrTiO₃:Rh as HEP, BiVO₄ as OEP, Fe³⁺/Fe²⁺ (1.0 mM) mediator; One-step system using single LaTiO₂N photocatalyst; Operational design with visible light up to 520 nm and H₂/O₂ separation by Nafion 117 membrane)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Overall Water Splitting photocatalyst system architecture.
                Extract all relevant entities from the text and combine them into a single category:
                1. Characterization systems: Complete descriptions that combine three elements as a single entity:
                   - The OWS system configuration/mode (e.g., One-step, Z-scheme)
                   - The specific components with their assigned functions (e.g., HEP, OEP, mediator)
                   - All associated operational parameters with units that belong to this system configuration

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must be a complete system combining configuration + components + its parameters
                - Preserve exact terms, units, chemical names, and technical specifications as in original text
                - Maintain the natural association between components and their specific functions in the system
                - Return simple lists without explanations, formatting, or additional information
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all photocatalyst system architecture entities from the following text: {question}"
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
        """Extracted entities from Overall Water Splitting testing system configuration"""
        
        activation_conditions: List[str] = Field(
            default=[], 
            description="Complete illumination system descriptions combining light source, intensity, and measurement details for OWS testing (e.g., 300 W Xe lamp with AM 1.5G filter at 100 mW cm⁻² measured by calibrated silicon photodiode, incident area 12.6 cm²; solar simulator with 420 nm cutoff filter)"
        )
        
        reaction_conditions: List[str] = Field(
            default=[], 
            description="Complete reactor and testing system descriptions combining reactor type, gas handling, and reaction medium details for OWS testing (e.g., closed-circulation Pyrex glass reactor with 370 mL volume at 25°C, gas analysis by Agilent 7890B GC with Molecular Sieve 5Å column, reaction medium: 0.05 M Na₂SO₄ in deionized water without sacrificial agents)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Overall Water Splitting testing system configuration.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY:
                1. Illumination conditions: Complete illumination system descriptions combining light source, intensity measurement, and spectral parameters for OWS testing
                2. Reactor system conditions: Complete reactor and testing system descriptions combining reactor design, gas handling protocols, and reaction medium details for OWS testing

                Guidelines:
                - Extract only entities explicitly mentioned in the text (no assumptions)
                - Each entry must combine all relevant parameters for the specific system component
                - Preserve exact values, units, instrument models, and technical specifications as in original text
                - Focus exclusively on testing system configuration (exclude material characterization-related parameters)
                - Return simple lists without explanations or formatting
                - Do not output duplicate entities.
                """,
            ),
            (
                "human",
                "Extract and classify all OWS testing system configuration entities from the following text: {question}"
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
        """Extracted entities from Overall Water Splitting performance evaluation and validation results"""
        
        characterization_results: List[str] = Field(
            default=[], 
            description="Associated pairs of characterization indicators + their data/conclusions for OWS performance evaluation (e.g., H₂:O₂ stoichiometric ratio approximately 1.98:1, isotope labeling confirms O₂ originates from H₂¹⁸O, XPS shows no shift in Ni 2p peak after reaction, ICP-MS shows Sr/Ti concentrations below 0.1 ppb detection limit)"
        )
        
        performance_results: List[str] = Field(
            default=[], 
            description="Associated pairs of performance indicators + their data/trends for OWS system (e.g., H₂ evolution rate 45.2 ± 2.1 µmol h⁻¹ g⁻¹ under AM 1.5G illumination, AQY 8.7% at 365 nm, STH efficiency 0.5%, continuous operation maintains 80% activity for 20 hours, dark control produces no gas evolution)"
        )

    # Prompt template for extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an entity extractor specializing in Overall Water Splitting performance evaluation and validation results.
                Extract all relevant entities from the text and classify them into these 2 categories ONLY. Each entry must be a **complete, associated unit** (indicator + corresponding data/conclusion/trend) — do NOT extract isolated indicators or disconnected data.
                
                1. Characterization results: Combine "characterization indicator (property/metric)" + "its specific data/conclusion" for OWS performance validation (e.g., "H₂:O₂ stoichiometric ratio approximately 1.98:1" instead of separate "H₂:O₂ ratio" and "1.98:1"; "isotope labeling confirms O₂ originates from H₂¹⁸O" instead of separate "isotope labeling" and "O₂ from water").
                
                2. Performance results: Combine "performance indicator (metric)" + "its specific data/trend" for OWS system (e.g., "H₂ evolution rate 45.2 ± 2.1 µmol h⁻¹ g⁻¹ under AM 1.5G illumination" instead of separate "H₂ evolution rate" and "45.2 µmol h⁻¹ g⁻¹"; "AQY 8.7% at 365 nm" instead of separate "AQY" and "8.7%").

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
        """Extracted entities from short texts related to Overall Water Splitting experiments"""
        
        methods_and_techniques: List[str] = Field(
            default=[], 
            description="OWS synthesis methods, characterization techniques, and system architectures (e.g., sol-gel synthesis, XRD characterization, Z-scheme system configuration, Mott-Schottky analysis, isotope labeling validation)"
        )
        
        chemical_reagents: List[str] = Field(
            default=[], 
            description="Chemical substances with details (concentrations, compositions, functions) for OWS (e.g., Sr(NO₃)₂ precursor, Ni dopant (5 at.%), Fe³⁺/Fe²⁺ redox mediator (1.0 mM), 0.05 M Na₂SO₄ electrolyte, no sacrificial agents)"
        )
        
        equipment_with_parameters: List[str] = Field(
            default=[], 
            description="Laboratory equipment combined with their operational parameters for OWS (e.g., 300 W Xe lamp with AM 1.5G filter at 100 mW cm⁻², closed-circulation Pyrex reactor (370 mL) at 25°C, Agilent 7890B GC with Molecular Sieve 5Å column, Bruker D8 ADVANCE diffractometer with Cu Kα radiation)"
        )
        
        performance_metrics: List[str] = Field(
            default=[], 
            description="OWS performance indicators with results (e.g., H₂ evolution rate 45.2 µmol h⁻¹ g⁻¹ under AM 1.5G, AQY 8.7% at 365 nm, STH efficiency 0.5%, H₂:O₂ stoichiometric ratio 1.98:1, 80% activity retention after 20 hours)"
        )

    # Prompt template for comprehensive extraction
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a comprehensive entity extractor for short texts on Overall Water Splitting experiments.
                Extract all relevant entities and classify them into these 4 categories ONLY (reduced categories to avoid omission):
                
                1. Methods and techniques: Combine OWS synthesis methods, characterization techniques, and system architectures
                2. Chemical reagents: All chemical substances with concentrations, compositions, functions, or ratios if specified for OWS
                3. Equipment with parameters: Pair lab equipment/apparatus with their directly associated operational parameters (temperature, pressure, voltage, intensity, models with units)
                4. Performance metrics: OWS performance indicators, including numerical results when provided (e.g., "H₂ evolution rate 45.2 µmol h⁻¹ g⁻¹" instead of separate "H₂ evolution rate" and "45.2 µmol h⁻¹ g⁻¹")

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