# sheets_logic.py
import os
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === 讀取認證：從環境變數 GOOGLE_CREDENTIALS (Railway/Render 等雲端常用) ===
def get_credentials_from_env():
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    return Credentials.from_service_account_info(creds_info)

def _service():
    creds = get_credentials_from_env()
    return build("sheets", "v4", credentials=creds)

def _parse_date(s: str):
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def get_latest_valid_row(sheet_id: str, sheet_name: str, user_id: str, line_id_header_candidates=None):
    """
    從指定試算表的指定分頁讀取資料，找出「符合該 LINE 使用者」且「今天在起迄日範圍內」的最新一筆。
    - sheet_name 會自動加上引號並拉整欄範圍：'工作表名'!A:Z
    - line_id_header_candidates：LINE ID 欄位可能的名稱清單
    回傳：
      {
        "LINE_ID": "...",
        "name": "...",
        "school": "...",
        "start_date": "YYYY-MM-DD",
        "end_date":   "YYYY-MM-DD"
      } 或 None
    """
    if line_id_header_candidates is None:
        # 依你的表頭可能出現的各種命名排一個嘗試名單
        line_id_header_candidates = ["LINE_ID", "Line ID", "line_id", "第 12 題", "第12題", "LINE Id"]

    rng = f"'%s'!A:Z" % sheet_name  # 為避免空白/特殊字元，強制加單引號
    svc = _service()
    resp = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng, majorDimension="ROWS").execute()
    rows = resp.get("values", [])

    if not rows or len(rows) < 2:
        return None

    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}

    # 找到 line_id 欄位
    line_id_col = None
    for cand in line_id_header_candidates:
        if cand in idx:
            line_id_col = idx[cand]
            break
    if line_id_col is None:
        # 找不到就直接放棄，請你調整表頭
        raise RuntimeError(f"找不到 LINE ID 欄位（嘗試: {line_id_header_candidates}），請確認表頭。")

    # 其他常用欄位（允許缺漏，用安全取值）
    def safe_get(r, name):
        j = idx.get(name, None)
        return (r[j].strip() if (j is not None and j < len(r)) else "")

    today = datetime.today().date()
    latest = None

    # 從下往上掃（較新在後面），遇到第一筆符合就用它
    for r in reversed(rows[1:]):
        line_id = (r[line_id_col].strip() if line_id_col < len(r) else "")
        if line_id != user_id:
            continue

        start_s = safe_get(r, "起始日期 (學生統一填實習起始日期/教師免填)")
        end_s   = safe_get(r, "結束日期 (學生統一填實習起始日期/教師免填)")
        name    = safe_get(r, "姓名")
        role  = safe_get(r, "角色") or safe_get(r, "角色")

        start_d = _parse_date(start_s)
        end_d   = _parse_date(end_s)
        if not start_d or not end_d:
            continue

        if start_d <= today <= end_d:
            latest = {
                "LINE_ID": line_id,
                "name": name,
                "school": school,
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
            }
            break

    return latest

def write_whitelist(entry: dict, path="whitelist.json"):
    """
    把通過條件的使用者寫入本地白名單檔案（以 LINE_ID 當 key）。
    格式會與你現有檔案一致：
    {
      "Uxxxxxxxx": {
        "student_id": "...",  # 若沒有就略過
        "name": "...",
        "role": "...",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
      }
    }
    """
    if not entry or not entry.get("LINE_ID"):
        return False

    data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    # 保留舊的 student_id（如有）
    obj = data.get(entry["LINE_ID"], {})
    obj.update({
        "name": entry.get("name") or obj.get("name", ""),
        "school": entry.get("school") or obj.get("school", ""),
        "start_date": entry.get("start_date"),
        "end_date": entry.get("end_date"),
    })
    data[entry["LINE_ID"]] = obj

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True
