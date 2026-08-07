import os
from pathlib import Path

from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import (
    MessageAction,
    RichMenu,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
)

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("找不到 CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

rich_menu = RichMenu(
    size=RichMenuSize(width=2500, height=1667),
    selected=False,
    name="國軍桃園醫檢師國考智慧學習 Rich Menu v2",
    chat_bar_text="開啟學習選單",
    areas=[
        # 新版圖片上方標題區不設定點擊功能。
        # 01：測驗與 AI 導師
        RichMenuArea(
            bounds=RichMenuBounds(x=40, y=410, width=790, height=675),
            action=MessageAction(label="測驗與 AI 導師", text="測驗與AI導師"),
        ),
        # 02：個人學習
        RichMenuArea(
            bounds=RichMenuBounds(x=860, y=410, width=770, height=675),
            action=MessageAction(label="個人學習", text="個人學習"),
        ),
        # 03：挑戰模式
        RichMenuArea(
            bounds=RichMenuBounds(x=1670, y=410, width=775, height=675),
            action=MessageAction(label="挑戰模式", text="挑戰模式"),
        ),
        # 04：排行榜
        RichMenuArea(
            bounds=RichMenuBounds(x=40, y=1115, width=1210, height=490),
            action=MessageAction(label="排行榜", text="排行榜"),
        ),
        # 05：我的資料
        RichMenuArea(
            bounds=RichMenuBounds(x=1280, y=1115, width=1165, height=490),
            # 沿用目前 handlers.py 既有指令，不變更權限或註冊流程。
            action=MessageAction(label="我的資料", text="核准名單"),
        ),
    ],
)

rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)

image_path = Path(__file__).with_name("rich_menu_v2.png")
with image_path.open("rb") as image_file:
    line_bot_api.set_rich_menu_image(
        rich_menu_id,
        "image/png",
        image_file,
    )

print("Rich Menu 建立成功")
print("richMenuId =", rich_menu_id)
print()
print("注意：此腳本不會設定 default rich menu。")
print("尚未核准的使用者不會自動看到它。")
print("下一步才會把 richMenuId 綁定到指定的 approved user。")
