from appendix_3_paper.entity_eval_para import *

if __name__=="__main__":
    # main(1)
    saving_dir = f"./appendix_3_paper/entity_acc/entities_acc_{subject}.json"
    for id in range(1, 21):
        if not is_json_file_empty(saving_dir):
            with open(saving_dir, "r", encoding="utf-8") as f:
                result_list = json.load(f)
                if check_paper_id_exists(result_list, id):
                    print(f"{id}文章评估完成，skipping....")
                    continue
        print(f"开始评估{subject},{id}....")
        main(id, subject=subject,saving_dir=saving_dir)