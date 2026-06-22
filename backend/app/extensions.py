from __future__ import annotations

import boto3
import redis
from botocore.client import BaseClient
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_recycle=3600, pool_size=10, max_overflow=20)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
db_session = scoped_session(SessionLocal)

redis_client: redis.Redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

socketio = SocketIO(
    cors_allowed_origins=settings.FRONTEND_URL,
    message_queue=settings.REDIS_URL if settings.is_production else None,
    async_mode="gevent" if settings.is_production else "threading",
    logger=False,
    engineio_logger=False,
)

cors = CORS()


def get_s3_client() -> BaseClient:
    return boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
