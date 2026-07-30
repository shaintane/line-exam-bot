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
                        label="👤 註冊",
                        text="註冊選單",
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

def build_challenge_result_flex(
    *,
    status,
    answered_count,
    total,
    correct,
    rate,
    elapsed_seconds,
    personal=None,
    needs_nickname=False,
):
    """建立挑戰結算 Flex Message。"""

    total = int(total or 30)
    answered_count = int(answered_count or 0)
    correct = int(correct or 0)
    elapsed_seconds = max(int(elapsed_seconds or 0), 0)

    minutes, seconds = divmod(elapsed_seconds, 60)
    elapsed_text = f"{minutes}分{seconds:02d}秒"

    if status == "timeout":
        title = "⏰ 挑戰時間到"
        subtitle = f"已完成 {answered_count} / {total} 題"
    else:
        title = "🏆 挑戰完成"
        subtitle = "本次挑戰成績"

    contents = [
        TextComponent(
            text=title,
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text=subtitle,
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(
            margin="lg",
        ),
        TextComponent(
            text="本次挑戰",
            weight="bold",
            size="md",
            margin="lg",
        ),
        BoxComponent(
            layout="vertical",
            margin="sm",
            spacing="sm",
            contents=[
                TextComponent(
                    text=f"答對題數：{correct} / {total}",
                    size="md",
                    wrap=True,
                ),
                TextComponent(
                    text=f"正確率：{rate}%",
                    size="md",
                    wrap=True,
                ),
                TextComponent(
                    text=f"完成時間：{elapsed_text}",
                    size="md",
                    wrap=True,
                ),
            ],
        ),
    ]

    if personal and personal.get("has_record"):
        rank = personal.get("rank")
        rank_text = f"第 {rank} 名" if rank is not None else "尚未排名"

        best_correct = int(personal.get("correct_count") or 0)
        best_total = int(personal.get("question_count") or total)
        best_elapsed = max(int(personal.get("elapsed_seconds") or 0), 0)
        best_minutes, best_seconds = divmod(best_elapsed, 60)
        best_elapsed_text = f"{best_minutes}分{best_seconds:02d}秒"

        contents.extend(
            [
                SeparatorComponent(
                    margin="lg",
                ),
                TextComponent(
                    text="個人紀錄",
                    weight="bold",
                    size="md",
                    margin="lg",
                ),
                BoxComponent(
                    layout="vertical",
                    margin="sm",
                    spacing="sm",
                    contents=[
                        TextComponent(
                            text=f"歷史最佳：{best_correct} / {best_total}",
                            size="md",
                            wrap=True,
                        ),
                        TextComponent(
                            text=f"最佳時間：{best_elapsed_text}",
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
            ]
        )

        if rank is not None and rank <= 10:
            contents.append(
                TextComponent(
                    text="🎉 成功進入 Top 10！",
                    size="sm",
                    weight="bold",
                    margin="lg",
                    wrap=True,
                )
            )

    if needs_nickname:
        contents.append(
            TextComponent(
                text="請直接輸入排行榜暱稱，設定後就會顯示在排行榜。",
                size="sm",
                color="#666666",
                margin="lg",
                wrap=True,
            )
        )

    contents.extend(
        [
            SeparatorComponent(
                margin="xl",
            ),
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="🔥 再次挑戰",
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
        ]
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text="挑戰結算",
        contents=bubble,
    )

def _split_flex_text(text, max_chars=1200):
    """將較長文字切成多個 Flex TextComponent 可安全顯示的區塊。"""
    cleaned = str(text or "").strip()

    if not cleaned:
        return ["目前沒有可顯示的資料。"]

    chunks = []
    current = ""

    for line in cleaned.splitlines():
        candidate = line if not current else f"{current}\n{line}"

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(line) > max_chars:
            chunks.append(line[:max_chars])
            line = line[max_chars:]

        current = line

    if current:
        chunks.append(current)

    return chunks


def build_learning_history_flex(message):
    """建立學習歷程結果 Flex。"""

    body_contents = [
        TextComponent(
            text="📊 學習歷程",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text="近期測驗與學習表現",
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(
            margin="lg",
        ),
    ]

    for chunk in _split_flex_text(message):
        body_contents.append(
            TextComponent(
                text=chunk,
                size="sm",
                margin="md",
                wrap=True,
            )
        )

    body_contents.extend(
        [
            SeparatorComponent(
                margin="xl",
            ),
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="🔍 弱點分析",
                    text="弱點分析",
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
                style="secondary",
                margin="lg",
                action=MessageAction(
                    label="🏠 回首頁",
                    text="主選單",
                ),
            ),
        ]
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=body_contents,
        )
    )

    return FlexSendMessage(
        alt_text="學習歷程",
        contents=bubble,
    )


def build_weakness_analysis_flex(message, has_data=True):
    """建立弱點分析結果 Flex。"""

    body_contents = [
        TextComponent(
            text="🔍 弱點分析",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text="依近期作答紀錄整理優先加強方向",
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(
            margin="lg",
        ),
    ]

    for chunk in _split_flex_text(message):
        body_contents.append(
            TextComponent(
                text=chunk,
                size="sm",
                margin="md",
                wrap=True,
            )
        )

    body_contents.append(
        SeparatorComponent(
            margin="xl",
        )
    )

    if has_data:
        body_contents.append(
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="🎯 開始弱點練習",
                    text="開始弱點練習",
                ),
            )
        )

    body_contents.extend(
        [
            ButtonComponent(
                style="primary",
                margin="sm" if has_data else "lg",
                action=MessageAction(
                    label="📊 學習歷程",
                    text="學習歷程",
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
        ]
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=body_contents,
        )
    )

    return FlexSendMessage(
        alt_text="弱點分析",
        contents=bubble,
    )

def build_registration_menu_flex():
    """建立註冊第二層選單 Flex。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="👤 註冊",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="申請使用資格，或查看核准資訊。",
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
                        label="📝 註冊",
                        text="開始註冊",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="✅ 核准名單",
                        text="核准名單",
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
        alt_text="註冊選單",
        contents=bubble,
    )


def build_registration_form_flex():
    """建立註冊資料填寫說明 Flex。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="📝 使用者註冊",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="請依下列格式直接輸入一行資料。",
                    size="sm",
                    color="#888888",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                TextComponent(
                    text="填寫格式",
                    weight="bold",
                    size="md",
                    margin="lg",
                    wrap=True,
                ),
                TextComponent(
                    text=(
                        "學校：\n"
                        "姓名：\n"
                        "學號：\n"
                        "起始日：\n"
                        "結束日："
                    ),
                    size="md",
                    margin="sm",
                    wrap=True,
                ),
                TextComponent(
                    text="日期格式：YYYY-MM-DD",
                    size="sm",
                    color="#666666",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(
                    margin="lg",
                ),
                TextComponent(
                    text="範例",
                    weight="bold",
                    size="md",
                    margin="lg",
                    wrap=True,
                ),
                TextComponent(
                    text=(
                        "學校：國立醫學大學\n"
                        "姓名：王小明\n"
                        "學號：A123456\n"
                        "起始日：2026-08-01\n"
                        "結束日：2026-12-31"
                    ),
                    size="sm",
                    margin="sm",
                    wrap=True,
                ),
                TextComponent(
                    text="輸入完成後直接送出即可。",
                    size="sm",
                    color="#666666",
                    margin="lg",
                    wrap=True,
                ),
            ],
        )
    )

    return FlexSendMessage(
        alt_text="使用者註冊",
        contents=bubble,
    )


def build_my_registration_flex(record=None):
    """一般使用者查看自己的核准資訊；不顯示 LINE ID 與學號。"""

    if not record:
        contents = [
            TextComponent(
                text="✅ 核准資訊",
                weight="bold",
                size="xl",
                wrap=True,
            ),
            SeparatorComponent(
                margin="lg",
            ),
            TextComponent(
                text="目前查無已核准的使用資格。",
                size="md",
                margin="lg",
                wrap=True,
            ),
        ]
    else:
        start_date = str(record.get("start_date") or "未設定")
        end_date = str(record.get("end_date") or "未設定")
        is_active = bool(record.get("is_active", True))
        status_text = "使用中" if is_active else "已停用"

        contents = [
            TextComponent(
                text="✅ 我的核准資訊",
                weight="bold",
                size="xl",
                wrap=True,
            ),
            TextComponent(
                text=f"狀態：{status_text}",
                size="sm",
                color="#666666",
                margin="sm",
                wrap=True,
            ),
            SeparatorComponent(
                margin="lg",
            ),
            TextComponent(
                text=f"姓名：{record.get('name') or '未設定'}",
                size="md",
                margin="lg",
                wrap=True,
            ),
            TextComponent(
                text=f"學校：{record.get('school') or '未設定'}",
                size="md",
                margin="sm",
                wrap=True,
            ),
            TextComponent(
                text=f"使用期限：{start_date} ～ {end_date}",
                size="md",
                margin="sm",
                wrap=True,
            ),
        ]

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text="我的核准資訊",
        contents=bubble,
    )
