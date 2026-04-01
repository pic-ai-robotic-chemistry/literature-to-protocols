# Pt/In2S3/CdS/Cu2ZnSnS4 Thin Film as an Efficient and Stable Photocathode for Water Reduction under Sunlight Radiation

## **1. Material Design & Fundamental Properties**

### 1.1 Target Composition & Crystal Chemistry
- **Nominal Composition**: Cu2ZnSnS4 (CZTS) with an elemental ratio of Cu/Zn/Sn/S = 23/14/13/50, as verified by EDX analysis.
- **Crystal Structure**: Kesterite phase achieved through electrodeposited Cu/Sn/Zn stacks followed by a two-step sulfurization process (320 °C for 200 minutes then 590 °C for 10 minutes in a sulfur atmosphere), confirmed by XRD and Raman spectroscopy.
- **Interfacial Engineering**: Integration of CdS and In2S3 layers as n-type semiconductor buffers; In2S3 specifically acts to protect the CdS layer from photocorrosion and to facilitate enhanced charge transfer.

### 1.2 Band Structure & Energetics
- **Band Gap**: Approximately 1.45 eV, determined from IPCE measurements and spectral conversion (plot of [hν ln(1 − IPCE)]² vs. photon energy), which aligns with the design target for effective light absorption.
- **Electronic Optimization Rationale**: The energy alignment through the strategic layering of CdS and In2S3 is aimed at improving charge separation dynamics, although explicit band edge positions relative to water redox potentials are not detailed.

### 1.3 Morphology, Facets & Heterostructures
- **CZTS Morphology**: The CZTS film exhibits well-grown crystallites with grain sizes of about 1.5 μm, as observed by SEM.
- **Buffer Layer Dimensions**: The CdS layer is dense and approximately 150 nm thick, while the In2S3 overlayer measures around 300 nm, effectively covering grain boundaries.
- **Composite Formation**: The Pt/In2S3/CdS/CZTS composite is constructed with a Pt co-catalyst deposited via photoelectrodeposition under simulated AM 1.5G illumination, forming an efficient heterostructure that enhances HER kinetics.
- **Design Rationale for Heterostructuring**: This layered architecture is engineered to optimize electron transport and interfacial contact, thereby promoting a stable and high-performing photocathode for water reduction under solar irradiation.

## **2. Synthesis & Post-Processing**

### 2.1 Synthesis Protocol
1. **Electrodeposition**: Deposit the Cu/Sn/Zn stack on a Mo-coated glass substrate pre-treated with a **10% KCN solution for 2 minutes**.  
  - Deposit the Cu layer at **−0.4 V** using a bath containing **0.05 M CuSO₄·5H₂O**, **0.02 M citric acid**, and **0.04 M trisodium citrate**.  
  - Deposit the Sn layer at **−0.54 V** using a solution of **0.05 M Sn(II) methanesulfonate**, **1 M methanesulfonic acid**, and **1 M Empigen BB detergent**.  
  - Deposit the Zn layer at **−1.2 V** from a bath with **0.1 M ZnSO₄·7H₂O** and **0.5 M K₂SO₄** (pH adjusted to 3).

2. **Thermal Processing and Sulfurization**:  
  - Heat the as-deposited stack at **320 °C for 200 minutes** in an evacuated Pyrex ampule.  
  - Sulfurize by heating at **590 °C for 10 minutes** in the presence of **5–10 mg elemental sulfur powder** to form the crystalline kesterite CZTS phase.

### 2.2 Post-Treatments & Modification
1. **Surface Cleaning**: Immerse the sulfurized CZTS film in a **10% KCN solution for 2 minutes** (to remove surface contaminants).  
2. **No Additional Bulk Modifications**: The protocol does not report further chemical or thermal bulk treatments beyond the cleaning procedure.

### 2.3 Co-catalyst & Surface Functionalization
1. **CdS Deposition**: Form the β-CdS layer via chemical bath deposition.  
  - Immerse the CZTS film in an aqueous solution containing **12.5 mmol dm⁻³ CdSO₄**, **0.22 M thiourea (SC(NH₂)₂)**, and **11 M NH₄OH** at **60 °C for 7 minutes**.
2. **In₂S₃ Deposition**: Deposit the In₂S₃ interlayer to protect the CdS and enhance charge separation.  
  - Use a chemical bath with **25 mol dm⁻³ In₂(SO₄)₃**, **0.1 M CH₃CSNH₂**, and **0.1 M CH₃COOH** at **65 °C for 15 minutes**.
3. **Pt Photodeposition**: Load Pt as the co-catalyst by photodeposition to reduce hydrogen overpotential.  
  - Conduct the process in a solution of **1 mM H₂PtCl₆** in **0.1 M Na₂SO₄** at a constant potential of **−0.1 V** under simulated AM 1.5G sunlight (**100 mW cm⁻²**) for **10 minutes**.

## **3. Characterization Methods & Settings**

The comprehensive characterization of the Pt/In₂S₃/CdS/CZTS photocathode utilizes complementary techniques to elucidate structural, compositional, optical, and electronic properties. The methods are organized into two main groups as follows.

### 3.1 Structural & Compositional Analysis

#### X-ray Diffraction (XRD)
- **Sample Preparation**: The CZTS film is prepared on its substrate; samples may be scraped or slightly milled for analysis.
- **Instrument & Model**: Rigaku Mini Flex X-ray diffractometer.
- **Instrument Parameters**: Cu Kα radiation is used; although exact 2θ range and step size are not specified, the settings are optimized for phase identification.
- **Measurement Conditions**: Performed under ambient temperature and pressure.
- **Test/Acquisition Parameters**: Typical scanning involved preliminary alignment followed by a full scan to capture the diffraction profile.
- **Operational Procedure**:
  1. Mount the film (or powdered sample) on a zero-background holder.
  2. Execute an alignment scan.
  3. Record the diffraction pattern over the selected 2θ range.
- **Purpose**: To confirm the formation of the kesterite CZTS phase and estimate crystallite size.
- **Data Analysis & Calibration**: Data processed using standard ICDD database approaches with potential Rietveld refinement; calibration is based on known standards.
- **Key Notes**: The procedure confirms the crystallographic integrity of the film and aids in phase purity assessment.

#### Raman Spectroscopy
- **Sample Preparation**: The as-deposited films are analyzed directly on their substrates.
- **Instrument & Model**: Jasco NRC 3100 laser Raman spectrophotometer.
- **Measurement Conditions**: Ambient conditions; specific excitation wavelength and integration time are adjusted to optimize spectral resolution.
- **Operational Procedure**:
  1. Illuminate the sample with a focused laser beam.
  2. Collect the scattered light.
- **Purpose**: To verify the structural signatures of the CdS and In₂S₃ layers via their characteristic Raman shifts.
- **Data Analysis & Calibration**: Raman peaks are compared with literature values to confirm layer compositions.
- **Key Notes**: Provides complementary structural validation alongside XRD.

#### X-ray Photoelectron Spectroscopy (XPS)
- **Sample Preparation**: Photodeposited samples are positioned to maximize surface sensitivity.
- **Measurement Conditions**: Measurements conducted under ultra-high vacuum conditions.
- **Operational Procedure**:
  1. Perform a survey scan to identify elemental composition.
  2. Record high-resolution scans of key binding energy regions.
- **Purpose**: To assess the surface chemical states and verify the deposition of catalysts.
- **Data Analysis & Calibration**: Energy scale is calibrated using the C 1s peak at 284.8 eV.
- **Key Notes**: Ensures precise surface composition analysis critical for interface quality.

### 3.2 Photophysical & Electrical Analysis

#### UV-Vis-NIR Diffuse Reflectance Spectroscopy (DRS)
- **Sample Preparation**: Powder samples are packed in a quartz holder with a transparent window.
- **Instrument & Model**: Shimadzu UV-3600i Plus spectrophotometer with an integrating sphere.
- **Instrument Parameters**: Utilizes halogen and deuterium lamps with PMT and InGaAs detectors.
- **Measurement Conditions**: Ambient conditions with BaSO₄ as a 100% reflectance reference.
- **Test/Acquisition Parameters**: Wavelength range from 250 to 1200 nm, with medium scan speed and 1 nm data intervals.
- **Operational Procedure**:
  1. Record baseline using BaSO₄.
  2. Replace the standard with the sample and acquire the spectrum.
- **Purpose**: To determine the optical absorption edge and band gap (approximately 1.45 eV).
- **Data Analysis & Calibration**: Reflectance data are converted via the Kubelka-Munk function and analyzed through Tauc plots.
- **Key Notes**: Confirms the optical behavior crucial for efficient light absorption.

#### Photoelectrochemical (PEC) Diagnostics (Mott-Schottky/EIS)
- **Sample Preparation**: Photocathodes integrated into both three-electrode and two-electrode PEC cells.
- **Measurement Conditions**: Testing in a 0.2 mol dm⁻³ phosphate buffer (pH 6.5) using AM 1.5G simulated sunlight (100 mW cm⁻²).
- **Test/Acquisition Parameters**: Current–potential responses recorded and potentials converted to RHE.
- **Operational Procedure**:
  1. Illuminate the photocathode under chopped light conditions.
  2. Record the I–V response and perform electrochemical impedance spectroscopy.
- **Purpose**: To evaluate photocurrent density, onset potentials, and charge separation efficiency.
- **Data Analysis & Calibration**: Analysis of J–V curves and IPCE data validates improved junction formation.
- **Key Notes**: Both spectral and electrical diagnostics complement structural and compositional insights.

## **4. Photocatalyst System Architecture**

### 4.1 System Configuration
- **OWS Mode**: One-step system.
  - **For One-step System:**  
    - **Photocatalyst Material**: Pt/In2S₃/CdS/CZTS composite, where the CZTS thin film serves as the primary light absorber.  
    - **Buffer Layers**: The CdS layer facilitates efficient charge separation, while the In₂S₃ layer acts as a protective buffer that enhances electrical contact and reduces photocorrosion of CdS.  
    - **Co-catalyst**: Pt nanoparticles, deposited via photoelectrodeposition in a 0.1 M Na₂SO₄ solution containing 1 mM H₂PtCl₆, serve to lower the hydrogen evolution overpotential and boost overall photocatalytic activity.

### 4.2 Operational Design
- **Light Absorption and Illumination**:  
  - **Light Source**: Utilization of AM 1.5G simulated sunlight at an intensity of 100 mW cm⁻² ensures broad spectrum irradiation.  
  - **Target Wavelength Range**: The operational design targets effective absorption within the 400–700 nm range, a spectrum conducive to maximizing photon capture and photocurrent generation.
- **System Architecture and Reaction Configuration**:  
  - **Testing Cell Setup**: The OWS process is implemented in a two-electrode configuration, where the Pt/In₂S₃/CdS/CZTS photocathode is coupled with a BiVO₄-based photoanode, facilitating bias-free water splitting.  
  - **Gas Evolution Monitoring**: While the design does not incorporate an explicit physical membrane or reactor compartmentalization for the separation of H₂ and O₂, online gas chromatography is applied to analyze the evolved gases and maintain operational oversight.
- **Operational Parameters and Safety Considerations**:  
  - **Controlled Environment**: The reaction is conducted in a pH 6.5 phosphate buffer solution (0.2 mol dm⁻³ Na₂HPO₄/NaH₂PO₄) to ensure electrolyte stability and minimize charge recombination.  
  - **Charge Transfer Efficiency**: The integrated double-layer configuration with In₂S₃ and CdS improves interfacial contact, thereby reducing series resistance and bolstering charge carrier efficiency.

This integrated approach, grounded in a one-step OWS strategy, highlights a deliberate configuration that leverages material synergy and controlled light management to facilitate effective water splitting under solar irradiation.

## **5. Testing System Configuration**

### 5.1 Reactor & Gas Handling
- **Reactor Design & Temperature Control**: The photoelectrochemical (PEC) cell was equipped with a water jacket to maintain a constant temperature of **293 K** during operation, ensuring thermal stability throughout the water splitting experiments.
- **Electrode Configuration**: Experiments were conducted using both three-electrode and two-electrode setups. For bias-free overall water splitting, the **Pt/In₂S₃/CdS/CZTS photocathode** was paired with a BiVO₄ photoanode.
- **Gas Analysis Chain**:
  - **Online Detection**: The PEC cell was directly connected to an **online gas chromatography (GC) system** for real-time monitoring of evolved gases.
  - **GC Instrumentation**: An **Agilent 490 Micro GC gas analyzer** equipped with an **MS-5A column** and a **thermal conductivity detector (TCD)** was employed for quantitative analysis of **H₂** and **O₂**.
  - **Sampling Protocol**: Gaseous products were continuously sampled from the reactor headspace and directed to the GC for immediate analysis, enabling accurate tracking of gas evolution rates.
  - **Carrier Gas**: While the specific carrier gas is not detailed, standard practice for MS-5A columns and TCDs typically involves argon or helium.
  - **Calibration**: Quantification was based on calibration with standard gas mixtures, ensuring reliable measurement of H₂ and O₂ concentrations.
- **Pressure & Atmosphere**: The reactor headspace atmosphere and pressure conditions were not explicitly specified; however, the system was designed for ambient pressure operation.

### 5.2 Illumination Conditions
- **Light Source**: An **Asahi Spectra HAL320 solar simulator** provided illumination, delivering **simulated AM 1.5G solar light** to closely replicate terrestrial sunlight.
- **Spectral Output & Filtering**: The AM 1.5G filter ensured the spectral distribution matched standard solar conditions, critical for benchmarking photocatalytic performance.
- **Irradiance & Calibration**: The incident light intensity at the sample position was set to **100 mW cm⁻²**, calibrated by measuring the current–voltage (J–V) curve of a standard silicon (Si) solar cell. This approach guarantees that the irradiance corresponds precisely to the AM 1.5G standard.
- **Illumination Geometry**: The working electrode (photocathode) was illuminated over an active area of **0.3 cm²** during H₂ evolution experiments, ensuring defined and reproducible exposure.

### 5.3 Reaction Medium
- **Electrolyte/Buffer**: The reaction medium consisted of a **phosphate buffer solution** (0.2 mol dm⁻³ Na₂HPO₄/NaH₂PO₄) maintained at **pH 6.5**, providing a neutral environment conducive to overall water splitting.
- **Water Quality**: While the specific purity of water was not detailed, the use of buffer solutions in PEC studies typically implies high-purity, deionized water.
- **Atmosphere**: The headspace composition during testing was not explicitly described, but the system was configured for direct gas evolution and analysis under ambient conditions.
- **Sacrificial Agent Verification**: No sacrificial electron donors or acceptors (e.g., methanol, triethanolamine, AgNO₃, Na₂S/Na₂SO₃) were added to the reaction medium. The experiment was conducted in pure phosphate buffer, confirming the test as true overall water splitting.

## **6. Performance Evaluation & Validation**

### 6.1 Activity Metrics
- **Photocurrent Density**: −9.3 mA cm⁻² at 0 VRHE under AM 1.5G simulated sunlight (100 mW cm⁻²) in a three-electrode configuration with 0.2 mol dm⁻³ Na₂HPO₄/NaH₂PO₄ (pH 6.5) as electrolyte.
- **Half-Cell Solar-to-Hydrogen (HC-STH) Efficiency**: 1.63% at 0.31 VRHE for the Pt/In₂S₃/CdS/CZTS photocathode, calculated using HC-STH (%) = (J × V × 100) / P, where J is photocurrent density, V is applied potential, and P is light intensity (100 mW cm⁻²).
- **Faradaic Efficiency for H₂ Evolution**: 96% at 0 VRHE, indicating nearly all photocurrent contributed to H₂ production; at 0.5 VRHE, Faradaic efficiency decreased from 89% (first 90 min) to 79% (last 30 min).
- **H₂ Evolution Rate**: 0.477 μmol min⁻¹ at 0 VRHE during a 2-hour test, with constant rate observed.
- **Incident Photon-to-Current Efficiency (IPCE)**: 45–50% between 400–700 nm, confirming efficient photoresponse across the visible spectrum.
- **H₂:O₂ Stoichiometric Ratio**: Not explicitly stated, but high Faradaic efficiency and monitored gas evolution suggest near-stoichiometric water splitting.

### 6.2 Selectivity & Mechanism
- **Product Origin Confirmation**: Evolved H₂ and O₂ were quantified by online gas chromatography (Agilent 490 Micro GC, MS-5A column, TCD detector) during PEC operation.
- **Suppression of Side Reactions**: The In₂S₃ interlayer prevented direct contact between CdS and electrolyte, reducing photocorrosion and undesired side reactions.
- **Mechanistic Insight**: The improved charge separation and reduced series resistance at the Pt/In₂S₃ interface were inferred from enhanced photocurrent and IPCE, though no isotope labeling or direct mechanistic probes were reported.

### 6.3 Stability & Durability
- **Continuous Operation**: The Pt/In₂S₃/CdS/CZTS electrode maintained stable photocurrent over 3 hours of continuous illumination, with no appreciable decrease; in contrast, Pt/CdS/CZTS showed significant decay (to –0.08 mA cm⁻²).
- **Faradaic Efficiency Over Time**: Remained high (96%) at 0 VRHE during 2-hour H₂ evolution; some decline at higher bias (0.5 VRHE).
- **Post-Reaction Characterization**:
  - **XPS**: For Pt/In₂S₃/CdS/CZTS, no new peaks or shifts were observed after testing, indicating chemical stability. For Pt/CdS/CZTS, new CdO shoulder peaks appeared, evidencing CdS oxidation.
  - **SEM**: In₂S₃ layer fully covered CdS/CZTS grains and grain boundaries, supporting its protective role.
  - **Raman Spectroscopy**: Confirmed retention of kesterite structure post-operation.

### 6.4 Controls & Data Quality
- **Gas Quantification**: Online gas chromatography ensured accurate measurement of H₂ and O₂ evolution during PEC tests.
- **Catalyst Loading Control**: Pt was photodeposited under standardized conditions (0.1 M Na₂SO₄, 1 mM H₂PtCl₆, −0.1 V, 10 min, AM 1.5G illumination) to ensure reproducibility.
- **Comparative Stability Testing**: Direct comparison between Pt/In₂S₃/CdS/CZTS and Pt/CdS/CZTS electrodes under identical conditions highlighted the stabilizing effect of the In₂S₃ layer.
- **Statistical Reporting**: No explicit mention of error bars, standard deviations, or number of replicates; data are presented as representative results.
- **Experimental Safeguards**: No specific dark or blank controls described, but high Faradaic efficiency and gas monitoring support the reliability of the reported performance.