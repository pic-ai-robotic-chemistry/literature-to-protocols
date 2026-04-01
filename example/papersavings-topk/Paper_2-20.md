# Efficient conversion of syngas to linear α-olefins by phase-pure χ-Fe5C2

## 1. Materials

### 1.1 Reagents

#### 1.1.1 Metal Precursors
- **Raney Iron Precursor**: Fe–Al alloy (50:50 wt%), [Purity not specified], Sigma‑Aldrich, Used as the active metal source that, after selective aluminum leaching, is transformed into a porous iron phase for in situ carburization to form phase‑pure χ‑Fe₅C₂.

#### 1.1.2 Additive/Promoter Precursors
- **Promoter Precursors**:
  - **Manganese Nitrate**: Mn(NO₃)₂, [Purity not specified], [Supplier details not provided], 0.5–12.5 wt%, Used as a promoter to enhance catalyst performance and suppress carbon deposition.
  - **Potassium Nitrate**: KNO₃, [Purity not specified], [Supplier details not provided], ≈1 wt%, Used as a promoter to improve catalyst performance.

#### 1.1.3 Solvents
- **Deionized Water**: H₂O, [Purity not specified], [Supplier details not provided], Used for repeated washing of the catalyst precursor to remove residual KOH.
- **Ethanol**: C₂H₅OH, AR grade, Sinopharm Chemical Reagent, Used for washing and thorough cleaning of the precursor.

#### 1.1.4 Base/Acid Regulators
- **Potassium Hydroxide Solution**: KOH (8 mol·L⁻¹), [Purity not specified], [Supplier details not provided], Heated to 70°C under stirring during catalyst preparation to dissolve aluminum from the Fe–Al alloy precursor.

#### 1.1.5 Passivation Atmosphere Gases
- **Passivation Gas**: 1% O₂ in He, [Purity not specified], [Operational details: Room temperature, 20 hours; flow rate not specified], Used to stabilize the catalyst surface prior to carburization.

#### 1.1.6 Synthesis Gas Environment Gases
- **Carburization Syngas**: H₂/CO/He (100/3.2/21.8), [Purity not specified], [Supplier details not provided], Employed in a fixed‑bed reactor at 350°C (temperature ramp rate of 0.5°C·min⁻¹ with a 6‑hour dwell), Used for in situ carburization to form phase‑pure χ‑Fe₅C₂.
- **ETEM Gas Environment**: H₂/CO (ratio 30), [Purity not specified], [Operational details: 1,200 Pa, 350°C], Used during environmental TEM experiments to monitor the rapid formation of χ‑Fe₅C₂.

### 1.2 Specific Experimental Equipment

#### Synthesis Equipment
- Laboratory reactor – Stainless-steel tubular fixed-bed reactor (Ext. diameter: 14.5 mm; Int. diameter: 9 mm; Length: 305 mm; Internal volume: 20 ml) used for in situ carburization.
- Reagent dissolution vessel – Flask with stirring and heating capability for dissolving the aluminum from the iron–aluminum alloy in an 8 mol L⁻¹ KOH solution.
- Inert atmosphere enclosure – Glove box designed to maintain an argon flow during drying of the Raney iron precursor.
- Drying apparatus – Vacuum oven used for drying the impregnated catalyst precursor at room temperature (model details not specified).

#### Characterization Equipment
- X‑ray diffractometer – Rigaku D/max-2600/PC instrument equipped with a D/teX ultrahigh-speed detector for in situ XRD and Rietveld refinement.
- Transmission electron microscope – Aberration-corrected FEI Titan ETEM G2 operating at 300 kV for environmental TEM imaging.
- Mössbauer spectrometer – In situ high-pressure cell with a sinusoidal velocity spectrometer and 57Co(Rh) source for 57Fe Mössbauer spectroscopy.
- Computational tool – Vienna Ab initio Simulation Package (VASP) for density functional theory calculations.
- Simulation software – MKMCXX software suite for performing microkinetic simulations.

#### Activation Equipment
- Flow system for passivation – Equipment for introducing 1% O₂ in helium to passivate the catalyst precursor under controlled conditions.
- Temperature control unit – Integrated with the reactor setup to precisely manage the temperature ramp (0.1°C/min up to 350°C).

#### Reaction Equipment
- Fixed-bed reactor – Stainless-steel tubular reactor (as detailed above) used for handling the syngas mixture during carburization.
- Stirred tank reactor – Continuously stirred tank reactor for operating under Fischer–Tropsch reaction conditions.

#### Product Analysis Equipment
- Gas analysis instrument – A gas chromatograph (GC) for evaluating product gas composition following reaction (generic description).

#### Other Specific Equipment
- Standard laboratory tools – Magnetic stirrers, pumps, and balance scales employed for reagent handling and process monitoring during catalyst synthesis.

### 1.3 Common Laboratory Equipment

In this section, various types of common laboratory equipment play a supportive role in ensuring that the synthesis, characterization, and evaluation processes are both precise and reproducible. Although not directly involved in catalyst synthesis, these tools facilitate essential operations such as reagent handling, moisture removal, and maintaining controlled experimental conditions.

#### **Drying Equipment**
- Vacuum Oven  
  The vacuum oven is key for drying materials—especially for drying impregnated catalysts prior to further activation steps. Operating at room temperature for approximately 12 hours under reduced pressure, it effectively removes residual moisture, ensuring anhydrous conditions necessary for high-quality catalyst performance.
- Glove Box  
  A glove box is employed to create an inert atmosphere during the drying process, particularly when drying under an argon flow. This equipment minimizes exposure to oxygen and moisture, safeguarding sensitive samples from possible contamination or oxidation.

#### **Calcination Equipment**
- Temperature-Controlled Reactor or Furnace  
  For procedures requiring controlled heating, such as the in situ carburization where a precise temperature ramp to 350°C is implemented, a temperature-controlled reactor or furnace is used. While not explicitly described as calcination equipment in every step, this equipment’s functionality aligns with calcination needs by enabling the gradual thermal treatment necessary for catalyst activation and phase transformation.

#### **Other Common Equipment**
- Analytical Balance  
  Accurate weighing of the Raney iron precursor, promoters, and other reagents is fundamental to reproducibility. An analytical balance ensures that measured quantities are precise, supporting consistent experimental outcomes.
- Magnetic Stirrer  
  During processes like wet impregnation for catalyst promotion (with reagents such as Mn(NO₃)₂), a magnetic stirrer facilitates thorough and uniform mixing.
- Pumps and Flow Controllers  
  These are essential for managing reagent flow as well as gas delivery during both synthesis and reaction phases.
- Pipettes or Graduated Cylinders  
  These tools assist in the precise measurement and transfer of liquid reagents, contributing further to the overall reliability and repeatability of the experimental procedure.

Together, this collection of equipment not only supports the practical aspects of catalyst synthesis and characterization but also upholds the rigorous conditions required for efficient experimental outcomes in the conversion of syngas to linear α‑olefins.

## 2. Synthesis Methods

### Extraction of Detailed Preparation and Post‑processing Steps

The synthesis of Mn-χ-Fe₅C₂ catalysts is executed through a well‐defined sequence that guarantees reproducibility. The procedure comprises the following steps:

#### • Precursor Preparation / Mixing
1. An iron–aluminum alloy powder is added to an 8 mol L⁻¹ KOH solution in a reaction flask. The mixture is heated to 70°C under continuous stirring to dissolve aluminum via leaching.  
   • Reagent: Iron–aluminum alloy (50:50 by weight)  
   • Reaction Conditions: 70°C, in 8 mol L⁻¹ KOH  
   • Washing: The resultant mixture is washed ten times with deionized water followed by seven washes with ethanol, ensuring removal of K⁺ and AlO₂⁻ ions before drying.
   
#### • Precipitation–Deposition and Promoter Incorporation
2. For promoted catalysts, following precursor mixing, a wet impregnation step is performed:
   • Promoter: Mn(NO₃)₂ is introduced to achieve 0.5–12.5 wt% Mn.  
   • Process: The Mn(NO₃)₂ solution is added dropwise under stirring, ensuring uniform deposition.  
   • The incorporation method guarantees thorough contact between the promoter and the precursor material.

#### • Drying
3. The washed (and, if applicable, promoter‐impregnated) precursor is dried:
   • For unpromoted samples: Drying is performed under a continuous argon flow to prevent oxidation.  
   • For promoted samples: The catalyst is dried in a vacuum oven at room temperature for 12 hours, ensuring complete solvent removal and uniform promoter distribution.

#### • Post‑processing: Passivation and Carburization
4. The dried precursor undergoes passivation by exposure to 1% O₂ in helium at room temperature for 20 hours.  
   • This step forms a protective oxide layer, stabilizing the Raney iron phase.
5. Carburization is conducted in a stainless‐steel tubular fixed‐bed reactor using a syngas mixture (H₂/CO/He = 100/3.2/21.8) at ambient pressure:
   • Temperature Ramp: 0.1°C min⁻¹ up to 350°C  
   • Dwell Time: 6 hours at 350°C  
   • In environmental TEM experiments, a H₂/CO ratio of 30 at 1,200 Pa and 350°C leads to rapid formation (within <0.5 h) of phase‐pure χ‑Fe₅C₂.

This structured sequence—from precise precursor treatment and promoter impregnation to controlled drying, passivation, and carburization—ensures accurate, reproducible synthesis of high‐performance Fischer–Tropsch catalysts while enabling direct comparisons to unpromoted χ‑Fe₅C₂ materials.

## 3. Synthesis Procedures

### 3.1 Reagent Preparation

In this section, the catalyst‐specific preparation routines are organized into three main steps: Weighing, Liquid Transfer, and Mixing. The following entries reflect the procedures described for the promoted Mn‑χ‑Fe₅C₂ catalyst in comparison with the unpromoted χ‑Fe₅C₂ system, with all details provided in the article printed below. Note that certain quantitative specifics (exact masses, volumes, stirring speeds, and precise equipment) are not explicitly reported in the source.

#### 3.1.1 Weighing

##### 3.1.1.1 Mn‑χ‑Fe₅C₂  
- **Raney Iron Precursor (Fe–Al Alloy)**: Weighed an appropriate amount using an analytical balance to prepare the base material for carburization.  
- **Mn(NO₃)₂**: Weighed to achieve a promoter loading within 0.5–12.5 wt% by wet impregnation (exact mass and balance precision not specified).

##### 3.1.1.2 χ‑Fe₅C₂ (Unpromoted)  
- **Raney Iron Precursor (Fe–Al Alloy)**: Weighed an appropriate amount using an analytical balance, forming the sole precursor for the unpromoted catalyst.

#### 3.1.2 Liquid Transfer

##### 3.1.2.1 Mn‑χ‑Fe₅C₂  
- **Deionized Water**: Transferred during the washing stage of the precursor using standard laboratory equipment (exact volume and method not provided).  
- **Ethanol**: Transferred for the washing process to remove residuals with typical apparatus (specific volume and transfer method not detailed).  
- **Mn(NO₃)₂ Solution**: Delivered via wet impregnation to incorporate the manganese promoter (exact transfer parameters are not specified).

##### 3.1.2.2 χ‑Fe₅C₂ (Unpromoted)  
- **Deionized Water**: Transferred for washing the Raney iron precursor, ensuring cleanliness of the material (transfer details remain unspecified).  
- **Ethanol**: Transferred for the final cleaning step with standard laboratory practice (exact details not provided).

#### 3.1.3 Mixing

##### 3.1.3.1 Mn‑χ‑Fe₅C₂  
- **Impregnation Mixture**: Mixed by magnetic stirring to ensure proper distribution of the manganese promoter; stirring conditions (speed and duration) are not explicitly stated.  
- **Final Suspension**: Dried in an argon flow after mixing, following the protocol for catalyst activation (additional conditions such as temperature are not detailed).

##### 3.1.3.2 χ‑Fe₅C₂ (Unpromoted)  
- **Precursor Washing Suspension**: Mixed under routine laboratory conditions by stirring for homogenization; specific parameters are not provided.  
- **Post‑Washing Mixture**: Dried under an inert atmosphere to complete the preparation process (detailed environmental conditions are not described).

### 3.2 Detailed synthesis process

#### Catalyst Preparation [1]: Mn–χ–Fe₅C₂

##### Step 1: Precursor Preparation
- **Reagents**:  
  • Iron–aluminum alloy powder (50:50 by weight)  
  • 8 mol L⁻¹ KOH solution (adequate volume for complete aluminum leaching)  
  • Deionized water and ethanol for washing  
- **Conditions**:  
  • Reaction temperature: 70°C under continuous stirring  
- **Process**:  
  • Add the iron–aluminum alloy powder into the 8 mol L⁻¹ KOH solution while stirring at 70°C to selectively dissolve aluminum, thereby forming a porous iron structure.  
  • Once aluminum dissolution is complete, separate the solid precursor.  
  • Wash the precursor sequentially: ten cycles with deionized water followed by seven cycles with ethanol to thoroughly remove leached aluminum species.  
  • Dry the washed iron precursor in an argon flow at room temperature for 6 hours.  
- **Key Steps**:  
  • Strict control of pH and temperature during leaching is critical for reproducible porosity.

##### Step 2: Catalyst Assembly (Promoter Impregnation)
- **Reagents**:  
  • Mn(NO₃)₂ solution (providing 0.5–12.5 wt% Mn relative to iron)  
- **Conditions**:  
  • Ambient conditions during impregnation; subsequent drying in a vacuum oven at room temperature for 12 hours  
- **Process**:  
  • Impregnate the dried Raney iron precursor with the Mn(NO₃)₂ solution, adding it dropwise under vigorous stirring to ensure a homogeneous dispersion of the promoter.  
  • After complete mixing, dry the catalyst in a vacuum oven at room temperature for 12 hours to remove residual moisture.
- **Key Steps**:  
  • Uniform distribution of manganese is essential for enhanced catalytic performance.

##### Step 3: Purification, Drying & Activation
- **Passivation**:  
  • Expose the impregnated catalyst to 1% O₂ in helium at room temperature for 20 hours to form a controlled surface oxide layer, preventing over-oxidation.
- **Carburization**:  
  • **Reagents**: Syngas (H₂/CO/He = 100/3.2/21.8)  
  • **Conditions**: Temperature ramp at 0.1°C min⁻¹ up to 350°C; dwell for 6 hours in a stainless‐steel tubular fixed-bed reactor  
  • **Process**:  
    - Initiate carburization by introducing the syngas while gradually increasing the temperature at the specified rate until reaching 350°C.  
    - Maintain the reactor at 350°C for 6 hours to achieve the formation of phase‐pure χ–Fe₅C₂.

*For unpromoted χ–Fe₅C₂, omit the promoter impregnation and follow the same protocol from precursor preparation through activation to ensure direct catalyst formation.*

## 4. Characterization Methods

### 4.1 In Situ X-ray Diffraction (XRD)
- **Operational Description**: In situ XRD was applied to determine the crystalline phase and confirm the formation of phase-pure χ‑Fe5C2 during the carburization process. The catalyst sample is monitored in real-time, with the collected diffraction patterns being refined using Rietveld analysis to ascertain lattice parameters and phase purity.
- **Instruments and Models**: The analysis was performed on a Rigaku D/max‑2600/PC system equipped with a D/teX ultrahigh‑speed detector and scintillation counter, utilizing a copper rotating anode.
- **Characterization Conditions**: Measurements were carried out under a syngas environment (H₂/CO/He = 100/3.2/21.8) at ambient pressure. A controlled heating rate of 0.5°C/min was implemented to ensure accurate phase transition detection.
- **Test Parameters**: Although specific step sizes or scanning rates were not detailed, the 2θ scan range and instrument calibration were optimized for precise phase identification.
- **Key Notes**: Strict sample alignment and pre-calibration of the instrument are critical. The Rietveld refinement results were compared with literature data to validate phase purity.

### 4.2 Environmental Transmission Electron Microscopy (ETEM)
- **Operational Description**: ETEM was employed to observe the microstructural evolution of the catalyst during its carburization. High-resolution imaging combined with inverse fast Fourier transform (IFFT) analysis provided detailed insight into the location and distribution of the χ‑Fe5C2 phase.
- **Instruments and Models**: An aberration‑corrected FEI Titan ETEM G2 instrument was used.
- **Characterization Conditions**: Experiments were performed under a gas composition of H₂/CO = 30 at a pressure of 1,200 Pa and a temperature of 350°C.
- **Test Parameters**: A pretreatment at 320°C for 1 hour preceded a rapid temperature increase to 350°C within about 0.5 hours, allowing real‑time structural monitoring.
- **Key Notes**: Temperature control and precise regulation of the gas environment are essential for reliable IFFT imaging and phase transition observation.

### 4.3 In Situ 57Fe Mössbauer Spectroscopy
- **Operational Description**: This technique was utilized to verify the exclusive formation and stability of phase‑pure χ‑Fe5C2 under in situ conditions. Sample and source are maintained at the same temperature to ensure measurement consistency.
- **Instruments and Models**: A sinusoidal velocity spectrometer equipped with a 57Co(Rh) source was employed.
- **Characterization Conditions**: Measurements are conducted at –153°C under strictly controlled thermal conditions.
- **Test Parameters**: The method delivers reproducible spectral data with uncertainties of ±0.02 mm/s for both the isomer shift and quadrupole splitting, ±0.03 mm/s for the line width, and ±0.1 T for the hyperfine field.
- **Key Notes**: Maintaining a uniform temperature for both the sample and source is critical, and the spectral fitting supports the reliability of phase identification when compared to established standards.

## 5. Catalytic Evaluation Methods

### 5.1 Activation

#### 5.1.1 Activation Temperature  
- **Definition:** The activation temperature is critical for initiating reduction and carburization of the catalyst precursor, driving the formation of phase‐pure χ‑Fe₅C₂.  
- **Experimental Conditions:** The catalyst precursor is heated using a controlled, linear temperature ramp. The temperature is increased at a rate of approximately 0.5°C per minute (with an alternative instance at 1°C per minute) until reaching 350°C.  
- **Observations:** This controlled heating ensures gradual conversion, minimizes the risk of forming unwanted phases, and enhances metal dispersion while reducing the possibility of sintering.

#### 5.1.2 Activation Pressure  
- **Definition:** Maintaining an appropriate pressure during activation ensures effective gas–solid contact and influences the reduction kinetics.  
- **Experimental Conditions:** The activation process is performed at ambient pressure.  
- **Observations:** Ambient pressure supports a stable transformation environment during in situ carburization, helping to avoid the formation of undesired iron oxides.

#### 5.1.3 Activation Gas Composition  
- **Definition:** The specific gas mixture provides both a reducing and carburizing atmosphere, which is essential for transforming the Raney iron precursor into the active χ‑Fe₅C₂ phase.  
- **Experimental Conditions:** A syngas mixture consisting of H₂, CO, and He in the exact ratio of 100/3.2/21.8 is used during the activation step.  
- **Observations:** The hydrogen facilitates the reduction of any residual oxides, while the CO supplies the necessary carbon to drive carburization. Helium acts as an inert diluent, moderating the reaction kinetics and ensuring uniform activation.

#### 5.1.4 Activation Space-Time Velocity  
- **Definition:** The space-time velocity controls the exposure of catalyst particles to the reactive gas mixture, ensuring consistent heat and mass transfer throughout the catalyst bed.  
- **Experimental Conditions:** The syngas flow rate is adjusted relative to the catalyst mass, with reported values around 60,000–75,000 mL/(g_cat·h).  
- **Observations:** Such precise control contributes to a homogeneous activation, thereby preventing over-reduction and excessive local heating.

#### 5.1.5 Activation Time  
- **Definition:** Sufficient dwell time at the target temperature allows complete carburization and ensures full conversion of the precursor to phase‐pure χ‑Fe₅C₂.  
- **Experimental Conditions:** A dwell time of 6 hours is maintained at 350°C during the in situ carburization step.  
- **Observations:** This duration is essential for achieving the desired structural transformation and catalytic performance without inducing sintering.

### 5.2 Reaction

The Fischer–Tropsch catalytic evaluation was systematically performed under defined reaction parameters to ensure reproducibility and clarity. Each parameter was carefully monitored to understand its impact on syngas activation and final product distribution.

#### 5.2.1 Reaction Temperature
- **Definition:** The reaction temperature is a critical parameter that governs syngas activation and the kinetics of the Fischer–Tropsch process. An increase in temperature leads to an exponential rise in CO conversion and hydrocarbon formation rates.
- **Experimental Conditions:** The tests were conducted over a temperature range of 250–320 °C.
- **Observations:** Within this range, the Mn–χ‑Fe₅C₂ catalyst maintained consistent activity, exhibiting stability for over 200 hours. The temperature also contributed to favorable selectivity towards lower olefins while limiting CO₂ production.

#### 5.2.2 Reaction Pressure
- **Definition:** Reaction pressure affects the concentration of syngas in the reactor, thereby influencing both conversion and product selectivity.
- **Experimental Conditions:** The system pressure was maintained between 2.3 and 3.0 MPa, with performance evaluations often focusing on an optimal pressure near 2.5 MPa.
- **Observations:** Operating at these pressures enhanced CO conversion and promoted higher carbon-based selectivity. However, increased pressure was also noted to potentially accelerate carbon deposition, emphasizing the need for careful control.

#### 5.2.3 Reaction H₂/CO Ratio
- **Definition:** The H₂/CO ratio is crucial for balancing the formation of various hydrocarbons. It directly influences the ratio of methane, lower olefins, and other products.
- **Experimental Conditions:** The catalyst was evaluated using a range of H₂/CO ratios. Specific tests reported ratios of 2.0 and 2.5, while an optimized ratio of 1.5 was shown to provide an excellent balance between CO conversion and reduced CO₂ selectivity.
- **Observations:** Variations in the H₂/CO ratio substantially affected product distribution. A ratio of 1.5 was particularly effective for the Mn–χ‑Fe₅C₂ catalyst, emphasizing its role in achieving high carbon efficiency and selectivity towards valuable lower olefins.

#### 5.2.4 Reaction Space-Time Velocity
- **Definition:** Space-time velocity (STV) relates the flow rate of reactants to the catalyst mass, impacting the residence time and overall conversion.
- **Experimental Conditions:** The reported gas hourly space velocity (GHSV) for the Mn–χ‑Fe₅C₂ catalyst was 60,000 mL/(g_cat·h).
- **Observations:** This high STV enabled efficient reactant processing with minimal catalyst deactivation, supporting steady CO conversion and stable long-term performance.

This detailed organization of reactor conditions ensures that the synthesis and catalytic evaluation are fully replicable, aligning closely with the experimental protocols outlined in the article "Efficient conversion of syngas to linear α-olefins by phase-pure χ-Fe₅C₂."

## 6 Results


### 6.1 Characterization Results

#### 6.1.1 Crystal Phase and Structure
- **Description:** The crystal phase composition and structural evolution of the Fischer–Tropsch catalysts were investigated using in situ X-ray diffraction (XRD) with Rietveld refinement, complemented by environmental transmission electron microscopy (ETEM) and in situ ^57Fe Mössbauer spectroscopy.
- **Findings:** In situ XRD patterns demonstrate that the transformation from the Raney iron precursor to phase-pure χ-Fe₅C₂ (Hägg carbide) initiates at 300°C and completes after 6 hours at 350°C under syngas flow (H₂/CO/He = 100/3.2/21.8). Rietveld refinement confirms the exclusive presence of χ-Fe₅C₂, with lattice parameters matching literature values. No competing iron oxide or metallic iron phases are detected. ETEM and high-resolution TEM (HRTEM) images further reveal the nucleation and growth of χ-Fe₅C₂ grains, with the final phase imaged along the (311) direction and a characteristic lattice spacing of approximately 2.7 Å. In situ ^57Fe Mössbauer spectroscopy (at –153°C) confirms that χ-Fe₅C₂ is the only iron phase present after carburization and during Fischer–Tropsch operation, both for unpromoted and Mn-promoted catalysts.
- **Observations:** The one-step in situ carburization reliably yields phase-pure χ-Fe₅C₂, which is maintained under reaction conditions. The absence of other iron phases is critical for suppressing side reactions and achieving high selectivity.

#### 6.1.2 Morphology and Microstructure
- **Description:** Catalyst morphology and microstructural evolution were characterized by ETEM and HRTEM, with filtered inverse fast Fourier transform (IFFT) imaging used to visualize lattice features and phase distribution.
- **Findings:** The passivated Raney iron precursor consists of crystallized iron particles surrounded by an amorphous oxide layer. Upon exposure to syngas (H₂/CO = 30, 1,200 Pa, 350°C), rapid (<0.5 h) and complete transformation to χ-Fe₅C₂ occurs, starting from the particle interior. TEM images after carburization show well-maintained, phase-pure χ-Fe₅C₂ grains with uniform morphology and no evidence of carbon deposition or manganese migration.
- **Observations:** The porous structure, originating from the KOH leaching of aluminum from the iron–aluminum alloy precursor, is preserved through synthesis and activation, supporting high catalytic activity and stability.

#### 6.1.3 Elemental Composition and Promoter Distribution
- **Description:** Elemental composition and promoter distribution were assessed using TEM-based techniques.
- **Findings:** Manganese, when introduced as a promoter (0.5–12.5 wt%), remains well-dispersed within the iron phase and does not migrate during reaction. The catalyst retains its compositional uniformity after prolonged Fischer–Tropsch operation.
- **Observations:** The stable incorporation of manganese correlates with enhanced catalyst stability, suppression of carbon deposition, and improved oxygen removal, directly contributing to high CO conversion and low CO₂ selectivity.

#### 6.1.4 Porosity and Surface Area
- **Description:** The development of porosity is attributed to the synthesis process, specifically the KOH leaching of aluminum from the iron–aluminum alloy precursor.
- **Findings:** While specific BET surface area, pore size, and pore volume values are not reported, TEM images confirm a highly porous morphology in the as-prepared and activated catalysts.
- **Observations:** The preserved porous structure facilitates efficient reactant diffusion and is integral to the observed high catalytic performance.

#### 6.1.5 Structural Stability under Reaction Conditions
- **Description:** The long-term structural stability of the catalyst was evaluated by in situ ^57Fe Mössbauer spectroscopy and post-reaction TEM analysis.
- **Findings:** After extended Fischer–Tropsch operation, χ-Fe₅C₂ remains the sole iron phase, with no detectable transformation or degradation. TEM images show no carbon buildup or promoter migration.
- **Observations:** The exceptional phase and morphological stability underpin the catalyst’s sustained activity and selectivity during prolonged operation.




### 6.2 Catalyst Performance

#### 6.2.1 CO Conversion
- **Description:** CO conversion quantifies the fraction of carbon monoxide transformed by the catalyst, calculated as:
  \[
  \text{CO Conversion} = \frac{F_{\text{CO,in}} - F_{\text{CO,out}}}{F_{\text{CO,in}}} \times 100
  \]
- **Experimental Data:** The Mn–χ–Fe₅C₂ catalyst achieved CO conversion values of 16.0% at 250°C and 2.3 MPa (SV = 12,000/8,000/8,000 ml g_cat⁻¹ h⁻¹), and 46.1% at 250°C and 3.0 MPa (SV = 3,000/1,900/100 ml g_cat⁻¹ h⁻¹). Under higher temperature and space velocity (320–325°C, 2.3 MPa, SV = 100,000 ml g_cat⁻¹ h⁻¹), CO conversion remained stable at 53% over 225 h.
- **Observations and Trends:** CO conversion increases with pressure and temperature. Manganese promotion significantly enhances conversion compared to unpromoted χ–Fe₅C₂, supporting higher activity under industrially relevant conditions.

#### 6.2.2 CO₂ Selectivity
- **Description:** CO₂ selectivity measures the proportion of converted CO forming CO₂, indicating the extent of unwanted oxidation:
  \[
  \text{CO}_2 \text{ Selectivity} = \frac{F_{\text{CO}_2,\text{out}}}{F_{\text{CO,in}} - F_{\text{CO,out}}} \times 100
  \]
- **Experimental Data:** At 250°C, CO₂ selectivity was 11.2% for χ–Fe₅C₂ and 9.3% for Mn–χ–Fe₅C₂ (2.3 MPa), and 9.4% for Mn–χ–Fe₅C₂ (3.0 MPa). At 290°C, CO₂ selectivity remained low at 9%.
- **Observations and Trends:** The Mn promoter reduces CO₂ selectivity relative to the unpromoted catalyst and reference materials, resulting in higher carbon efficiency.

#### 6.2.3 C₂–C₁₀ Linear α-Olefin (LAO) Selectivity
- **Description:** Selectivity to C₂–C₁₀ LAOs reflects the fraction of converted CO yielding valuable linear α-olefins:
  \[
  \text{C}_2\text{–C}_{10} \text{ LAO Selectivity} = \frac{F_{\text{C}_2\text{–C}_{10}\text{ LAO,out}}}{F_{\text{CO,in}} - F_{\text{CO,out}}} \times 100
  \]
- **Experimental Data:** At 290°C, the Mn–χ–Fe₅C₂ catalyst achieved a carbon-based selectivity of 51% to C₂–C₁₀ LAOs.
- **Observations and Trends:** The catalyst maintains high LAO selectivity across a broad temperature range, with product distributions closely following Anderson–Schulz–Flory (ASF) theory.

#### 6.2.4 α Factor (Chain Growth Probability)
- **Description:** The α factor, derived from ASF theory, represents the probability of chain propagation versus termination:
  \[
  \text{ASF:} \quad W_n = n(1-\alpha)^2\alpha^{n-1}
  \]
  where \( W_n \) is the weight fraction of hydrocarbons with chain length \( n \).
- **Experimental Data:** For Mn–χ–Fe₅C₂, α = 0.61 at 250°C and α = 0.63 at 290°C.
- **Observations and Trends:** These values are near the theoretical optimum (α ≈ 0.63) for maximizing C₂–C₁₀ hydrocarbon production, indicating efficient chain growth and minimal methane formation.

#### 6.2.5 Catalyst Stability and Deactivation Rate
- **Description:** Catalyst stability is assessed by monitoring CO conversion over time; the deactivation rate is:
  \[
  \text{Deactivation Rate} = \frac{\text{CO Conversion}_{\text{initial}} - \text{CO Conversion}_{\text{final}}}{\text{Time}} \quad (\text{h}^{-1})
  \]
- **Experimental Data:** The Mn–χ–Fe₅C₂ catalyst maintained stable CO conversion (53% at 320–325°C, 2.3 MPa, SV = 100,000 ml g_cat⁻¹ h⁻¹) over 225 h, with negligible deactivation observed.
- **Observations and Trends:** The presence of manganese suppresses carbon deposition and prevents phase changes, resulting in exceptional long-term stability.

---
**Summary:**  
The Mn–χ–Fe₅C₂ catalyst demonstrates high CO conversion, low CO₂ selectivity, optimal α factor, and outstanding stability under Fischer–Tropsch conditions. Manganese promotion is critical for enhancing both activity and selectivity, enabling efficient and durable production of linear α-olefins from syngas.
