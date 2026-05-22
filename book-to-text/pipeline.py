from time import time
from typing import List, Dict, Any, Optional

from fs import FileInput, FileSystem
from converter import PDF, Converter
from ocr import OCR
from logger import get_logger
from output import Output

logger = get_logger(__name__)


def run_pipeline(
        src: FileSystem,
        dest: FileSystem,
        converter: Converter,
        ocr: OCR,
        output: Output,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
) -> None:
    """Run the full pipeline: PDF -> Images -> Text.

    Args:
        src: Source filesystem
        dest: Destination filesystem
        converter: PDF to image converter
        ocr: OCR engine
        output: Output handler
        start_page: Start from this page number (0-indexed), applies to all files
        end_page: Stop at this page number (0-indexed), applies to all files
    """
    pdfs = src.ls()
    to_convert = _need_continue(pdfs, dest)
    if len(to_convert) == 0:
        logger.info("No files to convert")
        return
    logger.info(f"Found {len(to_convert)} files to convert")
    for file in to_convert:
        _handle_file(
            file,
            src,
            dest,
            converter,
            ocr,
            output,
            start_page=start_page,
            end_page=end_page,
        )
    logger.info(f"Handled {len(to_convert)} files")


def _need_continue(files: List[str], dest: FileSystem) -> List[Dict[str, Any]]:
    dirs = dest.ls()
    done = set(dirs)
    need = []
    for f in files:
        if f not in done:
            need.append({
                "name": f,
                "status": "begin"
            })
            continue
        pages = dest.ls(f)

        if len(pages) == 0:
            need.append({
                "name": f,
                "status": "begin"
            })
            continue

        need.append({
            "name": f,
            "status": "incomplete",
            "checkpoint": len(pages)
        })
    return need


def _handle_file(
    file: Dict[str, Any],
    src: FileSystem,
    dest: FileSystem,
    converter: Converter,
    ocr: OCR,
    output: Output,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
) -> None:
    file_bytes = src.read(file["name"])
    pdf = PDF(file["name"], file_bytes)

    # Calculate page range
    effective_start = start_page if start_page is not None else 0
    effective_end = end_page

    images = converter.convert(
        input=pdf,
        start_page=effective_start,
        end_page=effective_end,
    )
    logger.info(f"Converted {file['name']} to {len(images)} images")

    # Determine resume point
    if file["status"] == "begin":
        resume_start = 0
    elif file["status"] == "incomplete":
        resume_start = file["checkpoint"] + 1
    else:
        resume_start = 0

    # Apply CLI page limits to resume point
    start = max(resume_start, effective_start)
    end = effective_end if effective_end is not None else len(images)

    for i in range(start, min(end, len(images))):
        start_time = time()
        image = images[i]

        # Convert numpy array to PNG bytes
        img_data = _image_to_png_bytes(image.get_data())
        dest.put(FileInput(f"images/{file['name']}/{i}.png", img_data))

        page = ocr.ocr(image)
        end_time = time()
        logger.info(
            f"OCR {image.get_name()} page {i} in {end_time - start_time:.2f} seconds")
        if page:
            page.number = i
            output.add(page)


def _image_to_png_bytes(img_data) -> bytes:
    """Convert numpy array image to PNG bytes."""
    from io import BytesIO
    from PIL import Image
    import numpy as np

    if isinstance(img_data, np.ndarray):
        # Handle numpy array (H, W, C) or (H, W)
        if len(img_data.shape) == 3:
            # RGB/RGBA image
            mode = "RGB" if img_data.shape[2] == 3 else "RGBA"
            pil_img = Image.fromarray(img_data, mode=mode)
        else:
            # Grayscale
            pil_img = Image.fromarray(img_data, mode="L")
    else:
        pil_img = img_data

    buffer = BytesIO()
    pil_img.save(buffer, format="PNG")
    return buffer.getvalue()
