import json
def aggregate_method_stats(data):
    # 初始化结果列表，假设方法索引从0开始连续编号
    result = []
    # 遍历所有论文的数据
    for paper_data in data:
        # 处理单篇论文中的每个方法
        for method in paper_data:
            method_index = method['method_index']
            total = method['total_entities']
            true = method['true_entities']
            
            # 检查该方法是否已在结果列表中
            found = False
            for item in result:
                if item['method'] == method_index:
                    # 如果已存在，累加数值
                    item['total'] += total
                    item['true'] += true
                    found = True
                    break
            
            # 如果该方法不存在，添加新条目
            if not found:
                result.append({
                    'method': method_index,
                    'total': total,
                    'true': true
                })
    
    # 按方法索引排序结果
    result.sort(key=lambda x: x['method'])
    
    return result

# with open("entities_acc_4o_mini.json","r") as f:
# subject = "cof"
# subject = "mof"
subject = "ows"
with open(f"./appendix_3_paper/entity_acc/entities_acc_{subject}.json", "r", encoding="utf-8") as f:
    data = json.load(f)
aggregated = aggregate_method_stats(data)

# 打印结果
for item in aggregated:
    print(f"方法 {item['method']}: 总实体数={item['total']}, 正确实体数={item['true']},准确率：{round(item['true']/item['total'], 4)}")