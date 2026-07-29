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
