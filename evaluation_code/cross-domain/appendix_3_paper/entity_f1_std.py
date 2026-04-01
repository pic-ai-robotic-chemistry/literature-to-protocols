import json
import math
from statistics import mean, stdev
from scipy.stats import t
subject = "cof"
# subject = "mof"
# subject = "ows"

# -----------------------------
# 1. 读取 precision 数据
# -----------------------------
with open(f"./appendix_3_paper/entity_acc/entities_acc_{subject}.json", "r", encoding="utf-8") as f:
    acc_data = json.load(f)

# -----------------------------
# 2. 读取 recall 数据
# -----------------------------
with open(f"./appendix_3_paper/entity_complete/result/entity_complete_{subject}.json", "r", encoding="utf-8") as f:
    recall_data = json.load(f)


# =========================================================
# Part A: 把 precision 整理成
# precision_per_paper[paper_idx][method_idx] = precision
# =========================================================
precision_per_paper = {}

for paper_idx, paper_data in enumerate(acc_data):
    precision_per_paper[paper_idx] = {}
    for method in paper_data:
        method_idx = method["method_index"]
        total = method["total_entities"]
        true = method["true_entities"]
        precision = true / total if total > 0 else 0.0
        precision_per_paper[paper_idx][method_idx] = precision


# =========================================================
# Part B: 把 recall 整理成
# recall_per_paper[paper_idx][method_idx] = recall
#
# 注意：这里需要你根据你 recall json 的真实 method 对应关系修改
# 下面先按你之前的 Protocol1 / Protocol2 来写：
# 假设 method 0 -> Protocol1, method 1 -> Protocol2
# =========================================================
def count_covered(entity_dict: dict):
    covered_list = ['Protocol1', 'Protocol2']
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

recall_per_paper = {}

for paper_idx, paper_result in enumerate(recall_data):
    paper_list = []
    count = 0

    for x in paper_result["results"]:
        for k, v in x.items():
            cover, cnt_list = count_covered(v)
            if cover:
                count += 1
                if paper_list == []:
                    paper_list = cnt_list
                else:
                    paper_list = [a + b for a, b in zip(paper_list, cnt_list)]

    # Protocol1 -> method 0, Protocol2 -> method 1
    recall_per_paper[paper_idx] = {}
    if count > 0:
        recall_per_paper[paper_idx][0] = paper_list[0] / count
        recall_per_paper[paper_idx][1] = paper_list[1] / count
    else:
        recall_per_paper[paper_idx][0] = 0.0
        recall_per_paper[paper_idx][1] = 0.0


# =========================================================
# Part C: 逐篇逐方法计算 F1
# =========================================================
f1_per_method = {}   # {method_idx: [f1_paper1, f1_paper2, ...]}

common_papers = sorted(set(precision_per_paper.keys()) & set(recall_per_paper.keys()))

for paper_idx in common_papers:
    common_methods = sorted(
        set(precision_per_paper[paper_idx].keys()) &
        set(recall_per_paper[paper_idx].keys())
    )
    for method_idx in common_methods:
        p = precision_per_paper[paper_idx][method_idx]
        r = recall_per_paper[paper_idx][method_idx]

        if p + r == 0:
            f1 = 0.0
        else:
            f1 = 2 * p * r / (p + r)

        f1_per_method.setdefault(method_idx, []).append(f1)


# =========================================================
# Part D: 统计 mean / std / 95% CI
# =========================================================
for method_idx in sorted(f1_per_method.keys()):
    vals = f1_per_method[method_idx]
    n = len(vals)

    m = mean(vals)
    s = stdev(vals) if n > 1 else 0.0
    se = s / math.sqrt(n) if n > 1 else 0.0

    if n > 1:
        t_crit = t.ppf(0.975, df=n - 1)
        ci_low = m - t_crit * se
        ci_high = m + t_crit * se
    else:
        ci_low = ci_high = m

    print(
        f"Method {method_idx}: "
        f"F1 mean={m:.4f}, std={s:.4f}, 95% CI=[{ci_low:.4f}, {ci_high:.4f}], n={n}"
    )