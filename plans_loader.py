import os
import json

PLAN_DIR = "configs"

def load_plan_data(plan_id: str) -> dict:
    file_path = os.path.join(PLAN_DIR, f"{plan_id}.json")
    if not os.path.exists(file_path):
        print(f"[載入錯誤] 找不到課程檔案：{file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[載入成功] 已載入 {plan_id} 課程內容，共 {len(data.get('tasks', []))} 筆任務")
            return data
    except Exception as e:
        print(f"[錯誤] 載入 {plan_id} 時發生錯誤: {e}")
        return None
