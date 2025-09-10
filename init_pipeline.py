# init_pipeline.py (最小可運行版)

from datetime import datetime

try:
    from plans_loader import load_plan
except ImportError:
    print("[WARNING] plans_loader 模組缺失，使用 dummy load_plan")
    def load_plan(plan_id):
        return {"tasks": []}  # 假資料，避免 ImportError

# 暫時把其他功能註解掉
# from student_sheet_logic import init_student_sheet
# from drive_logic import create_student_drive_folder
# from whitelist import get_user_plan_list
# from sheets_logic import get_student_identity_from_basic_sheet


def init_plan_for_student(user_id, plan_id="Plan_A", base_date: datetime = None):
    print(f"[init_plan_for_student] (dummy) user={user_id}, plan={plan_id}")
    return True


def init_plan_list_for_student(user_id):
    print(f"[init_plan_list_for_student] (dummy) user={user_id}")
    return True
