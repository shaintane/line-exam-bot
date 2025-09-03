from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

DRIVE_PARENT_FOLDER_ID = "19cIFZlEHb8908rOhL67znKK8uzeux-QF"

SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

def create_student_drive_structure(user_id: str, student: dict, plan: dict, offset_base: int = 0):
    student_name = student.get("name", user_id)
    student_folder_name = f"{student_name}_{user_id[-6:]}"
    student_folder_id = create_drive_folder(student_folder_name, DRIVE_PARENT_FOLDER_ID)
    print(f"[Drive] 建立個人資料夾 {student_folder_name}，ID: {student_folder_id}")

    for task in plan.get("tasks", []):
        subfolder_name = task.get("drive_subfolder")
        if not subfolder_name:
            continue

        start_offset = task.get("start_offset_days", 0) + offset_base
        start_date = (datetime.strptime(student['start_date'], "%Y-%m-%d") + timedelta(days=start_offset)).strftime("%m%d")
        full_folder_name = f"{start_date}_{subfolder_name}"
        create_drive_folder(full_folder_name, student_folder_id)
        print(f"[Drive] 建立子資料夾 {full_folder_name}")

def create_drive_folder(name: str, parent_id: str) -> str:
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")
