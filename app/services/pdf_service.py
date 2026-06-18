from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image


async def images_to_pdf(images: list[UploadFile], output_name: str = "scan.pdf") -> Path:
    pil_images: list[Image.Image] = []
    for upload in images:
        if not upload or not upload.filename:
            continue
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ ghép PDF từ ảnh jpg, jpeg, png.")
        content = await upload.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            image = Image.open(tmp_path)
            pil_images.append(image.convert("RGB"))
        finally:
            tmp_path.unlink(missing_ok=True)

    if not pil_images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chưa chọn ảnh để ghép PDF.")

    output_path = Path(tempfile.gettempdir()) / output_name
    first, rest = pil_images[0], pil_images[1:]
    first.save(output_path, save_all=True, append_images=rest)
    for image in pil_images:
        image.close()
    return output_path

