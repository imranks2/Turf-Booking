from __future__ import annotations

import uuid

from werkzeug.datastructures import FileStorage

from app.config import settings
from app.exceptions import ValidationFailed
from app.extensions import get_s3_client

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _validate_image(file: FileStorage) -> None:
    if file.mimetype not in ALLOWED_CONTENT_TYPES:
        raise ValidationFailed("Only JPG and PNG images are allowed")
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise ValidationFailed("Each image must be 5MB or smaller")


def upload_turf_image(turf_id: str, file: FileStorage) -> str:
    _validate_image(file)
    ext = "png" if file.mimetype == "image/png" else "jpg"
    key = f"turfs/{turf_id}/{uuid.uuid4()}.{ext}"
    get_s3_client().upload_fileobj(
        file.stream, settings.S3_BUCKET, key, ExtraArgs={"ContentType": file.mimetype}
    )
    return key


def upload_player_image(player_id: str, file: FileStorage) -> str:
    _validate_image(file)
    ext = "png" if file.mimetype == "image/png" else "jpg"
    key = f"players/{player_id}/{uuid.uuid4()}.{ext}"
    get_s3_client().upload_fileobj(
        file.stream, settings.S3_BUCKET, key, ExtraArgs={"ContentType": file.mimetype}
    )
    return key


def presigned_url(key: str, expires: int = 3600) -> str:
    return get_s3_client().generate_presigned_url(
        "get_object", Params={"Bucket": settings.S3_BUCKET, "Key": key}, ExpiresIn=expires
    )
