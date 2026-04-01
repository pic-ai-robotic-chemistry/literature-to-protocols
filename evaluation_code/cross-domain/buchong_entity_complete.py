from appendix_3_paper.entity_complete_2 import *

if __name__=="__main__":
    saving_dir = f"./appendix_3_paper/entity_complete/result/entity_complete_{subject}.json"
    for id in range(1,21):
        if not is_json_file_empty(saving_dir):
            with open(saving_dir, "r", encoding="utf-8") as f:
                result_list = json.load(f)
                if check_paper_id_exists(result_list, id):
                    print(f"{id}文章评估完成，skipping....")
                    continue
            
        print(f"正在处理{subject}, {id}...")
        main(id, saving_dir)