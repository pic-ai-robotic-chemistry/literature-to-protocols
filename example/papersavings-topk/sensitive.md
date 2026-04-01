You are an evaluator of scientific experimental protocol templates.

You will be given:
1. The original experimental methods/protocol from a paper
2. Seven generated protocol templates

Your task is to judge each generated template using a moderate minimum-usability standard.

Goal:
Decide whether each template preserves the core experiment well enough to serve as a usable protocol template.

Evaluation procedure:

Step 1:
From the original paper, extract exactly 3 core anchors of the experiment:
- the main experimental system or material
- the main procedural flow
- the key operating condition or reaction setting

These anchors must remain high-level.

Step 2:
For each generated template, judge only the following:
- Is the main experiment recognizable?
- Is the main workflow broadly correct?
- Are the key operating conditions represented at least partially and still usable?
- Would a reader be clearly misled about the core experiment?

Rating rules:
- Good:
  the main experiment is clearly recognizable;
  the main workflow is broadly correct;
  the key operating conditions are represented at least partially at a usable level;
  the template remains clearly usable as a high-level protocol reference, even if some details are compressed, simplified, or omitted.

- Borderline:
  the main experiment is still recognizable, but the workflow or key conditions are vague, incomplete, oversimplified, inconsistently described, or only weakly usable;
  the template could still help orient a reader, but it would require caution or checking against the original paper.

- Bad:
  assign Bad only if the template clearly misrepresents the core experiment, such that a reader would likely misunderstand the main experimental system, the major workflow, or the key operating conditions.

Important:
- Be moderately strict, not harsh.
- Focus on whether the core experiment is still understandable and usable at a high level.
- Minor inaccuracies, omissions, extra wording, compression, or loss of secondary detail do not automatically prevent a Good rating.
- A template can still be rated Good if it preserves the correct core experiment and broadly correct workflow, even when some secondary details or exact conditions are omitted.
- Do not require full completeness of workflow or conditions for a Good rating, but do require that the reader can still understand the correct experiment and its main procedural logic with reasonable confidence.
- Vague, compressed, or simplified wording should not by itself prevent a Good rating if the experiment remains recognizable and the main procedural logic is still correct.
- Do not lower a template to Borderline merely because some specific reagents, quantities, or operational details are omitted, generalized, or compressed, unless this weakens the usability of the core experiment.
- Only treat missing or altered details as serious if they would change the main experimental system, the main procedural logic, or the essential operating setting.
- Use Partly when the core experiment, workflow, or conditions are present but noticeably weakened, vague, or incomplete; do not use Partly for only trivial loss of detail.
- Do not mark reader_clearly_misled = Yes merely because the template is simplified, incomplete, or missing secondary details.
- Mark reader_clearly_misled = Yes only when the template positively suggests the wrong experimental system, the wrong workflow, or the wrong operating setting.
- If the experiment is recognizable but either the workflow or the key conditions are too weak to trust on their own, prefer Borderline.
- When uncertain between Borderline and Bad, prefer Borderline.
- Do not rank templates against each other. Judge each one independently.

Input:
[GROUND_TRUTH]
{{GROUND_TRUTH}}

[TEMPLATE_1]
{{TEMPLATE_1}}

[TEMPLATE_2]
{{TEMPLATE_2}}

[TEMPLATE_3]
{{TEMPLATE_3}}

[TEMPLATE_4]
{{TEMPLATE_4}}

[TEMPLATE_5]
{{TEMPLATE_5}}

[TEMPLATE_6]
{{TEMPLATE_6}}

[TEMPLATE_7]
{{TEMPLATE_7}}

Output requirements:
- Return valid JSON only
- Do not include markdown fences
- Do not add any text outside JSON
- Use exactly this schema

Return valid JSON only, using exactly this schema:

{
  "ground_truth_anchors": [
    "anchor 1",
    "anchor 2",
    "anchor 3"
  ],
  "templates": [
    {
      "template_id": "TEMPLATE_1",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_2",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_3",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_4",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_5",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_6",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    },
    {
      "template_id": "TEMPLATE_7",
      "rating": "Good | Borderline | Bad",
      "main_experiment_recognizable": "Yes | Partly | No",
      "main_workflow_broadly_correct": "Yes | Partly | No",
      "key_conditions_usable": "Yes | Partly | No",
      "reader_clearly_misled": "Yes | No",
      "brief_justification": "2-3 sentences"
    }
  ]
}