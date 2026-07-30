from linebot.models import (
    BubbleContainer,
    BoxComponent,
    ButtonComponent,
    FlexSendMessage,
    MessageAction,
    QuickReply,
    QuickReplyButton,
    SeparatorComponent,
    TextComponent,
)


def build_home_flex():
    """建立首頁 Flex Message。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="醫事檢驗師國考學習系統",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="請選擇功能",
                    size="sm",
                    color="#888888",
                    margin="sm",
                ),
                ButtonComponent(
                    style="primary",
                    margin="lg",
                    action=MessageAction(
                        label="👤 註冊／會員",
                        text="註冊／會員",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="📚 一般測驗",
                        text="一般測驗",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="🎯 個人學習",
                        text="個人學習",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="🏆 挑戰模式",
                        text="挑戰模式",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="🥇 排行榜",
                        text="排行榜",
                    ),
                ),
            ],
        )
    )

    return FlexSendMessage(
        alt_text="醫事檢驗師國考學習系統主選單",
        contents=bubble,
    )


def build_personal_learning_flex():
    """建立個人學習 Flex Message。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="🎯 個人學習",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="查看學習紀錄，或依作答結果分析弱點。",
                    size="sm",
                    color="#888888",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                ButtonComponent(
                    style="primary",
                    margin="lg",
                    action=MessageAction(
                        label="📊 學習歷程",
                        text="學習歷程",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="🔍 弱點分析",
                        text="弱點分析",
                    ),
                ),
                ButtonComponent(
                    style="secondary",
                    margin="lg",
                    action=MessageAction(
                        label="🏠 回首頁",
                        text="主選單",
                    ),
                ),
            ],
        )
    )

    return FlexSendMessage(
        alt_text="個人學習選單",
        contents=bubble,
    )


def build_challenge_flex():
    """建立挑戰模式 Flex Message，並附上開始挑戰 Quick Reply。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="🏆 國考挑戰模式",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="30 題｜六科各 5 題｜23 分鐘",
                    size="md",
                    weight="bold",
                    margin="md",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                TextComponent(
                    text="排名規則",
                    weight="bold",
                    size="md",
                    margin="lg",
                ),
                TextComponent(
                    text="① 答對題數優先\n② 同分再比完成時間",
                    size="sm",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                TextComponent(
                    text="挑戰說明",
                    weight="bold",
                    size="md",
                    margin="lg",
                ),
                TextComponent(
                    text=(
                        "• 作答後不立即顯示對錯\n"
                        "• 挑戰開始後計時不暫停\n"
                        "• 挑戰結果不納入一般學習歷程與弱點分析"
                    ),
                    size="sm",
                    color="#666666",
                    margin="sm",
                    wrap=True,
                ),
                ButtonComponent(
                    style="primary",
                    margin="xl",
                    action=MessageAction(
                        label="👤 我的排名",
                        text="我的排名",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="🥇 排行榜",
                        text="排行榜",
                    ),
                ),
                ButtonComponent(
                    style="secondary",
                    margin="lg",
                    action=MessageAction(
                        label="🏠 回首頁",
                        text="主選單",
                    ),
                ),
            ],
        )
    )

    return FlexSendMessage(
        alt_text="國考挑戰模式",
        contents=bubble,
        quick_reply=QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(
                        label="🔥 開始挑戰",
                        text="開始挑戰",
                    )
                )
            ]
        ),
    )
