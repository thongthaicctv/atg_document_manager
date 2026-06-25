from __future__ import annotations

from io import BytesIO
import math
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

from app.config import get_config


ALLOWED_SCAN_EXTENSIONS = {".jpg", ".jpeg", ".png"}
A4_PORTRAIT_300_DPI = (2480, 3508)
A4_LANDSCAPE_300_DPI = (3508, 2480)
PAGE_MARGIN = 90
DETECTION_MAX_SIDE = 900


def _rgb_page(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        transparent = image.convert("RGBA")
        page = Image.new("RGB", transparent.size, "white")
        page.paste(transparent, mask=transparent.getchannel("A"))
        return page
    return image.convert("RGB")


def _enhance_document_image(image: Image.Image) -> Image.Image:
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Sharpness(image).enhance(1.12)
    return image


def _white_document_mask(image: Image.Image) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    pixels = image.load()
    mask_pixels = mask.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if max(r, g, b) > 155 and min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 70:
                mask_pixels[x, y] = 255
    return mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))


def _largest_component(mask: Image.Image) -> tuple[tuple[int, int, int, int], list[tuple[int, int]], int] | None:
    width, height = mask.size
    data = bytearray(1 if value > 0 else 0 for value in mask.tobytes())
    visited = bytearray(len(data))
    best_bbox: tuple[int, int, int, int] | None = None
    best_points: list[tuple[int, int]] = []
    best_count = 0

    for start, value in enumerate(data):
        if not value or visited[start]:
            continue

        stack = [start]
        visited[start] = 1
        count = 0
        min_x = width
        min_y = height
        max_x = 0
        max_y = 0
        points: list[tuple[int, int]] = []

        while stack:
            current = stack.pop()
            count += 1
            x = current % width
            y = current // width
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            points.append((x, y))

            for neighbor in (current - 1, current + 1, current - width, current + width):
                if neighbor < 0 or neighbor >= len(data) or visited[neighbor] or not data[neighbor]:
                    continue
                neighbor_x = neighbor % width
                if abs(neighbor_x - x) > 1:
                    continue
                visited[neighbor] = 1
                stack.append(neighbor)

        if count > best_count:
            best_count = count
            best_bbox = (min_x, min_y, max_x + 1, max_y + 1)
            best_points = points

    if not best_bbox:
        return None
    return best_bbox, best_points, best_count


def _scale_point(point: tuple[int, int], scale: float) -> tuple[float, float]:
    return point[0] / scale, point[1] / scale


def _expand_quad(points: list[tuple[float, float]], image_size: tuple[int, int], factor: float = 0.995) -> list[tuple[float, float]]:
    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)
    max_x, max_y = image_size
    expanded: list[tuple[float, float]] = []
    for x, y in points:
        expanded.append(
            (
                min(max((x - center_x) * factor + center_x, 0), max_x - 1),
                min(max((y - center_y) * factor + center_y, 0), max_y - 1),
            )
        )
    return expanded


def _detected_document_quad(image: Image.Image) -> list[tuple[float, float]] | None:
    scale = min(DETECTION_MAX_SIDE / max(image.size), 1.0)
    small_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    small = image.resize(small_size, Image.Resampling.BILINEAR)
    mask = _white_document_mask(small)
    component = _largest_component(mask)
    if not component:
        return None

    bbox, points, count = component
    width, height = small.size
    box_width = bbox[2] - bbox[0]
    box_height = bbox[3] - bbox[1]
    if count / (width * height) < 0.12 or box_width < width * 0.35 or box_height < height * 0.35:
        return None

    top_left = min(points, key=lambda point: point[0] + point[1])
    bottom_right = max(points, key=lambda point: point[0] + point[1])
    top_right = max(points, key=lambda point: point[0] - point[1])
    bottom_left = min(points, key=lambda point: point[0] - point[1])
    quad = [_scale_point(point, scale) for point in (top_left, top_right, bottom_right, bottom_left)]
    return _expand_quad(quad, image.size)


def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return math.hypot(first[0] - second[0], first[1] - second[1])


def _scan_document_image(image: Image.Image) -> Image.Image:
    image = _rgb_page(image)
    quad = _detected_document_quad(image)
    if not quad:
        return _enhance_document_image(image)

    top_left, top_right, bottom_right, bottom_left = quad
    width_average = (_distance(top_left, top_right) + _distance(bottom_left, bottom_right)) / 2
    height_average = (_distance(top_left, bottom_left) + _distance(top_right, bottom_right)) / 2
    page_size = A4_LANDSCAPE_300_DPI if width_average > height_average else A4_PORTRAIT_300_DPI
    printable_size = (page_size[0] - PAGE_MARGIN * 2, page_size[1] - PAGE_MARGIN * 2)

    # PIL QUAD order is upper-left, lower-left, lower-right, upper-right.
    scanned = image.transform(
        printable_size,
        Image.Transform.QUAD,
        (
            top_left[0],
            top_left[1],
            bottom_left[0],
            bottom_left[1],
            bottom_right[0],
            bottom_right[1],
            top_right[0],
            top_right[1],
        ),
        Image.Resampling.BICUBIC,
    )
    return _enhance_document_image(scanned)


def _a4_pdf_page(image: Image.Image) -> Image.Image:
    image = _scan_document_image(image)
    page_size = A4_LANDSCAPE_300_DPI if image.width > image.height else A4_PORTRAIT_300_DPI
    printable_size = (page_size[0] - PAGE_MARGIN * 2, page_size[1] - PAGE_MARGIN * 2)

    fitted = image.copy()
    fitted.thumbnail(printable_size, Image.Resampling.LANCZOS)

    page = Image.new("RGB", page_size, "white")
    left = (page_size[0] - fitted.width) // 2
    top = (page_size[1] - fitted.height) // 2
    page.paste(fitted, (left, top))
    fitted.close()
    return page


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
                    pil_images.append(_a4_pdf_page(image))
            except UnidentifiedImageError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không đọc được ảnh scan: {upload.filename}") from exc

        if not pil_images:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chưa chọn ảnh để ghép PDF.")

        stem = Path(output_name).stem or "scan"
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"{stem}_", suffix=".pdf") as tmp:
            output_path = Path(tmp.name)

        try:
            first, rest = pil_images[0], pil_images[1:]
            first.save(output_path, "PDF", save_all=True, append_images=rest, resolution=300.0, quality=95)
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        return output_path
    finally:
        for image in pil_images:
            image.close()
