from plans_loader import load_plan_data
from whitelist import get_student_data
from drive_logic import create_student_drive_structure
from student_sheet_logic import create_student_sheet_with_tasks

def init_plan_for_student(user_id: str, plan_id: str, offset_base: int = 0):
    print(f"[INIT] 開始為 {user_id} 初始化 {plan_id}（偏移量 {offset_base} 天）")

    student = get_student_data(user_id)
    if not student:
        print(f"[錯誤] 找不到 user_id: {user_id} 的學生資料")
        return

    plan = load_plan_data(plan_id)
    if not plan:
        print(f"[錯誤] 找不到課程模組: {plan_id}")
        return

    create_student_drive_structure(user_id, student, plan, offset_base)
    create_student_sheet_with_tasks(user_id, student, plan, offset_base)

    print(f"[INIT] {plan_id} 初始化完成 for {user_id}")
