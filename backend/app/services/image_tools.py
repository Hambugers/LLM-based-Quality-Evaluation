from __future__ import annotations

import hashlib
import re
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.schemas import RequestImage


MAX_IMAGES = 8
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def validate_and_save_uploads(upload_files: list[UploadFile], uploads_dir: Path) -> list[RequestImage]:
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if len(upload_files) > MAX_IMAGES:
        raise HTTPException(status_code=422, detail=f"图片数量不能超过 {MAX_IMAGES} 张")

    saved_images: list[RequestImage] = []
    for upload in upload_files:
        suffix = suffix_for_upload(upload.filename)
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="图片格式不受支持，仅允许 PNG/JPG/JPEG/WEBP")

        raw_bytes = upload.file.read()
        if len(raw_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=422, detail="单张图片大小不能超过 10MB")

        try:
            with Image.open(BytesIO(raw_bytes)) as image:
                detected_kind = (image.format or "").lower()
                width, height = image.size
        except OSError as exc:
            raise HTTPException(status_code=422, detail="图片无法解析，请重新上传有效文件") from exc
        if detected_kind == "jpeg":
            detected_kind = "jpg"
        if detected_kind not in {"png", "jpg", "webp"}:
            raise HTTPException(status_code=422, detail="图片内容校验失败，文件格式不正确")

        safe_name = sanitize_filename(upload.filename)
        target_path = uploads_dir / safe_name
        target_path.write_bytes(raw_bytes)

        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        saved_images.append(
            RequestImage(
                filename=safe_name,
                content_type=upload.content_type or "application/octet-stream",
                saved_path=target_path,
                size_bytes=len(raw_bytes),
                width=width,
                height=height,
                sha256=sha256,
                url=f"/uploads/{safe_name}",
            )
        )

    return saved_images


def build_image_quality_result(images: list[RequestImage]) -> dict[str, object]:
    if not images:
        return {
            "score": 0.0,
            "image_count": 0,
            "invalid_count": 0,
            "duplicate_ratio": 0.0,
            "summary": "未上传图片。",
            "images": [],
        }

    duplicate_count = len(images) - len({image.sha256 for image in images})
    duplicate_ratio = duplicate_count / len(images)
    very_small_count = sum(1 for image in images if min(image.width, image.height) < 120)
    size_penalty = min(0.4, (duplicate_ratio * 0.35) + ((very_small_count / len(images)) * 0.2))
    score = max(0.0, round(0.95 - size_penalty, 4))

    return {
        "score": score,
        "image_count": len(images),
        "invalid_count": 0,
        "duplicate_ratio": round(duplicate_ratio, 4),
        "summary": f"共检测 {len(images)} 张图片，重复比例 {duplicate_ratio:.2f}。",
        "images": [
            {
                "name": image.filename,
                "url": image.url,
                "size_bytes": image.size_bytes,
                "width": image.width,
                "height": image.height,
                "sha256": image.sha256,
            }
            for image in images
        ],
    }


def suffix_for_upload(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].strip().lower()


def sanitize_filename(filename: str | None) -> str:
    raw_name = filename or "upload.png"
    stem, _, suffix = raw_name.rpartition(".")
    stem = stem or "upload"
    cleaned_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", stem).strip("_") or "upload"
    cleaned_suffix = suffix.lower() if suffix else "png"
    return f"{cleaned_stem}.{cleaned_suffix}"
