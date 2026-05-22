# Book To Text

Converts a directory of PDF books into structured data.

## Usage

### Run Command

```bash
# Basic usage - process all PDFs
python main.py run ./input ./output

# With all options
python main.py run ./input ./output \
    --converter pyvips \
    --ocr paddle \
    --output-type yaml \
    --storage local \
    --dpi 300 \
    --start-page 0 \
    --end-page 10 \
    --verbose
```

### CLI Options

**Global:**
- `-v, --verbose`: Enable verbose logging

**Run command:**
- `input_directory`: Path to input directory containing PDFs
- `output_directory`: Path to output directory
- `--converter`: PDF converter (`pyvips`)
- `--ocr`: OCR engine (`paddle`, `paddle_vlm`)
- `--output-type`: Output format (`yaml`, `sqlite`)
- `--storage`: Storage backend (`local`, `s3`)
- `--dpi`: DPI for PDF conversion (default: 300)
- `--dry-run`: Validate without processing
- `--start-page`: Start from page N (0-indexed)
- `--end-page`: Stop at page N (0-indexed)
- `--s3-endpoint`: S3 endpoint URL
- `--s3-region`: S3 region
- `--s3-key`: S3 access key
- `--s3-secret`: S3 secret key

### Debug Command

```bash
# Show system info
python main.py debug

# With directory validation
python main.py debug ./input
```

### Programmatic Usage

```python
from main import bootstrap_run_pipeline

bootstrap_run_pipeline(
    input_directory="./input",
    output_directory="./output",
    converter="pyvips",
    ocr="paddle",
    output_type="yaml",
    storage="local",
    dpi=300,
    verbose=False,
    dry_run=False,
    start_page=0,
    end_page=10,
)
```

## Install

```bash
pip install -r requirements.txt
```

## Dependencies

- `click`: CLI framework
- `pyvips`: Image processing
- `pdf2image`: PDF to image conversion
- `numpy`: Array handling
- `pyyaml`: YAML output
- `pillow`: Image manipulation
- `boto3`: S3 storage (optional)
- `paddlepaddle`, `paddleocr`: OCR engine

## System Requirements

- Python 3.8+
- poppler (for pdf2image):
  - macOS: `brew install poppler`
  - Ubuntu: `apt-get install poppler-utils`
- Tesseract (optional, for OCR):
  - macOS: `brew install tesseract`
  - Ubuntu: `apt-get install tesseract-ocr`
