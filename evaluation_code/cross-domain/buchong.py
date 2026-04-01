from appendix_3_paper.pure_simple_gpt_buchong import main
import concurrent.futures

if __name__=="__main__":
    # 1. 构建所有待执行的任务参数
    tasks = []
    for num in range(1, 21):
        for subject in ["cof", "mof", "ows"]:
            tasks.append((num, subject))  # 每个元素是 (num, subject)

    # 2. 并行执行（根据任务类型选择 Executor）
    # IO 密集型 → ThreadPoolExecutor；CPU 密集型 → ProcessPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # 提交所有任务并获取 Future 对象
        futures = [executor.submit(main, num, subject) for num, subject in tasks]

        # 3. 可选：等待所有任务完成，并捕获异常（避免单个任务崩溃影响全局）
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # 获取 main 函数的返回值（如果有）
            except Exception as e:
                print(f"任务执行失败: {e}")