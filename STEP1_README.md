# LINE Bot 國考系統：第一輪重構

## 這一版完成的項目

1. `handlers.py` 先處理註冊與管理命令，再進入測驗流程。
2. 管理者身分改由 `.env` 的 `ADMIN_LINE_USER_IDS` 驗證。
3. 新增 `access_control.py`，集中處理白名單、啟用狀態與使用期限。
4. 暫時相容舊版中文欄位與新版英文欄位。
5. 新增一般使用者「註冊」流程。
6. 系統錯誤只記錄於伺服器 log，不再把例外內容傳給學生。
7. OpenAI 模型改由 `OPENAI_MODEL` 環境變數指定。

## 部署前必要設定

將 `.env.example` 複製為 `.env`，填入：

- `CHANNEL_ACCESS_TOKEN`
- `CHANNEL_SECRET`
- `OPENAI_API_KEY`
- `ADMIN_LINE_USER_IDS`

`ADMIN_LINE_USER_IDS` 必須是 LINE Messaging API 提供、以 `U` 開頭的 user ID。多位管理者可用逗號分隔。

## 測試流程

1. 一般使用者輸入：`註冊`
2. 輸入：`學校 姓名 學號 2026-08-01 2026-12-31`
3. 管理者輸入：`show pending`
4. 管理者輸入：`approve 學號`
5. 使用者輸入：`微生物`
6. 依序回答 A、B、C、D。

## 管理命令

- `show pending`
- `show whitelist`
- `approve 學號或LINE_ID`
- `input 學校 姓名 學號 起始日 結束日 LINE_ID`
- `disable 學號或LINE_ID`
- `enable 學號或LINE_ID`
- `delet 學號或LINE_ID`
