import json
import math
from statistics import mean, stdev
from scipy.stats import t

subject = "cof"
# subject = "mof"
# subject = "ows"

with open(f"./appendix_3_paper/entity_complete/result/entity_complete_{subject}.json", "r", encoding="utf-8") as f:
    result_list = json.load(f)

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

all_cnt = 0
all_paper_list = []
paper_ratios = []

for paper_result in result_list:
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

    all_cnt += count
    all_paper_list = [a + b for a, b in zip(paper_list, all_paper_list)] if all_paper_list != [] else paper_list

    if count > 0:
        paper_ratios.append([x / count for x in paper_list])

overall_means = [round(x / all_cnt, 4) for x in all_paper_list]
print("Overall mean ratios:", overall_means)
print("All covered entities:", all_cnt)
print("Protocol counts:", all_paper_list)

protocol_names = ['Protocol1', 'Protocol2']
n = len(paper_ratios)

print(f"\nNumber of papers used for statistics: {n}")

for i, protocol in enumerate(protocol_names):
    vals = [x[i] for x in paper_ratios]

    m = mean(vals)
    s = stdev(vals) if n > 1 else 0.0
    se = s / math.sqrt(n) if n > 1 else 0.0

    if n > 1:
        t_crit = t.ppf(0.975, df=n - 1)
        ci_low = m - t_crit * se
        ci_high = m + t_crit * se
    else:
        ci_low, ci_high = m, m

    print(f"\n{protocol}")
    print(f"Mean     : {m:.4f}")
    print(f"Std      : {s:.4f}")
    print(f"95% CI   : [{ci_low:.4f}, {ci_high:.4f}]")