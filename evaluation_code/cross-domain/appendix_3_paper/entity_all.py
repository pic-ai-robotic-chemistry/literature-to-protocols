import json
import math
from statistics import mean, stdev
from scipy.stats import t

try:
    import pandas as pd
    USE_PANDAS = True
except ImportError:
    USE_PANDAS = False


SUBJECTS = ["cof", "mof", "ows"]


def round4(x):
    if isinstance(x, float):
        return round(x, 4)
    return x


def count_covered(entity_dict: dict, covered_list):
    cnt_absent = 0
    cnt_list = [0 for _ in covered_list]

    for index, protocol in enumerate(covered_list):
        if entity_dict[protocol] == 'absent':
            cnt_absent += 1
        else:
            cnt_list[index] += 1

    if cnt_absent == len(covered_list):
        return 0, None
    else:
        return 1, cnt_list


def calc_mean_std_ci(vals):
    n = len(vals)

    if n > 1:
        m = mean(vals)
        s = stdev(vals)
        se = s / math.sqrt(n)
        t_crit = t.ppf(0.975, df=n - 1)
        ci_low = m - t_crit * se
        ci_high = m + t_crit * se
    elif n == 1:
        m = vals[0]
        s = 0.0
        ci_low = m
        ci_high = m
    else:
        m = 0.0
        s = 0.0
        ci_low = 0.0
        ci_high = 0.0

    return (
        round4(m),
        round4(s),
        round4(ci_low),
        round4(ci_high),
        n
    )


def process_subject(subject):
    covered_list = ['Protocol1', 'Protocol2']

    acc_path = f"./appendix_3_paper/entity_acc/entities_acc_{subject}.json"
    recall_path = f"./appendix_3_paper/entity_complete/result/entity_complete_{subject}.json"

    with open(acc_path, "r", encoding="utf-8") as f:
        acc_data = json.load(f)

    with open(recall_path, "r", encoding="utf-8") as f:
        recall_data = json.load(f)

    # =========================================================
    # 1. Precision: overall + per paper
    # =========================================================
    precision_per_paper = {}
    precision_counts = {}

    for paper_idx, paper_data in enumerate(acc_data):
        precision_per_paper[paper_idx] = {}
        for method in paper_data:
            method_idx = method["method_index"]
            total = method["total_entities"]
            true = method["true_entities"]

            precision = true / total if total > 0 else 0.0
            precision_per_paper[paper_idx][method_idx] = precision

            if method_idx not in precision_counts:
                precision_counts[method_idx] = {
                    "total_entities": 0,
                    "true_entities": 0
                }

            precision_counts[method_idx]["total_entities"] += total
            precision_counts[method_idx]["true_entities"] += true

    overall_precision = {}
    for method_idx, cnts in precision_counts.items():
        total = cnts["total_entities"]
        true = cnts["true_entities"]
        overall_precision[method_idx] = round4(true / total if total > 0 else 0.0)

    # =========================================================
    # 2. Recall: overall + per paper
    # =========================================================
    recall_per_paper = {}
    recall_counts = {
        0: {"total_entities": 0, "covered_entities": 0},
        1: {"total_entities": 0, "covered_entities": 0}
    }

    for paper_idx, paper_result in enumerate(recall_data):
        paper_list = []
        count = 0

        for x in paper_result["results"]:
            for _, v in x.items():
                cover, cnt_list = count_covered(v, covered_list)
                if cover:
                    count += 1
                    if paper_list == []:
                        paper_list = cnt_list
                    else:
                        paper_list = [a + b for a, b in zip(paper_list, cnt_list)]

        recall_per_paper[paper_idx] = {}

        if count > 0:
            recall_per_paper[paper_idx][0] = paper_list[0] / count
            recall_per_paper[paper_idx][1] = paper_list[1] / count

            recall_counts[0]["total_entities"] += count
            recall_counts[1]["total_entities"] += count

            recall_counts[0]["covered_entities"] += paper_list[0]
            recall_counts[1]["covered_entities"] += paper_list[1]
        else:
            recall_per_paper[paper_idx][0] = 0.0
            recall_per_paper[paper_idx][1] = 0.0

    overall_recall = {}
    for method_idx, cnts in recall_counts.items():
        total = cnts["total_entities"]
        covered = cnts["covered_entities"]
        overall_recall[method_idx] = round4(covered / total if total > 0 else 0.0)

    # =========================================================
    # 3. 整合 Precision / Recall / F1
    # =========================================================
    results = []

    common_papers = sorted(set(precision_per_paper.keys()) & set(recall_per_paper.keys()))
    common_methods = sorted(set(precision_counts.keys()) & set(recall_counts.keys()))

    for method_idx in common_methods:
        p_overall = overall_precision[method_idx]
        r_overall = overall_recall[method_idx]
        f1_overall = round4(2 * p_overall * r_overall / (p_overall + r_overall) if (p_overall + r_overall) > 0 else 0.0)

        p_vals = []
        r_vals = []
        f1_vals = []

        for paper_idx in common_papers:
            if method_idx not in precision_per_paper[paper_idx]:
                continue
            if method_idx not in recall_per_paper[paper_idx]:
                continue

            p = precision_per_paper[paper_idx][method_idx]
            r = recall_per_paper[paper_idx][method_idx]
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

            p_vals.append(p)
            r_vals.append(r)
            f1_vals.append(f1)

        p_mean, p_std, p_ci_low, p_ci_high, n_p = calc_mean_std_ci(p_vals)
        r_mean, r_std, r_ci_low, r_ci_high, n_r = calc_mean_std_ci(r_vals)
        f1_mean, f1_std, f1_ci_low, f1_ci_high, n_f1 = calc_mean_std_ci(f1_vals)

        results.append({
            "subject": subject,
            "method": method_idx,

            "precision_total_entities": precision_counts[method_idx]["total_entities"],
            "precision_true_entities": precision_counts[method_idx]["true_entities"],

            "recall_total_entities": recall_counts[method_idx]["total_entities"],
            "recall_covered_entities": recall_counts[method_idx]["covered_entities"],

            "overall_precision": p_overall,
            "overall_recall": r_overall,
            "overall_f1": f1_overall,

            "paper_precision_mean": p_mean,
            "paper_precision_std": p_std,
            "paper_precision_ci_low": p_ci_low,
            "paper_precision_ci_high": p_ci_high,

            "paper_recall_mean": r_mean,
            "paper_recall_std": r_std,
            "paper_recall_ci_low": r_ci_low,
            "paper_recall_ci_high": r_ci_high,

            "paper_f1_mean": f1_mean,
            "paper_f1_std": f1_std,
            "paper_f1_ci_low": f1_ci_low,
            "paper_f1_ci_high": f1_ci_high,

            "n_papers": min(n_p, n_r, n_f1)
        })

    return results


def main():
    all_results = []

    for subject in SUBJECTS:
        subject_results = process_subject(subject)
        all_results.extend(subject_results)

    print("=== Final integrated statistics ===")
    for item in all_results:
        print(f"\n[{item['subject']}] Method {item['method']}")
        print(f"  Precision counts       : true={item['precision_true_entities']}, total={item['precision_total_entities']}")
        print(f"  Recall counts          : covered={item['recall_covered_entities']}, total={item['recall_total_entities']}")
        print(f"  Overall Precision      : {item['overall_precision']:.4f}")
        print(f"  Overall Recall         : {item['overall_recall']:.4f}")
        print(f"  Overall F1             : {item['overall_f1']:.4f}")
        print(f"  Paper Precision Mean   : {item['paper_precision_mean']:.4f}")
        print(f"  Paper Precision Std    : {item['paper_precision_std']:.4f}")
        print(f"  Paper Precision 95% CI : [{item['paper_precision_ci_low']:.4f}, {item['paper_precision_ci_high']:.4f}]")
        print(f"  Paper Recall Mean      : {item['paper_recall_mean']:.4f}")
        print(f"  Paper Recall Std       : {item['paper_recall_std']:.4f}")
        print(f"  Paper Recall 95% CI    : [{item['paper_recall_ci_low']:.4f}, {item['paper_recall_ci_high']:.4f}]")
        print(f"  Paper F1 Mean          : {item['paper_f1_mean']:.4f}")
        print(f"  Paper F1 Std           : {item['paper_f1_std']:.4f}")
        print(f"  Paper F1 95% CI        : [{item['paper_f1_ci_low']:.4f}, {item['paper_f1_ci_high']:.4f}]")
        print(f"  N papers               : {item['n_papers']}")

    json_path = "./appendix_3_paper/integrated_metrics_all.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {json_path}")

    if USE_PANDAS:
        df = pd.DataFrame(all_results)
        csv_path = "./appendix_3_paper/integrated_metrics_all.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"Saved to {csv_path}")


if __name__ == "__main__":
    main()