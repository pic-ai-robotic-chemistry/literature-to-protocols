# prompt_examples.md

# Representative Prompt Examples for Normalization-Aware KG Construction

This file summarizes representative schema and prompt components used in `paper_type()` for normalization-aware knowledge-graph construction in the literature-to-protocol pipeline, as shown in `graph_utils/graph_generate_bak.py`.

## 1. Purpose

The KG construction stage does not rely on unconstrained extraction from raw paper text. Instead, it uses:

- schema-level constraints:
  - predefined node categories
  - predefined relation types
  - domain-specific extensions by paper type
- prompt-level constraints:
  - consistent node labeling
  - structured numerical attributes
  - referential consistency across repeated mentions
  - constrained relation direction and chemistry-specific link types

These components are used to normalize extracted entities, attributes, and relations before retrieval and protocol generation.

---

## 2. Core `paper_type()` Responsibilities

The `paper_type()` function configures domain-aware KG extraction by:

1. defining allowed node types
2. defining allowed relation types
3. attaching a domain label to document splits
4. expanding the schema for specific domains such as Fischer–Tropsch synthesis
5. constructing the system prompt passed to `LLMGraphTransformer`

For the Fischer–Tropsch setting, this function provides both:
- a domain-specific schema
- a domain-specific extraction instruction prompt

---

## 3. Schema-Level Constraints

## 3.1 Base node categories

Representative base node categories include:

- `Equipment:Synthesis Equipment`
- `Equipment:Characterization Equipment`
- `Equipment:Purification and Drying Equipment`
- `Reagents:Solvents`
- `Reagents:Base or Acid Regulators`
- `Reagents:Gases`
- `Characterization Methods:X-ray diffraction (XRD)`
- `reaction:temperature`
- `reaction:time`
- `reaction:pressure`
- `Purification:Washing`
- `Drying:temperature`

These categories constrain the representational space of the graph and reduce uncontrolled variation in node typing.

## 3.2 Base relation categories

Representative base relation types include:

- `is_used_by`
- `uses_material_from`
- `consumes`
- `produces`
- `is_synthesized_from`
- `is_mixed_with`
- `is_dissolved_in`
- `contains_chemical`
- `is_heated_in`
- `is_followed_by`
- `reacts_with`
- `is_analyzed_by`
- `has_temperature`
- `has_pressure`
- `has_duration`
- `has_concentration`

These predefined relation types reduce ambiguity in relation naming and support more stable downstream retrieval.

---

## 4. Fischer–Tropsch-Specific Schema Extensions

For the `FT Framework`, the schema is further extended with domain-specific node and relation types.

## 4.1 Representative FT-specific node extensions

Examples include:

- `Reagents:Promoter Precursors`
- `Reagents:Additive Precursors`
- `Reagents:Support Materials`
- `Reagents:Surface Modifiers`
- `Reagents:Reducing Agents`
- `Equipment:Fixed-bed Reactors`
- `Equipment:Slurry Reactors`
- `reaction:H2_CO_ratio`
- `reaction:space_time_velocity`
- `Activation:reduction_temperature`
- `Activation:reduction_gas`
- `Activation:reduction_time`
- `Results:alpha_value`
- `Results:C5+ selectivity`
- `Results:CO2_selectivity`
- `Results:olefin_to_paraffin_ratio`
- `Deactivation:carbon_deposition`
- `Process:feedstock_composition`
- `Process:product_distribution`

## 4.2 Representative FT-specific relation extensions

Examples include:

- `is_reduced_by`
- `is_promoted_by`
- `supports_catalyst`
- `is_loaded_with`
- `operates_under`
- `requires_H2_CO_ratio`
- `has_space_time_velocity`
- `exhibits_selectivity_for`
- `produces_product_distribution`
- `has_alpha_value`
- `undergoes_deactivation_due_to`
- `shows_carbon_deposition`
- `requires_pretreatment`
- `is_monitored_by`
- `undergoes_in_situ_characterization`

These domain-specific additions constrain the graph to chemistry-relevant semantics rather than generic open-ended relation generation.

---

## 5. Prompt-Level Normalization Constraints

The extraction prompt used for Fischer–Tropsch synthesis includes several explicit normalization instructions.

## 5.1 Node-label constraints

Representative prompt instructions:

- use general labels for consistency
- prefer general categories such as `catalyst` instead of highly local names such as `cobalt catalyst`
- use text-based identifiers rather than integer IDs

**Function:** reduce local naming drift and stabilize node typing.

## 5.2 Attribute-format constraints

Representative prompt instructions:

- include numerical values such as temperature and pressure as node attributes
- format them as key–value pairs
- use fixed naming conventions such as camel case

Example:

- `activationTemperature: 350`

**Function:** convert free-text experimental conditions into structured attribute representations.

## 5.3 Coreference-consistency constraints

Representative prompt instructions:

- maintain consistency for entities mentioned multiple times
- use the same identifier for repeated mentions of the same concept

Example:

- keep `Temperature-Programmed Reduction` consistent across mentions

**Function:** prevent the same experimental object from being split into multiple inconsistent nodes.

## 5.4 Relation-type and direction constraints

Representative prompt instructions:

- use active voice for clarity
- ensure relation direction reflects the underlying interaction
- preserve chemistry-specific hierarchy among catalyst components and process entities

Example:

- `Tubular Furnace - REDUCES -> Catalyst`

**Function:** reduce relation ambiguity and enforce stable graph semantics.

---

## 6. Representative Fischer–Tropsch Prompt Example

A representative system prompt includes the following components:

1. **Overview**
   - extract structured information for Fischer–Tropsch synthesis experiments
   - focus on catalyst development, reaction conditions, and product analysis

2. **Node Labeling**
   - consistent general labels
   - text-based node IDs
   - allowed node labels listed explicitly

3. **Numerical Data and Dates**
   - numerical conditions represented as attributes
   - key–value formatting
   - fixed naming conventions

4. **Coreference Resolution**
   - repeated mentions should remain consistent

5. **Relationship Direction**
   - active voice preferred
   - direction should reflect actual interactions

6. **Chemistry-Specific Rules**
   - catalyst components should preserve hierarchy
   - synthesis, reaction-condition, and performance links should use predefined relation styles

7. **Worked Example**
   - cobalt-based catalyst on silica
   - reduction under hydrogen at 350 °C for 2 h
   - C5+ selectivity and alpha value
   - example nodes and example relations

This worked example explicitly demonstrates how the prompt maps paper text into normalized nodes, attributes, and relations.

---

## 7. Example of How the Prompt Supports Normalization

Given source text such as:

> A cobalt-based catalyst on silica was prepared via impregnation. The precursor was reduced in a tubular furnace at 350°C under hydrogen for 2 hours. The catalyst showed 65% C5+ selectivity and an alpha value of 0.85.

The prompt encourages extraction in the following normalized form:

### Representative nodes
- `Cobalt-Based Catalyst`
  - type: `catalyst`
  - supportMaterial: `silica`
  - preparationMethod: `impregnation`

- `Reduction Condition`
  - type: `reaction condition`
  - temperature: `350`
  - gas: `hydrogen`
  - duration: `2h`

- `C5+ Hydrocarbons`
  - type: `product`
  - carbonRange: `C5+`

### Representative relations
- `Reduction Condition - PRODUCES -> Cobalt-Based Catalyst`
- `Cobalt-Based Catalyst - EXHIBITS_SELECTIVITY_FOR -> C5+ Hydrocarbons`

This illustrates how the extraction prompt constrains:
- node typing
- numerical attribute formatting
- relation semantics
- chemistry-specific normalization

---

## 8. How This Supports the Manuscript Claims

These schema and prompt components support the manuscript's methodological claim that normalization is implemented through explicit constraints during KG construction, rather than through unconstrained keyword matching over raw paper text.

More specifically, they provide concrete examples of:

- node-label constraints
- attribute-format constraints
- coreference-consistency requirements
- relation-type restrictions

Accordingly, Eq. (1) should be interpreted as matching over normalized entity–attribute representations in the KG, rather than as naive keyword matching over the original paper text.

---

## 9. Suggested Short Citation Language for the Manuscript

A concise in-text pointer can be written as:

> Representative extraction-prompt examples and schema definitions illustrating these normalization constraints are available in the repository (`graph_utils/graph_generate_bak.py`).

If preferred, this material can also be moved to a dedicated supplementary file to provide a more stable archival reference than code line numbers.
