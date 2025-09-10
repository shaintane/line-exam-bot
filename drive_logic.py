# drive_logic.py

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ✅ 延遲初始化 Google Drive client
_drive = None

def get_drive():
    """延遲初始化 Google Drive client"""
    global _drive
    if _drive is None:
        ga = GoogleAuth()
        ga.LoadServiceConfigFile("credentials.json")
        ga.ServiceAuth()
        _drive = GoogleDrive(ga)
        print("[Drive] Google Drive client 已初始化")
    return _drive


# ✅ Google Drive 的母資料夾 ID（存放學生專屬資料夾的根目錄）
PARENT_FOLDER_ID = "19cIFZlEHb8908rOhL67znKK8uzeux-QF"


def create_student_drive_folder(student: dict, tasks: list) -> str:
    """
    在 Google Drive 母資料夾下建立學生個人專屬資料夾，
    並依照 plan["tasks"] 建立子資料夾。
    """
    try:
        drive = get_drive()
        name = student.get("name", "unknown")
        student_id = student.get("student_id", "000000")
        folder_name = f"{name}_{student_id}"

        # 🔍 檢查是否已存在
        query = f"'{PARENT_FOLDER_ID}' in parents and trashed = false and title = '{folder_name}'"
        file_list = drive.ListFile({'q': query}).GetList()
        if file_list:
            folder_id = file_list[0]["id"]
            print(f"[Drive] 個人資料夾已存在：{folder_name}")
            return folder_id

        # 🆕 建立個人資料夾
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': PARENT_FOLDER_ID}]
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        folder_id = folder["id"]

        print(f"[Drive] 建立個人資料夾 {folder_name} (id={folder_id})")

        # ➕ 建立子資料夾
        for task in tasks:
            subfolder_name = task.get("drive_subfolder")
            if not subfolder_name:
                continue
            sub_metadata = {
                'title': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': folder_id}]
            }
            subfolder = drive.CreateFile(sub_metadata)
            subfolder.Upload()
            print(f"[Drive] ➤ 建立子資料夾 {subfolder_name}")

        return folder_id

    except Exception as e:
        print(f"[Drive] 建立學生資料夾時錯誤：{e}")
        return ""
