from datetime import datetime, timezone

from database import db


def utc_now() -> datetime:
    """回傳具時區資訊的 UTC 時間。"""
    return datetime.now(timezone.utc)


class User(db.Model):
    """LINE Bot 使用者基本資料。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(150), nullable=True)
    student_id = db.Column(db.String(100), nullable=True)
    role = db.Column(
        db.String(30),
        nullable=False,
        default="intern",
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="approved",
    )
    valid_from = db.Column(db.Date, nullable=True)
    valid_until = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    exam_attempts = db.relationship(
        "ExamAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    issue_reports = db.relationship(
        "IssueReport",
        back_populates="user",
        lazy=True,
        foreign_keys="IssueReport.user_id",
    )

    challenge_profile = db.relationship(
        "ChallengeProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    challenge_attempts = db.relationship(
        "ChallengeAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )


class ExamAttempt(db.Model):
    """每完成或進行一次測驗的主紀錄。"""

    __tablename__ = "exam_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )
    repo = db.Column(db.String(100), nullable=True)
    question_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )
    correct_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )
    score_rate = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="in_progress",
        index=True,
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="exam_attempts",
    )
    answer_records = db.relationship(
        "AnswerRecord",
        back_populates="attempt",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="AnswerRecord.question_number",
    )


class AnswerRecord(db.Model):
    """每一道題目的作答快照。"""

    __tablename__ = "answer_records"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_number = db.Column(
        db.Integer,
        nullable=False,
    )
    question_id = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )
    question_text = db.Column(
        db.Text,
        nullable=False,
    )
    options_json = db.Column(
        db.JSON,
        nullable=True,
    )
    student_answer = db.Column(
        db.String(10),
        nullable=False,
    )
    correct_answer = db.Column(
        db.String(10),
        nullable=False,
    )
    is_correct = db.Column(
        db.Boolean,
        nullable=False,
        index=True,
    )
    answered_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    attempt = db.relationship(
        "ExamAttempt",
        back_populates="answer_records",
    )
    explanation_records = db.relationship(
        "ExplanationRecord",
        back_populates="answer_record",
        cascade="all, delete-orphan",
        lazy=True,
    )

    issue_reports = db.relationship(
        "IssueReport",
        back_populates="answer_record",
        lazy=True,
        foreign_keys="IssueReport.answer_record_id",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "attempt_id",
            "question_number",
            name="uq_answer_attempt_question_number",
        ),
    )


class ExplanationRecord(db.Model):
    """AI 解析產生與查閱紀錄。"""

    __tablename__ = "explanation_records"

    id = db.Column(db.Integer, primary_key=True)
    answer_record_id = db.Column(
        db.Integer,
        db.ForeignKey("answer_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    explanation_text = db.Column(
        db.Text,
        nullable=False,
    )
    model_name = db.Column(
        db.String(100),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    answer_record = db.relationship(
        "AnswerRecord",
        back_populates="explanation_records",
    )

    issue_reports = db.relationship(
        "IssueReport",
        back_populates="explanation_record",
        lazy=True,
        foreign_keys="IssueReport.explanation_record_id",
    )


class IssueReport(db.Model):
    """題目／答案與 AI 解析問題回報。"""

    __tablename__ = "issue_reports"

    id = db.Column(db.Integer, primary_key=True)

    # 保留 user 關聯；即使未來刪除 User，也保留回報快照。
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_user_id = db.Column(
        db.String(64),
        nullable=False,
        index=True,
    )

    # 與原始作答／解析紀錄建立可追溯關聯。
    # 使用 SET NULL，避免學習歷程因到期清除時把 QC 回報一起刪除。
    answer_record_id = db.Column(
        db.Integer,
        db.ForeignKey("answer_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    explanation_record_id = db.Column(
        db.Integer,
        db.ForeignKey("explanation_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # question / ai_explanation
    report_type = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )
    issue_category = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    # 回報當下的題目與解析快照。
    subject = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )
    repo = db.Column(
        db.String(100),
        nullable=True,
    )
    question_number = db.Column(
        db.Integer,
        nullable=True,
    )
    question_id = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )
    question_text = db.Column(
        db.Text,
        nullable=False,
    )
    options_json = db.Column(
        db.JSON,
        nullable=True,
    )
    student_answer = db.Column(
        db.String(20),
        nullable=True,
    )
    correct_answer = db.Column(
        db.String(20),
        nullable=True,
    )
    ai_explanation = db.Column(
        db.Text,
        nullable=True,
    )

    user_comment = db.Column(
        db.Text,
        nullable=True,
    )

    # pending / reviewing / resolved / rejected
    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    admin_note = db.Column(
        db.Text,
        nullable=True,
    )
    reviewed_by = db.Column(
        db.String(64),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    user = db.relationship(
        "User",
        back_populates="issue_reports",
        foreign_keys=[user_id],
    )
    answer_record = db.relationship(
        "AnswerRecord",
        back_populates="issue_reports",
        foreign_keys=[answer_record_id],
    )
    explanation_record = db.relationship(
        "ExplanationRecord",
        back_populates="issue_reports",
        foreign_keys=[explanation_record_id],
    )


class ChallengeProfile(db.Model):
    """挑戰模式專用個人資料；與一般學習歷程分開。"""

    __tablename__ = "challenge_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    nickname = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    user = db.relationship(
        "User",
        back_populates="challenge_profile",
    )


class ChallengeAttempt(db.Model):
    """每次挑戰賽的獨立紀錄，不寫入一般 ExamAttempt。"""

    __tablename__ = "challenge_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_count = db.Column(
        db.Integer,
        nullable=False,
        default=30,
    )
    correct_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        index=True,
    )
    score_rate = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )
    time_limit_seconds = db.Column(
        db.Integer,
        nullable=False,
        default=1380,
    )
    elapsed_seconds = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="in_progress",
        index=True,
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    user = db.relationship(
        "User",
        back_populates="challenge_attempts",
    )
    challenge_answers = db.relationship(
        "ChallengeAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="ChallengeAnswer.question_number",
    )


class ChallengeAnswer(db.Model):
    """挑戰賽單題作答快照；不納入弱點分析。"""

    __tablename__ = "challenge_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("challenge_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_number = db.Column(
        db.Integer,
        nullable=False,
    )
    subject = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )
    repo = db.Column(
        db.String(100),
        nullable=True,
    )
    question_id = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )
    question_text = db.Column(
        db.Text,
        nullable=False,
    )
    options_json = db.Column(
        db.JSON,
        nullable=True,
    )
    student_answer = db.Column(
        db.String(10),
        nullable=False,
    )
    correct_answer = db.Column(
        db.String(10),
        nullable=False,
    )
    is_correct = db.Column(
        db.Boolean,
        nullable=False,
        index=True,
    )
    answered_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    attempt = db.relationship(
        "ChallengeAttempt",
        back_populates="challenge_answers",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "attempt_id",
            "question_number",
            name="uq_challenge_answer_attempt_question_number",
        ),
    )
