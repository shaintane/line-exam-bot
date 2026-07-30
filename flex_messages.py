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

def build_leaderboard_flex(rows):
    """建立挑戰模式 Top 10 排行榜 Flex Message。"""

    if not rows:
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                spacing="md",
                contents=[
                    TextComponent(
                        text="🥇 歷史排行榜",
                        weight="bold",
                        size="xl",
                        wrap=True,
                    ),
                    TextComponent(
                        text="目前還沒有完成的挑戰紀錄。",
                        size="sm",
                        color="#888888",
                        margin="lg",
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
                        style="secondary",
                        margin="sm",
                        action=MessageAction(
                            label="🏠 回首頁",
                            text="主選單",
                        ),
                    ),
                ],
            )
        )

        return FlexSendMessage(
            alt_text="挑戰模式歷史排行榜",
            contents=bubble,
        )

    titles = {
        1: "神級人物",
        2: "國考大神",
        3: "超強挑戰者",
    }

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    ranking_contents = []

    for row in rows:
        rank = int(row["rank"])
        nickname = str(row.get("nickname") or "未設定暱稱")
        correct_count = int(row.get("correct_count") or 0)
        question_count = int(row.get("question_count") or 30)
        elapsed_seconds = max(int(row.get("elapsed_seconds") or 0), 0)

        minutes, seconds = divmod(elapsed_seconds, 60)
        elapsed_text = f"{minutes}分{seconds:02d}秒"

        prefix = medals.get(rank, f"{rank}.")
        title = titles.get(rank)

        name_text = f"{prefix} {nickname}"
        if title:
            name_text += f"｜{title}"

        ranking_contents.append(
            BoxComponent(
                layout="vertical",
                margin="md",
                spacing="xs",
                contents=[
                    TextComponent(
                        text=name_text,
                        weight="bold" if rank <= 3 else "regular",
                        size="sm",
                        wrap=True,
                    ),
                    TextComponent(
                        text=f"{correct_count}/{question_count}｜{elapsed_text}",
                        size="xs",
                        color="#777777",
                        wrap=True,
                    ),
                ],
            )
        )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="🥇 歷史排行榜",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="Top 10｜答對題數優先，同分再比完成時間",
                    size="xs",
                    color="#888888",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                *ranking_contents,
                SeparatorComponent(
                    margin="lg",
                ),
                ButtonComponent(
                    style="primary",
                    margin="lg",
                    action=MessageAction(
                        label="👤 我的排名",
                        text="我的排名",
                    ),
                ),
                ButtonComponent(
                    style="secondary",
                    margin="sm",
                    action=MessageAction(
                        label="🏠 回首頁",
                        text="主選單",
                    ),
                ),
            ],
        )
    )

    return FlexSendMessage(
        alt_text="挑戰模式歷史排行榜",
        contents=bubble,
    )

def build_personal_rank_flex(summary):
    """建立個人挑戰排名 Flex Message。"""

    if not summary or not summary.get("has_record"):
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                spacing="md",
                contents=[
                    TextComponent(
                        text="👤 我的排名",
                        weight="bold",
                        size="xl",
                        wrap=True,
                    ),
                    TextComponent(
                        text="目前還沒有完成的挑戰成績。",
                        size="sm",
                        color="#888888",
                        margin="lg",
                        wrap=True,
                    ),
                    ButtonComponent(
                        style="primary",
                        margin="xl",
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
            alt_text="我的挑戰排名",
            contents=bubble,
        )

    rank = summary.get("rank")
    rank_text = f"第 {rank} 名" if rank is not None else "尚未排名"

    nickname = str(summary.get("nickname") or "未設定暱稱")
    correct_count = int(summary.get("correct_count") or 0)
    question_count = int(summary.get("question_count") or 30)
    score_rate = summary.get("score_rate")
    if score_rate is None:
        score_rate = round(
            (correct_count / question_count) * 100,
            1,
        ) if question_count else 0

    elapsed_seconds = max(
        int(summary.get("elapsed_seconds") or 0),
        0,
    )
    minutes, seconds = divmod(elapsed_seconds, 60)
    elapsed_text = f"{minutes}分{seconds:02d}秒"

    if rank is not None and rank <= 10:
        status_text = "🔥 已進入 Top 10！"
    else:
        status_text = "繼續挑戰，刷新你的最佳紀錄。"

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="👤 我的排名",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text=nickname,
                    size="md",
                    weight="bold",
                    margin="md",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                BoxComponent(
                    layout="vertical",
                    margin="lg",
                    spacing="sm",
                    contents=[
                        TextComponent(
                            text=f"歷史最佳：{correct_count} / {question_count}",
                            size="md",
                            wrap=True,
                        ),
                        TextComponent(
                            text=f"正確率：{score_rate}%",
                            size="md",
                            wrap=True,
                        ),
                        TextComponent(
                            text=f"最佳時間：{elapsed_text}",
                            size="md",
                            wrap=True,
                        ),
                        TextComponent(
                            text=f"目前排名：{rank_text}",
                            size="md",
                            weight="bold",
                            wrap=True,
                        ),
                    ],
                ),
                TextComponent(
                    text=status_text,
                    size="sm",
                    color="#666666",
                    margin="lg",
                    wrap=True,
                ),
                ButtonComponent(
                    style="primary",
                    margin="xl",
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
        alt_text="我的挑戰排名",
        contents=bubble,
    )
