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
                    text="國軍桃園醫檢師國考智慧學習系統",
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
                        label="📚 測驗與AI導師",
                        text="測驗與AI導師",
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
        alt_text="國軍桃園醫檢師國考智慧學習系統主選單",
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
        contents.extend(
            [
                TextComponent(
                    text="🎉 恭喜進入 Top 10！請選擇是否設定排行榜暱稱。",
                    size="sm",
                    weight="bold",
                    margin="lg",
                    wrap=True,
                ),
                ButtonComponent(
                    style="primary",
                    margin="lg",
                    action=MessageAction(
                        label="✏️ 輸入暱稱",
                        text="設定挑戰暱稱",
                    ),
                ),
                ButtonComponent(
                    style="secondary",
                    margin="sm",
                    action=MessageAction(
                        label="⏭️ 跳過",
                        text="跳過挑戰暱稱",
                    ),
                ),
            ]
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
    """建立註冊資料填寫說明 Flex；可複製格式另以純文字傳送。"""

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
                    text="請參考下方範例填寫資料，並將資料直接送出。",
                    size="sm",
                    color="#888888",
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
                    text="日期格式：YYYY-MM-DD",
                    size="sm",
                    color="#666666",
                    margin="lg",
                    wrap=True,
                ),
                TextComponent(
                    text="下方會再提供可直接複製的填寫格式。",
                    size="sm",
                    color="#666666",
                    margin="sm",
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


def build_subject_selection_flex():
    """建立國考六科選擇 Flex Message。"""

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="📚 測驗與 AI 導師",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="請選擇想練習的國考科目",
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
                        label="臨床血清免疫學",
                        text="臨床血清免疫學",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="臨床血液與血庫學",
                        text="臨床血液與血庫學",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="臨床生物化學",
                        text="臨床生物化學",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="分子檢驗與鏡檢學",
                        text="醫學分子檢驗與鏡檢學",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="臨床生理與病理學",
                        text="臨床生理與病理學",
                    ),
                ),
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="臨床微生物學",
                        text="臨床微生物學",
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
        alt_text="請選擇國考科目",
        contents=bubble,
    )

def build_exam_result_flex(
    *,
    subject,
    question_count,
    correct_count,
    rate,
    wrong_answers,
    explanation_limit=3,
):
    """建立一般測驗完成 Flex Message，5 題測驗保留解析 Quick Reply。"""

    question_count = int(question_count or 0)
    correct_count = int(correct_count or 0)
    rate = float(rate or 0)
    explanation_limit = int(explanation_limit or 0)
    wrong_answers = list(wrong_answers or [])

    if wrong_answers:
        wrong_text = "\n".join(
            f"題號 {item.get('題號', '')}｜你選 {item.get('作答', '')}｜正解 {item.get('正解', '')}"
            for item in wrong_answers
        )
    else:
        wrong_text = "🎉 全部答對！"

    if question_count == 5:
        ai_text = (
            f"🤖 請點選下方題號查看 AI 解析\n"
            f"本次最多解析 {explanation_limit} 題"
        )
    else:
        ai_text = (
            f"🤖 AI 解析上限為 {explanation_limit} 題\n"
            "請輸入例如：題號3"
        )

    contents = [
        TextComponent(
            text="✅ 測驗完成",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text=str(subject or ""),
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
        BoxComponent(
            layout="vertical",
            margin="lg",
            spacing="sm",
            contents=[
                TextComponent(
                    text=f"答對題數：{correct_count} / {question_count}",
                    size="md",
                    weight="bold",
                    wrap=True,
                ),
                TextComponent(
                    text=f"正確率：{rate:g}%",
                    size="md",
                    wrap=True,
                ),
            ],
        ),
        SeparatorComponent(margin="lg"),
        TextComponent(
            text="錯題整理" if wrong_answers else "作答結果",
            weight="bold",
            size="md",
            margin="lg",
            wrap=True,
        ),
        TextComponent(
            text=wrong_text,
            size="sm",
            color="#555555",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
        TextComponent(
            text=ai_text,
            size="sm",
            color="#666666",
            margin="lg",
            wrap=True,
        ),
        ButtonComponent(
            style="primary",
            margin="xl",
            action=MessageAction(
                label="📚 回到選科測驗",
                text="測驗與AI導師",
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
    ]

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=contents,
        )
    )

    quick_reply = None
    if question_count == 5:
        quick_reply_items = [
            QuickReplyButton(
                action=MessageAction(
                    label=f"題{number}",
                    text=f"題號{number}",
                )
            )
            for number in range(1, 6)
        ]
        quick_reply_items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="⚠️ 回報問題",
                    text="回報問題",
                )
            )
        )
        quick_reply = QuickReply(
            items=quick_reply_items
        )

    return FlexSendMessage(
        alt_text=f"{subject} 測驗完成" if subject else "測驗完成",
        contents=bubble,
        quick_reply=quick_reply,
    )


# =============================================================
# 管理員：問題回報管理
# =============================================================

ISSUE_STATUS_LABELS = {
    "pending": "🔴 待處理",
    "reviewing": "🟡 處理中",
    "resolved": "✅ 已完成",
    "rejected": "⚪ 判定無問題",
}

ISSUE_CATEGORY_LABELS = {
    "wrong_answer": "答案疑似錯誤",
    "bad_question": "題目敘述有問題",
    "bad_option": "選項有問題",
    "image_problem": "圖片異常",
    "ai_wrong": "解析內容疑似錯誤",
    "ai_answer_mismatch": "與題庫答案不一致",
    "ai_unclear": "解析不清楚",
    "ai_missing": "遺漏重要內容",
    "other": "其他",
}


def build_admin_tools_flex():
    """管理者從「我的資料／核准名單」進入管理功能。"""
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="🛠 管理功能",
                    weight="bold",
                    size="xl",
                    wrap=True,
                ),
                TextComponent(
                    text="管理使用者資料與問題回報。",
                    size="sm",
                    color="#888888",
                    margin="sm",
                    wrap=True,
                ),
                SeparatorComponent(margin="lg"),
                ButtonComponent(
                    style="primary",
                    margin="lg",
                    action=MessageAction(
                        label="🛠 問題回報管理",
                        text="問題回報管理",
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
        alt_text="管理功能",
        contents=bubble,
    )


def build_issue_report_dashboard_flex(counts):
    """問題回報管理首頁。"""
    counts = counts or {}

    contents = [
        TextComponent(
            text="🛠 問題回報管理",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text="查看學生回報並更新處理狀態。",
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
    ]

    for status in (
        "pending",
        "reviewing",
        "resolved",
        "rejected",
    ):
        label = ISSUE_STATUS_LABELS[status]
        count = int(counts.get(status, 0) or 0)

        contents.append(
            ButtonComponent(
                style="primary" if status in {"pending", "reviewing"} else "secondary",
                margin="sm",
                action=MessageAction(
                    label=f"{label}　{count}",
                    text=f"回報列表|{status}",
                ),
            )
        )

    contents.append(
        ButtonComponent(
            style="secondary",
            margin="lg",
            action=MessageAction(
                label="🏠 回首頁",
                text="主選單",
            ),
        )
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text="問題回報管理",
        contents=bubble,
    )


def build_issue_report_list_flex(
    reports,
    *,
    status,
):
    """顯示指定狀態的問題回報清單。"""
    reports = list(reports or [])
    status_label = ISSUE_STATUS_LABELS.get(
        status,
        str(status or ""),
    )

    contents = [
        TextComponent(
            text=status_label,
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text=f"最近 {len(reports)} 筆回報",
            size="sm",
            color="#888888",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
    ]

    if not reports:
        contents.append(
            TextComponent(
                text="目前沒有此狀態的問題回報。",
                size="sm",
                color="#666666",
                margin="lg",
                wrap=True,
            )
        )
    else:
        for report in reports:
            report_type = (
                "🤖 解析"
                if report.report_type == "ai_explanation"
                else "⚠️ 題目"
            )
            category = ISSUE_CATEGORY_LABELS.get(
                report.issue_category,
                report.issue_category or "未分類",
            )
            subject = str(report.subject or "未標示科目")
            question_number = report.question_number or "-"

            contents.extend(
                [
                    BoxComponent(
                        layout="vertical",
                        margin="lg",
                        spacing="xs",
                        contents=[
                            TextComponent(
                                text=f"#{report.id} {report_type}｜{subject}",
                                size="sm",
                                weight="bold",
                                wrap=True,
                            ),
                            TextComponent(
                                text=f"題號 {question_number}｜{category}",
                                size="xs",
                                color="#666666",
                                wrap=True,
                            ),
                        ],
                    ),
                    ButtonComponent(
                        style="secondary",
                        margin="sm",
                        action=MessageAction(
                            label=f"查看回報 #{report.id}",
                            text=f"查看回報|{report.id}",
                        ),
                    ),
                ]
            )

    contents.extend(
        [
            SeparatorComponent(margin="lg"),
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="↩️ 回問題回報管理",
                    text="問題回報管理",
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
        ]
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="sm",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text=f"{status_label}問題回報",
        contents=bubble,
    )


def _issue_options_text(options):
    if not isinstance(options, list):
        return ""

    text = "\n".join(
        str(item)
        for item in options
    ).strip()

    if len(text) > 900:
        text = text[:897] + "..."

    return text


def build_issue_report_detail_flex(report):
    """顯示單筆問題回報內容與管理操作。"""
    report_type_label = (
        "🤖 AI 解析問題"
        if report.report_type == "ai_explanation"
        else "⚠️ 題目／答案問題"
    )
    status_label = ISSUE_STATUS_LABELS.get(
        report.status,
        report.status or "未知",
    )
    category_label = ISSUE_CATEGORY_LABELS.get(
        report.issue_category,
        report.issue_category or "未分類",
    )

    question_text = str(
        report.question_text or ""
    ).strip()
    if len(question_text) > 1200:
        question_text = question_text[:1197] + "..."

    options_text = _issue_options_text(
        report.options_json
    )

    ai_text = str(
        report.ai_explanation or ""
    ).strip()
    if len(ai_text) > 1600:
        ai_text = ai_text[:1597] + "..."

    user_name = str(
        getattr(
            report,
            "_registered_name",
            "",
        )
        or ""
    ).strip()

    student_id = str(
        getattr(
            report,
            "_registered_student_id",
            "",
        )
        or ""
    ).strip()

    # 相容舊資料：若 service 未附加註冊資料，再嘗試既有 relationship。
    if (
        not user_name
        and getattr(report, "user", None) is not None
    ):
        user_name = str(
            report.user.name or ""
        ).strip()
        student_id = str(
            report.user.student_id or ""
        ).strip()

    reporter_text = user_name or "未保存姓名"
    if student_id:
        reporter_text += f"（{student_id}）"

    contents = [
        TextComponent(
            text=f"回報 #{report.id}",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        TextComponent(
            text=f"{report_type_label}｜{status_label}",
            size="sm",
            color="#666666",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
        TextComponent(
            text=f"科目：{report.subject or '-'}",
            size="sm",
            margin="lg",
            wrap=True,
        ),
        TextComponent(
            text=f"題號：{report.question_number or '-'}",
            size="sm",
            margin="sm",
            wrap=True,
        ),
        TextComponent(
            text=f"Question ID：{report.question_id or '-'}",
            size="xs",
            color="#777777",
            margin="sm",
            wrap=True,
        ),
        TextComponent(
            text=f"回報人：{reporter_text}",
            size="sm",
            margin="sm",
            wrap=True,
        ),
        TextComponent(
            text=f"問題類型：{category_label}",
            size="sm",
            weight="bold",
            margin="sm",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
        TextComponent(
            text="題目",
            size="md",
            weight="bold",
            margin="lg",
        ),
        TextComponent(
            text=question_text or "-",
            size="sm",
            margin="sm",
            wrap=True,
        ),
    ]

    if options_text:
        contents.extend(
            [
                TextComponent(
                    text="選項",
                    size="md",
                    weight="bold",
                    margin="lg",
                ),
                TextComponent(
                    text=options_text,
                    size="sm",
                    color="#555555",
                    margin="sm",
                    wrap=True,
                ),
            ]
        )

    contents.extend(
        [
            TextComponent(
                text=f"學生答案：{report.student_answer or '-'}",
                size="sm",
                margin="lg",
                wrap=True,
            ),
            TextComponent(
                text=f"題庫答案：{report.correct_answer or '-'}",
                size="sm",
                weight="bold",
                margin="sm",
                wrap=True,
            ),
        ]
    )

    if report.report_type == "ai_explanation":
        contents.extend(
            [
                SeparatorComponent(margin="lg"),
                TextComponent(
                    text="被回報的 AI 解析",
                    size="md",
                    weight="bold",
                    margin="lg",
                ),
                TextComponent(
                    text=ai_text or "未保存解析內容",
                    size="sm",
                    margin="sm",
                    wrap=True,
                ),
            ]
        )

    contents.append(
        SeparatorComponent(margin="lg")
    )

    if report.status == "pending":
        contents.append(
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="🟡 開始處理",
                    text=f"處理回報|{report.id}",
                ),
            )
        )

    if report.status in {"pending", "reviewing"}:
        contents.extend(
            [
                ButtonComponent(
                    style="primary",
                    margin="sm",
                    action=MessageAction(
                        label="✅ 已修正／確認",
                        text=f"完成回報|{report.id}",
                    ),
                ),
                ButtonComponent(
                    style="secondary",
                    margin="sm",
                    action=MessageAction(
                        label="⚪ 確認無問題",
                        text=f"無問題回報|{report.id}",
                    ),
                ),
            ]
        )

    contents.extend(
        [
            ButtonComponent(
                style="secondary",
                margin="lg",
                action=MessageAction(
                    label="↩️ 回問題回報管理",
                    text="問題回報管理",
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
        ]
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="sm",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text=f"問題回報 #{report.id}",
        contents=bubble,
    )


def _split_ai_explanation_sections(explanation):
    """將目前 Structured Output 組成的純文字解析拆成 Flex 區塊。"""
    text = str(explanation or "").strip()

    labels = [
        "作答結果：",
        "正確答案：",
        "核心解析：",
        "選項辨析：",
        "結論：",
        "國考重點：",
    ]

    found = []
    for label in labels:
        pos = text.find(label)
        if pos >= 0:
            found.append((pos, label))

    found.sort()

    if not found:
        return {"body": text}

    key_map = {
        "作答結果：": "result",
        "正確答案：": "correct_answer",
        "核心解析：": "core",
        "選項辨析：": "option_analysis",
        "結論：": "conclusion",
        "國考重點：": "exam_tip",
    }

    sections = {}

    for index, (pos, label) in enumerate(found):
        start = pos + len(label)
        end = (
            found[index + 1][0]
            if index + 1 < len(found)
            else len(text)
        )

        sections[key_map[label]] = text[start:end].strip()

    return sections


def build_ai_explanation_flex(
    *,
    question_number,
    explanation,
    image_url="",
    remaining=0,
    question_count=5,
    allow_ai_report=False,
):
    """建立單題 AI 解析 Flex Message。"""
    question_number = int(question_number or 0)
    remaining = max(int(remaining or 0), 0)
    question_count = int(question_count or 0)

    sections = _split_ai_explanation_sections(explanation)

    contents = [
        TextComponent(
            text=f"📘 題號 {question_number} 解析",
            weight="bold",
            size="xl",
            wrap=True,
        ),
        SeparatorComponent(margin="lg"),
    ]

    result = str(sections.get("result", "")).strip()
    correct_answer = str(sections.get("correct_answer", "")).strip()

    if result:
        contents.append(
            TextComponent(
                text=f"作答結果：{result}",
                size="md",
                weight="bold",
                margin="lg",
                wrap=True,
            )
        )

    if correct_answer:
        contents.append(
            TextComponent(
                text=f"正確答案：{correct_answer}",
                size="md",
                margin="sm",
                wrap=True,
            )
        )

    section_items = [
        ("core", "核心解析"),
        ("option_analysis", "選項辨析"),
        ("conclusion", "結論"),
        ("exam_tip", "🎯 國考重點"),
    ]

    any_section = False

    for key, title in section_items:
        value = str(sections.get(key, "")).strip()

        if not value:
            continue

        if not any_section:
            contents.append(
                SeparatorComponent(margin="lg")
            )
            any_section = True

        contents.extend(
            [
                TextComponent(
                    text=title,
                    size="md",
                    weight="bold",
                    margin="lg",
                    wrap=True,
                ),
                TextComponent(
                    text=value,
                    size="sm",
                    color="#555555",
                    margin="sm",
                    wrap=True,
                ),
            ]
        )

    fallback = str(sections.get("body", "")).strip()

    if fallback:
        contents.append(
            TextComponent(
                text=fallback,
                size="sm",
                color="#555555",
                margin="lg",
                wrap=True,
            )
        )

    if image_url:
        contents.extend(
            [
                SeparatorComponent(margin="lg"),
                TextComponent(
                    text="🔗 題目圖片",
                    size="sm",
                    weight="bold",
                    margin="lg",
                    wrap=True,
                ),
                TextComponent(
                    text=str(image_url),
                    size="xs",
                    color="#777777",
                    margin="sm",
                    wrap=True,
                ),
            ]
        )

    contents.extend(
        [
            SeparatorComponent(margin="xl"),
            ButtonComponent(
                style="primary",
                margin="lg",
                action=MessageAction(
                    label="📚 回分科測驗",
                    text="測驗與AI導師",
                ),
            ),
        ]
    )

    if remaining > 0 and question_count == 5:
        contents.append(
            TextComponent(
                text=(
                    f"🤖 尚可解析 {remaining} 題，"
                    "請直接點選下方題號。"
                ),
                size="xs",
                color="#777777",
                margin="lg",
                wrap=True,
            )
        )
    elif remaining <= 0:
        contents.append(
            TextComponent(
                text="🤖 本次測驗 AI 解析次數已使用完畢。",
                size="xs",
                color="#777777",
                margin="lg",
                wrap=True,
            )
        )

    quick_reply_items = []

    if remaining > 0 and question_count == 5:
        quick_reply_items.extend(
            QuickReplyButton(
                action=MessageAction(
                    label=f"題{number}",
                    text=f"題號{number}",
                )
            )
            for number in range(1, 6)
        )

    if allow_ai_report:
        quick_reply_items.append(
            QuickReplyButton(
                action=MessageAction(
                    label="🤖 回報解析問題",
                    text="回報解析問題",
                )
            )
        )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=contents,
        )
    )

    return FlexSendMessage(
        alt_text=f"題號 {question_number} AI 解析",
        contents=bubble,
        quick_reply=(
            QuickReply(items=quick_reply_items)
            if quick_reply_items
            else None
        ),
    )
