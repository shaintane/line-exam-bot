# sheets_logic.py
import os
import json
import re
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
    # 允許 2025/8/29 這種格式
    try:
        parts = re.split(r"[\/\-]", s.split()[0])
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return datetime(y, m, d).date()
    except Exception:
        return None

def get_latest_valid_row(sheet_id: str, sheet_name: str, user_id: str, line_id_header_candidates=None):
    """
    讀取指定分頁，找出符合該 LINE_ID 的「最新一筆」：
    - LINE_ID 欄位：精確或模糊（包含 line+id）
    - 日期欄位：模糊匹配（起始/開始/start；結束/截止/end），若不存在則視為無期限
    """
    if line_id_header_candidates is None:
        line_id_header_candidates = ["LINE_ID", "LINE ID", "Line ID", "line_id", "第 12 題", "第12題"]

    svc = _service()
    rng = f"'%s'!A:Z" % sheet_name
    resp = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=rng, majorDimension="ROWS"
    ).execute()

    rows = resp.get("values", [])
    if not rows or len(rows) < 2:
        return None

    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    norm_headers = [re.sub(r"\s+", "", h).lower() for h in headers]

    # 1) LINE_ID 欄位
    line_col = None
    for cand in line_id_header_candidates:
        if cand in idx:
            line_col = idx[cand]; break
    if line_col is None:
        for i, h in enumerate(norm_headers):
            if "line" in h and "id" in h:
                line_col = i; break
    if line_col is None:
        raise RuntimeError(f"找不到 LINE ID 欄位（嘗試: {line_id_header_candidates}），請確認表頭。")

    # 2) 日期欄位（模糊）
    def _find_col_by_keywords(keywords):
        for i, h in enumerate(norm_headers):
            if any(k in h for k in keywords):
                return i
        return None
    start_col = _find_col_by_keywords(["起始", "開始", "start"])
    end_col   = _find_col_by_keywords(["結束", "截止", "end"])

    def at(r, col):
        return (r[col].strip() if col is not None and col < len(r) else "")

    # 3) 從下往上找最新一筆符合 LINE_ID 的資料
    today = datetime.today().date()
    for r in reversed(rows[1:]):
        if at(r, line_col) != user_id:
            continue

        # 安全取欄位（沒有就空）
        def pick(names):
            for n in names:
                j = idx.get(n)
                if j is not None and j < len(r):
                    return r[j].strip()
            return ""

        name  = pick(["姓名", "Name"]) or ""
        role  = pick(["ROLE", "角色"]) or ""
        email = pick(["Email", "EMAIL", "電子信箱"]) or ""

        start_d = _parse_date(at(r, start_col)) if start_col is not None else None
        end_d   = _parse_date(at(r, end_col))   if end_col   is not None else None

        within = True
        if start_d and end_d:
            within = (start_d <= today <= end_d)

        if within:
            return {
                "LINE_ID": user_id,
                "name": name,
                "role": role.lower(),
                "email": email,
                "start_date": start_d.isoformat() if start_d else "",
                "end_date":   end_d.isoformat()   if end_d   else "",
            }

    return None

def write_whitelist(entry: dict, path="whitelist.json"):
    """
    把通過條件的使用者寫入本地白名單檔案（以 LINE_ID 當 key）。
    儲存欄位：name, role, start_date, end_date, email
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

    obj = data.get(entry["LINE_ID"], {})
    obj.update({
        "name": entry.get("name") or obj.get("name", ""),
        "role": entry.get("role") or obj.get("role", "student"),
        "start_date": entry.get("start_date") or obj.get("start_date", ""),
        "end_date": entry.get("end_date") or obj.get("end_date", ""),
        "email": entry.get("email") or obj.get("email", ""),
    })
    data[entry["LINE_ID"]] = obj

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True
