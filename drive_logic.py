# drive_logic.py

import os
import json
import datetime
from pydrive2.auth import GoogleAuth as DriveAuth
from pydrive2.drive import GoogleDrive as DriveClient

ga = DriveAuth()
ga.LoadServiceConfigFile("credentials.json")
ga.ServiceAuth()
drive = DriveClient(ga)

PARENT_FOLDER_ID = "19cIFZlEHb8908rOhL67znKK8uzeux-QF"

def create_student_drive_folders(user_id: str, student: dict, plan: dict, base_date: datetime.datetime):
    try:
        name = student.get("name", user_id[-4:])
        student_id = student.get("student_id", user_id[-6:])
        folder_name = f"{name}_{student_id}"

        # 搜尋是否已存在個人資料夾
        query = (
            f"'{PARENT_FOLDER_ID}' in parents and trashed = false and title = '{folder_name}'"
        )
        file_list = drive.ListFile({'q': query}).GetList()
        if file_list:
            print(f"[Drive] 個人資料夾已存在：{folder_name}")
            return

        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': PARENT_FOLDER_ID}]
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()

        print(f"[Drive] 建立個人資料夾 {folder_name}")

        # 建立子資料夾
        for task in plan["tasks"]:
            subfolder_name = task.get("drive_subfolder")
            if not subfolder_name:
                continue
            sub_metadata = {
                'title': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': folder["id"]}]
            }
            subfolder = drive.CreateFile(sub_metadata)
            subfolder.Upload()
            print(f"[Drive] ➤ 建立子資料夾 {subfolder_name}")

    except Exception as e:
        print(f"[Drive] 建立學生資料夾時錯誤：{e}")
