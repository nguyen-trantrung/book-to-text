import click
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent / "book-to-text"))

from fs import LocalFileSystem, ObjectStorageFileSystem, FileSystem
from converter import PyvipsConverter, Converter
from ocr import PaddleVietOCR, PaddleVLM, OCR
from output import YAMLOutput, Output
from pipeline import run_pipeline
from logger import get_logger

logger = get_logger(__name__)


def validate_directories(input_dir: str, output_dir: str) -> Tuple[Path, Path]:
    """Validate input and output directories.

    Args:
        input_dir: Path to input directory
        output_dir: Path to output directory

    Returns:
        Tuple of (input_path, output_path)

    Raises:
        click.ClickException: If validation fails
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Check input directory exists
    if not input_path.exists():
        raise click.ClickException(f"Input directory does not exist: {input_dir}")

    if not input_path.is_dir():
        raise click.ClickException(f"Input path is not a directory: {input_dir}")

    # Check for PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    if len(pdf_files) == 0:
        logger.warning(f"No PDF files found in {input_dir}")
    else:
        logger.info(f"Found {len(pdf_files)} PDF files")

    # Create output directory if needed
    if not output_path.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_path.mkdir(parents=True, exist_ok=True)

    return input_path, output_path


def create_components(
    storage: str,
    input_dir: str,
    output_dir: str,
    converter_type: str,
    ocr_type: str,
    output_type: str,
    dpi: int,
    s3_endpoint: Optional[str] = None,
    s3_region: Optional[str] = None,
    s3_key: Optional[str] = None,
    s3_secret: Optional[str] = None,
) -> Tuple[FileSystem, FileSystem, Converter, OCR, Output]:
    """Create and configure pipeline components.

    Args:
        storage: Storage backend type (local, s3)
        input_dir: Input directory path
        output_dir: Output directory path
        converter_type: Converter type (pyvips)
        ocr_type: OCR engine type (paddle, paddle_vlm)
        output_type: Output format (yaml, sqlite)
        dpi: DPI for PDF to image conversion
        s3_endpoint: S3 endpoint URL (for s3 storage)
        s3_region: S3 region (for s3 storage)
        s3_key: S3 access key (for s3 storage)
        s3_secret: S3 secret key (for s3 storage)

    Returns:
        Tuple of (src_fs, dest_fs, converter, ocr_engine, output)
    """
    # Set up filesystems
    if storage == "local":
        src_fs = LocalFileSystem(input_dir)
        dest_fs = LocalFileSystem(output_dir)
    elif storage == "s3":
        if not all([s3_endpoint, s3_region, s3_key, s3_secret]):
            raise click.ClickException(
                "S3 storage requires --s3-endpoint, --s3-region, --s3-key, --s3-secret"
            )
        src_fs = ObjectStorageFileSystem(
            input_dir, s3_key, s3_secret, s3_region, s3_endpoint
        )
        dest_fs = ObjectStorageFileSystem(
            output_dir, s3_key, s3_secret, s3_region, s3_endpoint
        )
    else:
        raise click.ClickException(f"Unknown storage: {storage}")

    # Set up converter
    if converter_type == "pyvips":
        conv = PyvipsConverter(dpi=dpi)
    else:
        raise click.ClickException(f"Unknown converter: {converter_type}")

    # Set up OCR
    if ocr_type == "paddle":
        ocr_engine = PaddleVietOCR()
    elif ocr_type == "paddle_vlm":
        ocr_engine = PaddleVLM()
    else:
        raise click.ClickException(f"Unknown OCR engine: {ocr_type}")

    # Set up output
    if output_type == "yaml":
        output = YAMLOutput(dest_fs)
    elif output_type == "sqlite":
        raise click.ClickException("SQLite output not yet implemented")
    else:
        raise click.ClickException(f"Unknown output type: {output_type}")

    return src_fs, dest_fs, conv, ocr_engine, output


def bootstrap_run_pipeline(
    input_directory: str,
    output_directory: str,
    converter: str = "pyvips",
    ocr: str = "paddle",
    output_type: str = "yaml",
    storage: str = "local",
    dpi: int = 300,
    verbose: bool = False,
    dry_run: bool = False,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    s3_endpoint: Optional[str] = None,
    s3_region: Optional[str] = None,
    s3_key: Optional[str] = None,
    s3_secret: Optional[str] = None,
) -> None:
    """Bootstrap and run the full pipeline programmatically.

    This function can be called from other Python code to run the pipeline
    without using the CLI.

    Args:
        input_directory: Path to input directory containing PDFs
        output_directory: Path to output directory
        converter: PDF to image converter (pyvips)
        ocr: OCR engine (paddle, paddle_vlm)
        output_type: Output format (yaml, sqlite)
        storage: Storage backend (local, s3)
        dpi: DPI for PDF to image conversion (default: 300)
        verbose: Enable verbose logging
        dry_run: Validate setup without processing
        start_page: Start from this page number (0-indexed)
        end_page: Stop at this page number (0-indexed)
        s3_endpoint: S3 endpoint URL (for s3 storage)
        s3_region: S3 region (for s3 storage)
        s3_key: S3 access key (for s3 storage)
        s3_secret: S3 secret key (for s3 storage)
    """
    if verbose:
        logger.setLevel("DEBUG")

    logger.info(f"Bootstrapping pipeline: {input_directory} -> {output_directory}")

    # Validate directories
    validate_directories(input_directory, output_directory)

    if dry_run:
        logger.info("Dry run mode - validation complete, skipping processing")
        return

    # Create components
    src_fs, dest_fs, conv, ocr_engine, output = create_components(
        storage=storage,
        input_dir=input_directory,
        output_dir=output_directory,
        converter_type=converter,
        ocr_type=ocr,
        output_type=output_type,
        dpi=dpi,
        s3_endpoint=s3_endpoint,
        s3_region=s3_region,
        s3_key=s3_key,
        s3_secret=s3_secret,
    )

    # Run pipeline
    run_pipeline(
        src_fs,
        dest_fs,
        conv,
        ocr_engine,
        output,
        start_page=start_page,
        end_page=end_page,
    )
    logger.info("Pipeline completed")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Book to Text converter CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose mode enabled")


@cli.command()
@click.argument("input_directory")
@click.argument("output_directory")
@click.option(
    "--converter",
    type=click.Choice(["pyvips"], case_sensitive=False),
    default="pyvips",
    help="PDF to image converter (default: pyvips)",
)
@click.option(
    "--ocr",
    type=click.Choice(["paddle", "paddle_vlm"], case_sensitive=False),
    default="paddle",
    help="OCR engine (default: paddle)",
)
@click.option(
    "--output-type",
    type=click.Choice(["yaml", "sqlite"], case_sensitive=False),
    default="yaml",
    help="Output format (default: yaml)",
)
@click.option(
    "--storage",
    type=click.Choice(["local", "s3"], case_sensitive=False),
    default="local",
    help="Storage backend (default: local)",
)
@click.option(
    "--dpi",
    type=int,
    default=300,
    help="DPI for PDF to image conversion (default: 300)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate setup without processing",
)
@click.option(
    "--start-page",
    type=int,
    default=None,
    help="Start from this page number (0-indexed)",
)
@click.option(
    "--end-page",
    type=int,
    default=None,
    help="Stop at this page number (0-indexed)",
)
@click.option("--s3-endpoint", help="S3 endpoint URL")
@click.option("--s3-region", help="S3 region")
@click.option("--s3-key", help="S3 access key")
@click.option("--s3-secret", help="S3 secret key")
@click.pass_context
def run(
    ctx: click.Context,
    input_directory: str,
    output_directory: str,
    converter: str,
    ocr: str,
    output_type: str,
    storage: str,
    dpi: int,
    dry_run: bool,
    start_page: Optional[int],
    end_page: Optional[int],
    s3_endpoint: Optional[str],
    s3_region: Optional[str],
    s3_key: Optional[str],
    s3_secret: Optional[str],
):
    """Run the full pipeline: PDF -> Images -> Text."""
    try:
        bootstrap_run_pipeline(
            input_directory=input_directory,
            output_directory=output_directory,
            converter=converter,
            ocr=ocr,
            output_type=output_type,
            storage=storage,
            dpi=dpi,
            verbose=ctx.obj.get("verbose", False),
            dry_run=dry_run,
            start_page=start_page,
            end_page=end_page,
            s3_endpoint=s3_endpoint,
            s3_region=s3_region,
            s3_key=s3_key,
            s3_secret=s3_secret,
        )
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.argument("input_directory", required=False)
def debug(input_directory: Optional[str]):
    """Prints all the configuration and environment details.

    Optionally validates an input directory.
    """
    import platform
    import sys

    click.echo("=" * 50)
    click.echo("Debug Information")
    click.echo("=" * 50)
    click.echo(f"Python version: {sys.version}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Python path: {sys.executable}")

    # Check optional dependencies
    deps = [
        ("click", "click"),
        ("pyvips", "pyvips"),
        ("pdf2image", "pdf2image"),
        ("numpy", "numpy"),
        ("yaml", "pyyaml"),
        ("boto3", "boto3"),
        ("paddle", "paddlepaddle"),
        ("paddleocr", "paddleocr"),
        ("PIL", "pillow"),
    ]

    click.echo("\nDependencies:")
    for module_name, pkg_name in deps:
        try:
            __import__(module_name)
            click.echo(f"  {pkg_name}: OK")
        except ImportError:
            click.echo(f"  {pkg_name}: NOT INSTALLED")

    # Validate directory if provided
    if input_directory:
        click.echo(f"\nValidating directory: {input_directory}")
        try:
            input_path, _ = validate_directories(input_directory, "/tmp/validation_output")
            pdf_files = list(input_path.glob("*.pdf"))
            click.echo(f"  Directory exists: YES")
            click.echo(f"  PDF files found: {len(pdf_files)}")
            for pdf in pdf_files[:5]:
                click.echo(f"    - {pdf.name}")
            if len(pdf_files) > 5:
                click.echo(f"    ... and {len(pdf_files) - 5} more")
        except click.ClickException as e:
            click.echo(f"  Validation failed: {e}")

    click.echo("=" * 50)


if __name__ == "__main__":
    cli()
