# drive_logic.py (lazy load 版, 移除 PyDrive2, 改用 google-auth + googleapiclient)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ 全域 client，僅在第一次呼叫時初始化
_drive_service = None

# ✅ Google Drive 的母資料夾 ID（存放學生專屬資料夾的根目錄）
PARENT_FOLDER_ID = "19cIFZlEHb8908rOhL67znKK8uzeux-QF"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_drive_service():
    """延遲初始化 Google Drive API service"""
    global _drive_service
    if _drive_service is None:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        _drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
        print("[Drive] Google Drive client 已初始化")
    return _drive_service


def create_student_drive_folder(student: dict, tasks: list) -> str:
    """
    在 Google Drive 母資料夾下建立學生個人專屬資料夾，
    並依照 plan["tasks"] 建立子資料夾。
    """
    try:
        service = get_drive_service()
        name = student.get("name", "unknown")
        student_id = student.get("student_id", "000000")
        folder_name = f"{name}_{student_id}"

        # 🔍 檢查是否已存在
        query = (
            f"'{PARENT_FOLDER_ID}' in parents and "
            f"name = '{folder_name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        results = service.files().list(q=query, spaces="drive").execute()
        items = results.get("files", [])
        if items:
            folder_id = items[0]["id"]
            print(f"[Drive] 個人資料夾已存在：{folder_name}")
            return folder_id

        # 🆕 建立個人資料夾
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [PARENT_FOLDER_ID],
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = folder.get("id")
        print(f"[Drive] 建立個人資料夾 {folder_name} (id={folder_id})")

        # ➕ 建立子資料夾
        for task in tasks:
            subfolder_name = task.get("drive_subfolder")
            if not subfolder_name:
                continue
            sub_metadata = {
                "name": subfolder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [folder_id],
            }
            service.files().create(body=sub_metadata, fields="id").execute()
            print(f"[Drive] ➤ 建立子資料夾 {subfolder_name}")

        return folder_id

    except HttpError as e:
        print(f"[Drive] 建立學生資料夾時 API 錯誤：{e}")
        return ""
    except Exception as e:
        print(f"[Drive] 建立學生資料夾時發生錯誤：{e}")
        return ""
