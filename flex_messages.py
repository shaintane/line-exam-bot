from linebot.models import (
    BubbleContainer,
    BoxComponent,
    ButtonComponent,
    FlexSendMessage,
    MessageAction,
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
