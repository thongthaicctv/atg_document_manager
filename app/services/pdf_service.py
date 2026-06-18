from __future__ import annotations

from io import BytesIO
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import get_config


ALLOWED_SCAN_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _rgb_page(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        transparent = image.convert("RGBA")
        page = Image.new("RGB", transparent.size, "white")
        page.paste(transparent, mask=transparent.getchannel("A"))
        return page
    return image.convert("RGB")


async def images_to_pdf(images: list[UploadFile], output_name: str = "scan.pdf") -> Path:
    pil_images: list[Image.Image] = []
    try:
        max_bytes = int(get_config()["storage"]["max_file_size_mb"]) * 1024 * 1024
        for upload in images:
            if not upload or not upload.filename:
                continue
            suffix = Path(upload.filename).suffix.lower()
            if suffix not in ALLOWED_SCAN_EXTENSIONS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ ghép PDF từ ảnh jpg, jpeg, png.")

            content = await upload.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Ảnh scan vượt quá dung lượng cho phép.")

            try:
                with Image.open(BytesIO(content)) as image:
                    pil_images.append(_rgb_page(image))
            except UnidentifiedImageError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không đọc được ảnh scan: {upload.filename}") from exc

        if not pil_images:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chưa chọn ảnh để ghép PDF.")

        stem = Path(output_name).stem or "scan"
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"{stem}_", suffix=".pdf") as tmp:
            output_path = Path(tmp.name)

        try:
            first, rest = pil_images[0], pil_images[1:]
            first.save(output_path, "PDF", save_all=True, append_images=rest, resolution=200.0)
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        return output_path
    finally:
        for image in pil_images:
            image.close()
