# eval_final_plans_parallel.py

import json
import re
import csv
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.messages import HumanMessage
from agents.load_llm import main_llm, fast_llm


ROOT_DIR = Path(".")
OUT_DIR = Path("eval_mof_plan_diff_results")
OUT_DIR.mkdir(exist_ok=True)

JSONL_PATH = OUT_DIR / "final_plan_pair_eval.jsonl"
PRETTY_JSON_PATH = OUT_DIR / "final_plan_pair_eval_pretty.json"
CSV_PATH = OUT_DIR / "final_plan_pair_eval.csv"
RAW_DIR = OUT_DIR / "raw_llm_outputs"
RAW_DIR.mkdir(exist_ok=True)

MAX_PAIRS = 20

# 并发数量。建议 3-4 起步；如果限速，调成 2 或 1。
MAX_WORKERS = 4

# Use fast_llm for cheaper/faster evaluation.
# Set to False if you want to use main_llm.
USE_FAST_LLM = False

# Summary uses deterministic derived score instead of only the LLM's direct winner.
USE_DERIVED_WINNER_FOR_SUMMARY = True


def find_final_plan_file(folder: Path) -> Optional[Path]:
    """
    Find the final plan file in a folder.
    Compatible with:
    - 21_main_final_plan.txt
    - main_final_plan.txt
    - xxx_main_final_plan(1).txt
    """
    if not folder.exists():
        return None

    candidates = list(folder.glob("*main_final_plan*.txt"))
    if not candidates:
        return None

    def score(p: Path):
        m = re.match(r"^(\d+)_", p.name)
        prefix_num = int(m.group(1)) if m else -1
        return (prefix_num, len(p.name))

    return sorted(candidates, key=score, reverse=True)[0]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_json(content: str) -> Dict[str, Any]:
    """
    Try to extract valid JSON from model output.
    """
    content = content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start:end + 1])

    raise ValueError(f"Cannot parse JSON from model output:\n{content[:1000]}")


def build_eval_prompt(
    pair_id: int,
    origin_text: str,
    protocol_text: str,
) -> str:
    return f"""
You are an evaluator for automated experimental workflow generation.

Your task is to compare two final plans:
- PLAN_A_ORIGIN_PAPER: generated from the original paper.
- PLAN_B_PROTOCOL: generated from an extracted protocol.

Evaluation goal:
Decide which final plan is better for converting the experimental information into an automation-scope material-preparation workflow.

Very important framing:
1. Evaluate the automatable material-preparation lifecycle, NOT the full paper workflow.
2. Do NOT reward a plan for including downstream applications, characterization, performance tests, product analysis, or extra paper content.
3. Downstream catalytic testing, photocatalysis, electrochemical testing, GC/HPLC/NMR/XRD analysis, gas analysis, product sampling, and performance evaluation are NOT required stages by default.
4. If downstream tests or offline analysis are included in the main executable workflow without being clearly marked as optional, out-of-scope, or external, count them as application overreach.
5. Do NOT penalize a plan for omitting downstream tests or offline analysis if the material-preparation workflow is complete.
6. Drying, activation, post-synthetic modification, washing, purification, final dispersion/storage, and waste handling ARE part of the material-preparation lifecycle when relevant.
7. Manual, external, or unsupported operations are acceptable if they are clearly isolated as boundaries instead of being falsely treated as automated.
8. Multi-branch material synthesis is acceptable if the branches are clearly separated. It is bad only if incompatible branches are mixed.

The core question is:
"Which plan better produces an automation-ready material-preparation workflow, with proper boundaries for non-automatable or downstream application steps?"

Default required material-preparation lifecycle:
- reagent/container preparation,
- solid/liquid dosing,
- precursor solution preparation,
- mixing/stirring/dispersion before synthesis,
- main synthesis reaction,
- post-synthetic modification if required for the target material,
- washing/purification/centrifugation/filtration,
- solvent exchange if needed,
- drying,
- activation if needed for final material state,
- final dispersion/storage state,
- waste handling,
- explicit boundary notes for manual/external/unsupported required preparation steps.

Default non-required downstream/application stages:
- catalytic reaction testing,
- photocatalytic performance testing,
- methane oxidation testing,
- electrochemical testing,
- electrode performance measurement,
- gas analysis,
- GC/HPLC/NMR/XRD/product analysis,
- offline characterization,
- performance evaluation,
- product sampling for analysis.

Important rule:
Only count downstream/application/testing stages as required if BOTH plans explicitly define the final plan's main target as executing that downstream test. If only one plan includes downstream tests while the other focuses on material preparation, treat the downstream inclusion as potential overreach, not as an omission by the other plan.

Metrics to evaluate:

1. Material Preparation Coverage
Evaluate whether the plan covers the required material-preparation lifecycle.
Compute:
material_coverage = covered_material_stage_count / required_material_stage_count

A plan should be rewarded for covering synthesis, washing, drying, activation, modification, final material state, and waste handling.
A plan should NOT get extra credit for downstream application tests.

2. Material Stage Omission
Count missing stages from the material-preparation lifecycle only.
Do not count omitted downstream testing or characterization as omissions.
Fields:
- material_omission_count
- severe_material_omission_count
- missing_material_stages

3. Automation Boundary Quality
Evaluate whether non-automatable operations are handled correctly.
Good:
- manual/external/unsupported steps are clearly marked,
- downstream tests are marked optional/out-of-scope/external,
- unsupported preparation steps are not disguised as automated,
- platform substitutes are provided when reasonable.

Bad:
- unsupported operation is treated as automated,
- gas charging, glovebox, furnace, vacuum, rotary evaporation, freeze-thaw, membrane extrusion, offline analysis, or characterization are silently placed in the automated main workflow without boundary notes.

Score:
automation_boundary_score_5 from 0 to 5.

4. Application Overreach
Count downstream or analysis steps included in the main executable workflow.

Examples of application overreach:
- catalytic reaction testing in the main workflow,
- photocatalysis testing in the main workflow,
- electrochemical testing in the main workflow,
- GC/HPLC/NMR/XRD/gas analysis in the main workflow,
- product sampling for offline analysis treated as a required automated step,
- performance evaluation included as if it were part of material preparation.

Do NOT count these as overreach if clearly marked optional, external, out-of-scope, or excluded from automation.

Fields:
- downstream_test_in_main_count
- offline_analysis_in_main_count
- optional_or_external_downstream_count
- application_overreach_penalty_5 from 0 to 5

5. Platform Adaptation Practicality
Evaluate whether the material-preparation workflow is practically executable on the platform.
Reward:
- valid module mapping,
- clear containers,
- clear sample transitions,
- actionable parameters or safe platform defaults,
- reasonable handling of manual/external boundaries.

Penalize:
- severe vessel/volume mismatch,
- wrong module mapping,
- missing essential transfer,
- unclear final material state,
- impossible automated operation.

Score:
platform_adaptation_practicality_score_20 from 0 to 20.

6. Automation-Scope Fidelity
Evaluate whether the plan faithfully converts the experimental protocol into an automation-scope workflow.
Reward:
- material-preparation lifecycle is preserved,
- downstream tests are excluded or clearly separated,
- manual/external boundaries are clear,
- difficult steps are not silently deleted,
- extra paper content is not mixed into the main workflow.

Score:
automation_scope_fidelity_score_20 from 0 to 20.

7. Branch Handling
Evaluate material synthesis branches only.
Good:
- multiple material variants or MOF branches are clearly separated,
- independent containers and reaction conditions are clear,
- parallelization is schedulable.

Bad:
- incompatible routes mixed together,
- route conditions merged incorrectly,
- unclear sample-to-step mapping.

Score:
branch_handling_score_5 from 0 to 5.
If no branching is required, give 5 unless the plan invents unnecessary branches.

You should compare the following two plans:

==============================
PLAN_A_ORIGIN_PAPER_{pair_id}
==============================
{origin_text}

==============================
PLAN_B_PROTOCOL_{pair_id}
==============================
{protocol_text}

Return only valid JSON. Do not include markdown, comments, or explanatory text outside the JSON.

Use exactly this JSON schema:

{{
  "pair_id": {pair_id},
  "winner": "origin_paper | protocol | tie",
  "winner_reason_short": "One concise sentence explaining why the winner is better for automation-scope material workflow generation.",
  "evaluation_basis": {{
    "inferred_material_preparation_stages": [
      "stage 1",
      "stage 2"
    ],
    "excluded_downstream_stages": [
      "downstream stage 1",
      "downstream stage 2"
    ],
    "notes": "Briefly state the inferred automation-scope material workflow."
  }},
  "origin_paper": {{
    "material_preparation_coverage": {{
      "required_material_stage_count": 0,
      "covered_material_stage_count": 0,
      "material_coverage": 0.0,
      "coverage_reason": "Short reason."
    }},
    "material_stage_omission": {{
      "material_omission_count": 0,
      "severe_material_omission_count": 0,
      "missing_material_stages": [
        "missing material stage 1",
        "missing material stage 2"
      ]
    }},
    "automation_boundary_quality": {{
      "manual_or_external_step_count": 0,
      "correctly_isolated_boundary_count": 0,
      "unsupported_as_automated_count": 0,
      "automation_boundary_score_5": 0.0,
      "boundary_reason": "Short reason."
    }},
    "application_overreach": {{
      "downstream_test_in_main_count": 0,
      "offline_analysis_in_main_count": 0,
      "optional_or_external_downstream_count": 0,
      "application_overreach_penalty_5": 0.0,
      "overreach_reason": "Short reason."
    }},
    "platform_adaptation_practicality": {{
      "platform_adaptation_practicality_score_20": 0.0,
      "practicality_reason": "Short reason."
    }},
    "automation_scope_fidelity": {{
      "automation_scope_fidelity_score_20": 0.0,
      "fidelity_reason": "Short reason."
    }},
    "branch_handling": {{
      "multi_branch_material_workflow": false,
      "branch_conflict_count": 0,
      "branch_handling_score_5": 0.0,
      "branch_reason": "Short reason."
    }},
    "main_strengths": [
      "strength 1",
      "strength 2"
    ],
    "main_weaknesses": [
      "weakness 1",
      "weakness 2"
    ]
  }},
  "protocol": {{
    "material_preparation_coverage": {{
      "required_material_stage_count": 0,
      "covered_material_stage_count": 0,
      "material_coverage": 0.0,
      "coverage_reason": "Short reason."
    }},
    "material_stage_omission": {{
      "material_omission_count": 0,
      "severe_material_omission_count": 0,
      "missing_material_stages": [
        "missing material stage 1",
        "missing material stage 2"
      ]
    }},
    "automation_boundary_quality": {{
      "manual_or_external_step_count": 0,
      "correctly_isolated_boundary_count": 0,
      "unsupported_as_automated_count": 0,
      "automation_boundary_score_5": 0.0,
      "boundary_reason": "Short reason."
    }},
    "application_overreach": {{
      "downstream_test_in_main_count": 0,
      "offline_analysis_in_main_count": 0,
      "optional_or_external_downstream_count": 0,
      "application_overreach_penalty_5": 0.0,
      "overreach_reason": "Short reason."
    }},
    "platform_adaptation_practicality": {{
      "platform_adaptation_practicality_score_20": 0.0,
      "practicality_reason": "Short reason."
    }},
    "automation_scope_fidelity": {{
      "automation_scope_fidelity_score_20": 0.0,
      "fidelity_reason": "Short reason."
    }},
    "branch_handling": {{
      "multi_branch_material_workflow": false,
      "branch_conflict_count": 0,
      "branch_handling_score_5": 0.0,
      "branch_reason": "Short reason."
    }},
    "main_strengths": [
      "strength 1",
      "strength 2"
    ],
    "main_weaknesses": [
      "weakness 1",
      "weakness 2"
    ]
  }},
  "comparison": {{
    "better_material_coverage": "origin_paper | protocol | tie",
    "fewer_material_omissions": "origin_paper | protocol | tie",
    "better_automation_boundary_quality": "origin_paper | protocol | tie",
    "less_application_overreach": "origin_paper | protocol | tie",
    "better_platform_adaptation_practicality": "origin_paper | protocol | tie",
    "better_automation_scope_fidelity": "origin_paper | protocol | tie",
    "better_branch_handling": "origin_paper | protocol | tie",
    "better_overall_for_automation_scope_material_workflow": "origin_paper | protocol | tie"
  }}
}}

Judgment rule:
- The winner should be based on better_overall_for_automation_scope_material_workflow.
- Material preparation coverage, platform practicality, and automation-scope fidelity are more important than paper coverage.
- Downstream application/testing/analysis should not help a plan win unless both plans define testing as the main automation target.
- A plan should not lose just because it omits downstream tests or offline analysis.
- A plan should be penalized if it mixes downstream tests or offline analysis into the main executable workflow.
- A plan should be rewarded for clearly separating optional/external/downstream steps from the material-preparation workflow.
""".strip()


def make_error_result(
    pair_id: int,
    status: str,
    error_message: str,
    origin_path: Optional[Path],
    protocol_path: Optional[Path],
) -> Dict[str, Any]:
    return {
        "_status": status,
        "pair_id": pair_id,
        "winner": "error",
        "winner_reason_short": error_message,
        "_origin_path": str(origin_path) if origin_path else None,
        "_protocol_path": str(protocol_path) if protocol_path else None,
        "_error": error_message,
    }


def evaluate_pair(pair_id: int, origin_path: Path, protocol_path: Path) -> Dict[str, Any]:
    origin_text = read_text(origin_path)
    protocol_text = read_text(protocol_path)
    final_prompt = build_eval_prompt(pair_id, origin_text, protocol_text)

    last_error = None
    last_content = None

    for attempt in range(1, 4):
        try:
            if USE_FAST_LLM:
                resp = fast_llm.invoke([HumanMessage(content=final_prompt)])
            else:
                resp = main_llm.invoke([HumanMessage(content=final_prompt)])

            content = getattr(resp, "content", None) or str(resp)
            last_content = content

            raw_path = RAW_DIR / f"pair_{pair_id}_attempt_{attempt}.txt"
            raw_path.write_text(content, encoding="utf-8")

            result = extract_json(content)
            result["_status"] = "ok"
            result["_origin_path"] = str(origin_path)
            result["_protocol_path"] = str(protocol_path)

            result = add_derived_scores(result)
            return result

        except Exception as e:
            last_error = e
            # 简单 backoff，避免并发时短暂限流导致所有 attempt 立刻失败
            time.sleep(1.5 * attempt)
            continue

    raw_debug_path = RAW_DIR / f"pair_{pair_id}_failed_last_output.txt"
    if last_content:
        raw_debug_path.write_text(last_content, encoding="utf-8")

    raise RuntimeError(f"Failed to evaluate pair {pair_id}: {last_error}")


def evaluate_pair_safe(pair_id: int, origin_file: Path, protocol_file: Path) -> Dict[str, Any]:
    """
    Wrapper for parallel execution.
    Always returns a result object, never raises.
    """
    try:
        print(f"[START] pair {pair_id}")
        result = evaluate_pair(pair_id, origin_file, protocol_file)
        print(f"[DONE] pair {pair_id}: winner={result.get('winner')}, derived={result.get('_derived_winner')}")
        return result
    except Exception as e:
        print(f"[ERROR] pair {pair_id}: {e}")
        return make_error_result(
            pair_id=pair_id,
            status="error",
            error_message=str(e),
            origin_path=origin_file,
            protocol_path=protocol_file,
        )


def get_nested(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(x: float, low: float, high: float) -> float:
    return max(low, min(high, x))


def join_list(xs):
    if isinstance(xs, list):
        return " | ".join(str(x) for x in xs)
    return ""


def compute_side_score(side: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automation-Scope Material Workflow Score.

    This score intentionally does NOT reward downstream application/testing coverage.
    """
    material_coverage = safe_float(
        get_nested(side, "material_preparation_coverage", "material_coverage"),
        default=None,
    )

    required_count = safe_int(
        get_nested(side, "material_preparation_coverage", "required_material_stage_count"),
        default=0,
    )
    covered_count = safe_int(
        get_nested(side, "material_preparation_coverage", "covered_material_stage_count"),
        default=0,
    )

    if material_coverage is None:
        if required_count > 0:
            material_coverage = covered_count / required_count
        else:
            material_coverage = 0.0

    material_coverage = clamp(material_coverage, 0.0, 1.0)

    boundary_5 = safe_float(
        get_nested(side, "automation_boundary_quality", "automation_boundary_score_5"),
        default=0.0,
    )
    boundary_norm = clamp(boundary_5 / 5.0, 0.0, 1.0)

    practicality_20 = safe_float(
        get_nested(side, "platform_adaptation_practicality", "platform_adaptation_practicality_score_20"),
        default=0.0,
    )
    practicality_norm = clamp(practicality_20 / 20.0, 0.0, 1.0)

    fidelity_20 = safe_float(
        get_nested(side, "automation_scope_fidelity", "automation_scope_fidelity_score_20"),
        default=0.0,
    )
    fidelity_norm = clamp(fidelity_20 / 20.0, 0.0, 1.0)

    branch_5 = safe_float(
        get_nested(side, "branch_handling", "branch_handling_score_5"),
        default=0.0,
    )
    branch_norm = clamp(branch_5 / 5.0, 0.0, 1.0)

    material_omission_count = safe_int(
        get_nested(side, "material_stage_omission", "material_omission_count"),
        default=0,
    )
    severe_material_omission_count = safe_int(
        get_nested(side, "material_stage_omission", "severe_material_omission_count"),
        default=0,
    )

    downstream_test_count = safe_int(
        get_nested(side, "application_overreach", "downstream_test_in_main_count"),
        default=0,
    )
    offline_analysis_count = safe_int(
        get_nested(side, "application_overreach", "offline_analysis_in_main_count"),
        default=0,
    )
    overreach_5 = safe_float(
        get_nested(side, "application_overreach", "application_overreach_penalty_5"),
        default=0.0,
    )
    overreach_norm = clamp(overreach_5 / 5.0, 0.0, 1.0)

    unsupported_as_automated_count = safe_int(
        get_nested(side, "automation_boundary_quality", "unsupported_as_automated_count"),
        default=0,
    )
    manual_external_count = safe_int(
        get_nested(side, "automation_boundary_quality", "manual_or_external_step_count"),
        default=0,
    )

    denom = max(required_count, 1)
    omission_penalty = clamp(
        (material_omission_count + 2 * severe_material_omission_count) / denom,
        0.0,
        1.0,
    )

    downstream_count_penalty = clamp(
        (downstream_test_count + offline_analysis_count) / 3.0,
        0.0,
        1.0,
    )

    unsupported_penalty = clamp(
        unsupported_as_automated_count / max(manual_external_count + 1, 1),
        0.0,
        1.0,
    )

    derived_score_100 = 100.0 * (
        0.30 * material_coverage
        + 0.20 * boundary_norm
        + 0.25 * practicality_norm
        + 0.20 * fidelity_norm
        + 0.05 * branch_norm
        - 0.12 * omission_penalty
        - 0.18 * overreach_norm
        - 0.12 * downstream_count_penalty
        - 0.08 * unsupported_penalty
    )

    return {
        "material_coverage": round(material_coverage, 4),
        "boundary_norm": round(boundary_norm, 4),
        "practicality_norm": round(practicality_norm, 4),
        "fidelity_norm": round(fidelity_norm, 4),
        "branch_norm": round(branch_norm, 4),
        "material_omission_penalty": round(omission_penalty, 4),
        "application_overreach_norm": round(overreach_norm, 4),
        "downstream_count_penalty": round(downstream_count_penalty, 4),
        "unsupported_penalty": round(unsupported_penalty, 4),
        "derived_score_100": round(clamp(derived_score_100, 0.0, 100.0), 2),
    }


def add_derived_scores(result: Dict[str, Any]) -> Dict[str, Any]:
    if result.get("_status") not in (None, "ok"):
        return result

    origin = result.get("origin_paper", {})
    protocol = result.get("protocol", {})

    origin_score = compute_side_score(origin)
    protocol_score = compute_side_score(protocol)

    result["_derived_scores"] = {
        "origin_paper": origin_score,
        "protocol": protocol_score,
    }

    o = origin_score["derived_score_100"]
    p = protocol_score["derived_score_100"]

    if abs(o - p) < 1e-6:
        derived_winner = "tie"
    elif p > o:
        derived_winner = "protocol"
    else:
        derived_winner = "origin_paper"

    result["_derived_winner"] = derived_winner
    return result


def flatten_for_csv(result: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "status": result.get("_status", "ok"),
        "pair_id": result.get("pair_id"),
        "llm_winner": result.get("winner"),
        "derived_winner": result.get("_derived_winner"),
        "winner_reason_short": result.get("winner_reason_short"),
        "origin_path": result.get("_origin_path"),
        "protocol_path": result.get("_protocol_path"),
        "error": result.get("_error"),
    }

    if result.get("_status") != "ok":
        return row

    basis = result.get("evaluation_basis", {})
    row.update({
        "inferred_material_preparation_stages": join_list(basis.get("inferred_material_preparation_stages", [])),
        "excluded_downstream_stages": join_list(basis.get("excluded_downstream_stages", [])),
        "evaluation_basis_notes": basis.get("notes"),
    })

    origin = result.get("origin_paper", {})
    protocol = result.get("protocol", {})
    comp = result.get("comparison", {})
    derived = result.get("_derived_scores", {})

    for side_name, obj in [("origin", origin), ("protocol", protocol)]:
        derived_side_key = "origin_paper" if side_name == "origin" else "protocol"
        dscore = derived.get(derived_side_key, {})

        row.update({
            f"{side_name}_required_material_stage_count": get_nested(obj, "material_preparation_coverage", "required_material_stage_count"),
            f"{side_name}_covered_material_stage_count": get_nested(obj, "material_preparation_coverage", "covered_material_stage_count"),
            f"{side_name}_material_coverage": get_nested(obj, "material_preparation_coverage", "material_coverage"),
            f"{side_name}_coverage_reason": get_nested(obj, "material_preparation_coverage", "coverage_reason"),

            f"{side_name}_material_omission_count": get_nested(obj, "material_stage_omission", "material_omission_count"),
            f"{side_name}_severe_material_omission_count": get_nested(obj, "material_stage_omission", "severe_material_omission_count"),
            f"{side_name}_missing_material_stages": join_list(get_nested(obj, "material_stage_omission", "missing_material_stages", default=[])),

            f"{side_name}_manual_or_external_step_count": get_nested(obj, "automation_boundary_quality", "manual_or_external_step_count"),
            f"{side_name}_correctly_isolated_boundary_count": get_nested(obj, "automation_boundary_quality", "correctly_isolated_boundary_count"),
            f"{side_name}_unsupported_as_automated_count": get_nested(obj, "automation_boundary_quality", "unsupported_as_automated_count"),
            f"{side_name}_automation_boundary_score_5": get_nested(obj, "automation_boundary_quality", "automation_boundary_score_5"),
            f"{side_name}_boundary_reason": get_nested(obj, "automation_boundary_quality", "boundary_reason"),

            f"{side_name}_downstream_test_in_main_count": get_nested(obj, "application_overreach", "downstream_test_in_main_count"),
            f"{side_name}_offline_analysis_in_main_count": get_nested(obj, "application_overreach", "offline_analysis_in_main_count"),
            f"{side_name}_optional_or_external_downstream_count": get_nested(obj, "application_overreach", "optional_or_external_downstream_count"),
            f"{side_name}_application_overreach_penalty_5": get_nested(obj, "application_overreach", "application_overreach_penalty_5"),
            f"{side_name}_overreach_reason": get_nested(obj, "application_overreach", "overreach_reason"),

            f"{side_name}_platform_adaptation_practicality_score_20": get_nested(obj, "platform_adaptation_practicality", "platform_adaptation_practicality_score_20"),
            f"{side_name}_practicality_reason": get_nested(obj, "platform_adaptation_practicality", "practicality_reason"),

            f"{side_name}_automation_scope_fidelity_score_20": get_nested(obj, "automation_scope_fidelity", "automation_scope_fidelity_score_20"),
            f"{side_name}_fidelity_reason": get_nested(obj, "automation_scope_fidelity", "fidelity_reason"),

            f"{side_name}_multi_branch_material_workflow": get_nested(obj, "branch_handling", "multi_branch_material_workflow"),
            f"{side_name}_branch_conflict_count": get_nested(obj, "branch_handling", "branch_conflict_count"),
            f"{side_name}_branch_handling_score_5": get_nested(obj, "branch_handling", "branch_handling_score_5"),
            f"{side_name}_branch_reason": get_nested(obj, "branch_handling", "branch_reason"),

            f"{side_name}_derived_score_100": dscore.get("derived_score_100"),
            f"{side_name}_derived_material_omission_penalty": dscore.get("material_omission_penalty"),
            f"{side_name}_derived_application_overreach_norm": dscore.get("application_overreach_norm"),
            f"{side_name}_derived_downstream_count_penalty": dscore.get("downstream_count_penalty"),
            f"{side_name}_derived_unsupported_penalty": dscore.get("unsupported_penalty"),

            f"{side_name}_strengths": join_list(obj.get("main_strengths", [])),
            f"{side_name}_weaknesses": join_list(obj.get("main_weaknesses", [])),
        })

    row.update({
        "better_material_coverage": comp.get("better_material_coverage"),
        "fewer_material_omissions": comp.get("fewer_material_omissions"),
        "better_automation_boundary_quality": comp.get("better_automation_boundary_quality"),
        "less_application_overreach": comp.get("less_application_overreach"),
        "better_platform_adaptation_practicality": comp.get("better_platform_adaptation_practicality"),
        "better_automation_scope_fidelity": comp.get("better_automation_scope_fidelity"),
        "better_branch_handling": comp.get("better_branch_handling"),
        "better_overall_for_automation_scope_material_workflow": comp.get("better_overall_for_automation_scope_material_workflow"),
    })

    return row


def save_jsonl_results(results: List[Dict[str, Any]]) -> None:
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


def save_pretty_json(results: List[Dict[str, Any]]) -> None:
    with PRETTY_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def collect_pair_files() -> List[Tuple[int, Optional[Path], Optional[Path]]]:
    pairs = []
    for i in range(1, MAX_PAIRS + 1):
        origin_dir = ROOT_DIR / "logs" / f"mof-origin_paper-{i}"
        protocol_dir = ROOT_DIR / "logs" / f"mof-protocol-{i}"

        origin_file = find_final_plan_file(origin_dir)
        protocol_file = find_final_plan_file(protocol_dir)

        pairs.append((i, origin_file, protocol_file))

    return pairs


def main():
    all_results: List[Dict[str, Any]] = []
    futures = {}

    pairs = collect_pair_files()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for pair_id, origin_file, protocol_file in pairs:
            if origin_file is None or protocol_file is None:
                result = make_error_result(
                    pair_id=pair_id,
                    status="missing_file",
                    error_message="Missing final plan file.",
                    origin_path=origin_file,
                    protocol_path=protocol_file,
                )
                all_results.append(result)
                print(f"[MISSING] pair {pair_id}: origin={origin_file}, protocol={protocol_file}")
                continue

            print(f"[SUBMIT] pair {pair_id}")
            print(f"  origin:   {origin_file}")
            print(f"  protocol: {protocol_file}")

            future = executor.submit(evaluate_pair_safe, pair_id, origin_file, protocol_file)
            futures[future] = pair_id

        for future in as_completed(futures):
            pair_id = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = make_error_result(
                    pair_id=pair_id,
                    status="error",
                    error_message=str(e),
                    origin_path=None,
                    protocol_path=None,
                )

            all_results.append(result)

            if result.get("_status") == "ok":
                derived = result.get("_derived_scores", {})
                origin_d = derived.get("origin_paper", {})
                protocol_d = derived.get("protocol", {})

                print(
                    f"[RESULT] pair {pair_id} | "
                    f"llm_winner={result.get('winner')} | "
                    f"derived_winner={result.get('_derived_winner')} | "
                    f"origin_score={origin_d.get('derived_score_100')} | "
                    f"protocol_score={protocol_d.get('derived_score_100')} | "
                    f"origin_mat_cov={origin_d.get('material_coverage')} | "
                    f"protocol_mat_cov={protocol_d.get('material_coverage')} | "
                    f"origin_overreach={origin_d.get('application_overreach_norm')} | "
                    f"protocol_overreach={protocol_d.get('application_overreach_norm')}"
                )
            else:
                print(f"[RESULT] pair {pair_id} | status={result.get('_status')} | error={result.get('_error')}")

    # Sort results by pair_id for stable JSON/CSV output.
    all_results = sorted(all_results, key=lambda x: x.get("pair_id", 999999))

    if all_results:
        rows = [flatten_for_csv(r) for r in all_results]
        fieldnames = sorted({k for row in rows for k in row.keys()})

        with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        save_jsonl_results(all_results)
        save_pretty_json(all_results)

        print(f"\nSaved JSONL to:       {JSONL_PATH}")
        print(f"Saved pretty JSON to: {PRETTY_JSON_PATH}")
        print(f"Saved CSV to:         {CSV_PATH}")

        summarize(all_results)


def summarize(results: List[Dict[str, Any]]):
    ok_results = [r for r in results if r.get("_status") == "ok"]
    failed_results = [r for r in results if r.get("_status") != "ok"]

    n_total = len(results)
    n_ok = len(ok_results)

    llm_winner_counts = {"origin_paper": 0, "protocol": 0, "tie": 0}
    derived_winner_counts = {"origin_paper": 0, "protocol": 0, "tie": 0}

    comparison_counts = {
        "better_material_coverage": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "fewer_material_omissions": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "better_automation_boundary_quality": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "less_application_overreach": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "better_platform_adaptation_practicality": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "better_automation_scope_fidelity": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "better_branch_handling": {"origin_paper": 0, "protocol": 0, "tie": 0},
        "better_overall_for_automation_scope_material_workflow": {"origin_paper": 0, "protocol": 0, "tie": 0},
    }

    metrics = {
        "origin_derived_score": [],
        "protocol_derived_score": [],
        "origin_material_coverage": [],
        "protocol_material_coverage": [],
        "origin_material_omission": [],
        "protocol_material_omission": [],
        "origin_severe_material_omission": [],
        "protocol_severe_material_omission": [],
        "origin_boundary": [],
        "protocol_boundary": [],
        "origin_overreach": [],
        "protocol_overreach": [],
        "origin_downstream_main": [],
        "protocol_downstream_main": [],
        "origin_analysis_main": [],
        "protocol_analysis_main": [],
        "origin_practicality": [],
        "protocol_practicality": [],
        "origin_fidelity": [],
        "protocol_fidelity": [],
        "origin_branch": [],
        "protocol_branch": [],
    }

    def add_metric(name, value):
        if isinstance(value, (int, float)):
            metrics[name].append(value)

    for r in ok_results:
        llm_winner = r.get("winner", "tie")
        llm_winner_counts[llm_winner] = llm_winner_counts.get(llm_winner, 0) + 1

        derived_winner = r.get("_derived_winner", "tie")
        derived_winner_counts[derived_winner] = derived_winner_counts.get(derived_winner, 0) + 1

        comp = r.get("comparison", {})
        for key, counter in comparison_counts.items():
            val = comp.get(key, "tie")
            counter[val] = counter.get(val, 0) + 1

        origin = r.get("origin_paper", {})
        protocol = r.get("protocol", {})
        derived = r.get("_derived_scores", {})

        add_metric("origin_derived_score", get_nested(derived, "origin_paper", "derived_score_100"))
        add_metric("protocol_derived_score", get_nested(derived, "protocol", "derived_score_100"))

        add_metric("origin_material_coverage", get_nested(origin, "material_preparation_coverage", "material_coverage"))
        add_metric("protocol_material_coverage", get_nested(protocol, "material_preparation_coverage", "material_coverage"))

        add_metric("origin_material_omission", get_nested(origin, "material_stage_omission", "material_omission_count"))
        add_metric("protocol_material_omission", get_nested(protocol, "material_stage_omission", "material_omission_count"))

        add_metric("origin_severe_material_omission", get_nested(origin, "material_stage_omission", "severe_material_omission_count"))
        add_metric("protocol_severe_material_omission", get_nested(protocol, "material_stage_omission", "severe_material_omission_count"))

        add_metric("origin_boundary", get_nested(origin, "automation_boundary_quality", "automation_boundary_score_5"))
        add_metric("protocol_boundary", get_nested(protocol, "automation_boundary_quality", "automation_boundary_score_5"))

        add_metric("origin_overreach", get_nested(origin, "application_overreach", "application_overreach_penalty_5"))
        add_metric("protocol_overreach", get_nested(protocol, "application_overreach", "application_overreach_penalty_5"))

        add_metric("origin_downstream_main", get_nested(origin, "application_overreach", "downstream_test_in_main_count"))
        add_metric("protocol_downstream_main", get_nested(protocol, "application_overreach", "downstream_test_in_main_count"))

        add_metric("origin_analysis_main", get_nested(origin, "application_overreach", "offline_analysis_in_main_count"))
        add_metric("protocol_analysis_main", get_nested(protocol, "application_overreach", "offline_analysis_in_main_count"))

        add_metric("origin_practicality", get_nested(origin, "platform_adaptation_practicality", "platform_adaptation_practicality_score_20"))
        add_metric("protocol_practicality", get_nested(protocol, "platform_adaptation_practicality", "platform_adaptation_practicality_score_20"))

        add_metric("origin_fidelity", get_nested(origin, "automation_scope_fidelity", "automation_scope_fidelity_score_20"))
        add_metric("protocol_fidelity", get_nested(protocol, "automation_scope_fidelity", "automation_scope_fidelity_score_20"))

        add_metric("origin_branch", get_nested(origin, "branch_handling", "branch_handling_score_5"))
        add_metric("protocol_branch", get_nested(protocol, "branch_handling", "branch_handling_score_5"))

    def avg(xs):
        return sum(xs) / len(xs) if xs else None

    def rate(count, denom):
        return count / denom if denom else 0

    print("\n===== Summary =====")
    print(f"Expected pairs: {n_total}")
    print(f"Successfully evaluated pairs: {n_ok}")
    print(f"Failed / missing pairs: {len(failed_results)}")

    if failed_results:
        print("Failed pair IDs:", [r.get("pair_id") for r in failed_results])

    print("\n--- LLM Winner Counts ---")
    print(f"LLM winner counts: {llm_winner_counts}")
    print(f"Protocol LLM win rate among evaluated pairs: {rate(llm_winner_counts.get('protocol', 0), n_ok):.2%}")
    print(f"Origin LLM win rate among evaluated pairs:   {rate(llm_winner_counts.get('origin_paper', 0), n_ok):.2%}")
    print(f"Tie LLM rate among evaluated pairs:          {rate(llm_winner_counts.get('tie', 0), n_ok):.2%}")

    print("\n--- Derived Winner Counts ---")
    print(f"Derived winner counts: {derived_winner_counts}")
    print(f"Protocol derived win rate among evaluated pairs: {rate(derived_winner_counts.get('protocol', 0), n_ok):.2%}")
    print(f"Origin derived win rate among evaluated pairs:   {rate(derived_winner_counts.get('origin_paper', 0), n_ok):.2%}")
    print(f"Tie derived rate among evaluated pairs:          {rate(derived_winner_counts.get('tie', 0), n_ok):.2%}")

    print("\n--- Derived Score ---")
    print(f"Origin avg derived score_100:   {avg(metrics['origin_derived_score'])}")
    print(f"Protocol avg derived score_100: {avg(metrics['protocol_derived_score'])}")

    print("\n--- Material Preparation Coverage ---")
    print(f"Origin avg material coverage:   {avg(metrics['origin_material_coverage'])}")
    print(f"Protocol avg material coverage: {avg(metrics['protocol_material_coverage'])}")
    print(f"Better material coverage counts: {comparison_counts['better_material_coverage']}")

    print("\n--- Material Stage Omissions ---")
    print(f"Origin avg material omission count:   {avg(metrics['origin_material_omission'])}")
    print(f"Protocol avg material omission count: {avg(metrics['protocol_material_omission'])}")
    print(f"Origin avg severe material omission count:   {avg(metrics['origin_severe_material_omission'])}")
    print(f"Protocol avg severe material omission count: {avg(metrics['protocol_severe_material_omission'])}")
    print(f"Fewer material omissions counts: {comparison_counts['fewer_material_omissions']}")

    print("\n--- Automation Boundary Quality ---")
    print(f"Origin avg boundary score_5:   {avg(metrics['origin_boundary'])}")
    print(f"Protocol avg boundary score_5: {avg(metrics['protocol_boundary'])}")
    print(f"Better automation boundary quality counts: {comparison_counts['better_automation_boundary_quality']}")

    print("\n--- Application Overreach ---")
    print(f"Origin avg application overreach penalty_5:   {avg(metrics['origin_overreach'])}")
    print(f"Protocol avg application overreach penalty_5: {avg(metrics['protocol_overreach'])}")
    print(f"Origin avg downstream tests in main workflow:   {avg(metrics['origin_downstream_main'])}")
    print(f"Protocol avg downstream tests in main workflow: {avg(metrics['protocol_downstream_main'])}")
    print(f"Origin avg offline analysis in main workflow:   {avg(metrics['origin_analysis_main'])}")
    print(f"Protocol avg offline analysis in main workflow: {avg(metrics['protocol_analysis_main'])}")
    print(f"Less application overreach counts: {comparison_counts['less_application_overreach']}")

    print("\n--- Platform Adaptation Practicality ---")
    print(f"Origin avg practicality score_20:   {avg(metrics['origin_practicality'])}")
    print(f"Protocol avg practicality score_20: {avg(metrics['protocol_practicality'])}")
    print(f"Better platform adaptation practicality counts: {comparison_counts['better_platform_adaptation_practicality']}")

    print("\n--- Automation-Scope Fidelity ---")
    print(f"Origin avg automation-scope fidelity score_20:   {avg(metrics['origin_fidelity'])}")
    print(f"Protocol avg automation-scope fidelity score_20: {avg(metrics['protocol_fidelity'])}")
    print(f"Better automation-scope fidelity counts: {comparison_counts['better_automation_scope_fidelity']}")

    print("\n--- Branch Handling ---")
    print(f"Origin avg branch handling score_5:   {avg(metrics['origin_branch'])}")
    print(f"Protocol avg branch handling score_5: {avg(metrics['protocol_branch'])}")
    print(f"Better branch handling counts: {comparison_counts['better_branch_handling']}")

    print("\n--- Overall Automation-Scope Material Workflow ---")
    print(f"Better overall counts: {comparison_counts['better_overall_for_automation_scope_material_workflow']}")


if __name__ == "__main__":
    main()