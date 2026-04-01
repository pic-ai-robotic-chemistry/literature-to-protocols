import json
import math
from statistics import mean, stdev
from scipy.stats import t

def aggregate_method_stats(data):
    result = []
    for paper_data in data:
        for method in paper_data:
            method_index = method['method_index']
            total = method['total_entities']
            true = method['true_entities']

            found = False
            for item in result:
                if item['method'] == method_index:
                    item['total'] += total
                    item['true'] += true
                    found = True
                    break

            if not found:
                result.append({
                    'method': method_index,
                    'total': total,
                    'true': true
                })

    result.sort(key=lambda x: x['method'])
    return result

def collect_method_acc_per_paper(data):
    """
    收集每个 method 在每篇论文上的 accuracy
    返回:
        {
            method_index: [acc_paper1, acc_paper2, ...]
        }
    """
    method_accs = {}

    for paper_data in data:
        for method in paper_data:
            method_index = method['method_index']
            total = method['total_entities']
            true = method['true_entities']

            if total == 0:
                continue

            acc = true / total
            method_accs.setdefault(method_index, []).append(acc)

    return method_accs

# with open("entities_acc_4o_mini.json","r") as f:
# subject = "cof"
# subject = "mof"
subject = "ows"

with open(f"./appendix_3_paper/entity_acc/entities_acc_{subject}.json", "r", encoding="utf-8") as f:
    data = json.load(f)

aggregated = aggregate_method_stats(data)
method_accs = collect_method_acc_per_paper(data)

# 打印结果
for item in aggregated:
    method_idx = item['method']
    total = item['total']
    true = item['true']
    overall_acc = true / total if total > 0 else 0.0

    vals = method_accs.get(method_idx, [])
    n = len(vals)

    if n > 1:
        m = mean(vals)
        s = stdev(vals)                 # 样本标准差
        se = s / math.sqrt(n)
        t_crit = t.ppf(0.975, df=n - 1) # 95% CI
        ci_low = m - t_crit * se
        ci_high = m + t_crit * se
    elif n == 1:
        m = vals[0]
        s = 0.0
        ci_low = ci_high = m
    else:
        m = 0.0
        s = 0.0
        ci_low = ci_high = 0.0

    print(
        f"方法 {method_idx}: "
        f"总实体数={total}, "
        f"正确实体数={true}, "
        f"总体准确率={overall_acc:.4f}, "
        f"按论文平均准确率={m:.4f}, "
        f"标准差={s:.4f}, "
        f"95%CI=[{ci_low:.4f}, {ci_high:.4f}], "
        f"n={n}"
    )