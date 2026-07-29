import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


db = SQLAlchemy()


def normalize_database_url(database_url: str) -> str:
    """
    將舊式 postgres:// 連線字串轉成 SQLAlchemy 可接受的 postgresql://。
    Render 通常會提供 postgresql://，此函式可兼容舊格式。
    """
    cleaned_url = str(database_url or "").strip()

    if cleaned_url.startswith("postgres://"):
        cleaned_url = cleaned_url.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    return cleaned_url


def init_database(app) -> None:
    """
    將 Flask 應用程式連接到 PostgreSQL。

    此階段只負責：
    1. 讀取 DATABASE_URL
    2. 初始化 Flask-SQLAlchemy
    3. 測試資料庫連線

    尚不會建立資料表。
    """
    database_url = normalize_database_url(
        os.getenv("DATABASE_URL", "")
    )

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    db.init_app(app)

    with app.app_context():
        db.session.execute(text("SELECT 1"))
        db.session.commit()

    app.logger.info(
        "PostgreSQL connection test completed successfully."
    )
