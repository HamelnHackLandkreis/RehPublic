"""CLI interface for wildlife camera processor using Typer."""

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from wildlife_processor.config.models_config import (
    get_model_description,
    list_available_regions,
    validate_region,
    get_default_region,
)
from wildlife_processor.core.processor import WildlifeProcessor
from wildlife_processor.utils.json_output import JSONOutputHandler

# Create Typer app
app = typer.Typer(
    name="wildlife-processor",
    help="Process wildlife camera images using PyTorch Wildlife for animal detection and classification.",
    add_completion=False,
)

# Rich console for output
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def process_directory(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing wildlife camera images organized as /location/datetime/image.jpg",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    model_region: str = typer.Option(
        get_default_region(),
        "--model-region",
        "-r",
        help="Regional model to use for classification (amazon, europe, hamelin, general)",
    ),
    output: Path = typer.Option(
        "results.json", "--output", "-o", help="Output JSON file path for results"
    ),
    progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Show progress indicators during processing",
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Maximum processing time per image in seconds"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Process a directory of wildlife camera images for animal detection and classification.

    The tool expects images organized in the following structure:
    /locationName/datetime/image.jpg

    Example:
    /forest_trail_1/2024-01-15_08-30/IMG_001.jpg
    /meadow_cam_2/2024-01-16_14-22/IMG_002.jpg

    Results are saved as JSON with detection results grouped by camera location.
    """
    setup_logging(verbose)

    # Validate model region
    if not validate_region(model_region):
        console.print(f"[red]Error:[/red] Invalid model region '{model_region}'")
        console.print(f"Available regions: {', '.join(list_available_regions())}")
        console.print(
            "Use 'wildlife-processor list-models' to see detailed information."
        )
        raise typer.Exit(1)

    # Validate directory
    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise typer.Exit(1)

    if not directory.is_dir():
        console.print(f"[red]Error:[/red] Path is not a directory: {directory}")
        raise typer.Exit(1)

    try:
        console.print("[green]Starting wildlife camera processing...[/green]")
        console.print(f"Directory: {directory}")
        console.print(f"Model region: {model_region}")
        console.print(f"Output file: {output}")
        console.print()

        # Initialize processor
        processor = WildlifeProcessor(
            model_region=model_region, timeout_per_image=timeout
        )

        # Process directory
        results = processor.process_directory(directory, show_progress=progress)

        # Save results to JSON
        json_handler = JSONOutputHandler()
        json_handler.save_results(results, output)

        # Display summary
        _display_processing_summary(results, processor)

        console.print("[green]✓[/green] Processing completed successfully!")
        console.print(f"Results saved to: {output}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Processing interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during processing:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("list-models")
def list_models() -> None:
    """List available regional models and their geographic coverage."""
    console.print("[bold]Available Regional Models:[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Region", style="cyan")
    table.add_column("Model Name", style="green")
    table.add_column("Geographic Coverage", style="yellow")

    regions = list_available_regions()
    for region in regions:
        description = get_model_description(region)
        # Parse description to get model name and coverage
        if " - " in description:
            model_name, coverage = description.split(" - ", 1)
        else:
            model_name = description
            coverage = "Not specified"

        table.add_row(region, model_name, coverage)

    console.print(table)
    console.print(f"\nDefault region: [cyan]{get_default_region()}[/cyan]")
    console.print("\nUse --model-region to specify which regional model to use.")


@app.command()
def validate_setup() -> None:
    """Validate that PyTorch Wildlife models can be loaded and are working correctly."""
    setup_logging(verbose=True)

    console.print("[bold]Validating PyTorch Wildlife setup...[/bold]\n")

    try:
        # Test each available region
        regions = list_available_regions()

        for region in regions:
            console.print(f"Testing region: [cyan]{region}[/cyan]")

            try:
                processor = WildlifeProcessor(model_region=region)

                # This will load and validate the models
                if processor.model_manager.validate_models():
                    console.print(
                        f"  [green]✓[/green] {region} models loaded successfully"
                    )
                else:
                    console.print(f"  [red]✗[/red] {region} model validation failed")

            except Exception as e:
                console.print(f"  [red]✗[/red] {region} failed: {e}")

        console.print("\n[green]Setup validation completed![/green]")

    except Exception as e:
        console.print(f"[red]Setup validation failed:[/red] {e}")
        console.print("\nPlease ensure PyTorch Wildlife is properly installed:")
        console.print("  uv add PytorchWildlife")
        raise typer.Exit(1)


def _display_processing_summary(results, processor) -> None:
    """Display processing summary statistics.

    Args:
        results: ProcessingResults object
        processor: WildlifeProcessor instance
    """
    console.print("\n[bold]Processing Summary:[/bold]")

    # Basic statistics
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total images", str(results.total_images))
    table.add_row("Successful detections", str(results.successful_detections))
    table.add_row("Failed images", str(len(results.failed_images)))
    table.add_row("Processing duration", f"{results.processing_duration:.2f}s")
    table.add_row("Cameras found", str(len(results.results_by_camera)))

    # Calculate total detections
    total_detections = sum(
        len(result.detections)
        for camera_results in results.results_by_camera.values()
        for result in camera_results
    )
    table.add_row("Total animal detections", str(total_detections))

    console.print(table)

    # Performance statistics
    stats = processor.get_processing_statistics()
    if stats["total_images_processed"] > 0:
        console.print("\n[bold]Performance:[/bold]")
        console.print(f"Average time per image: {stats['average_time_per_image']:.2f}s")
        console.print(f"Fastest image: {stats['min_time']:.2f}s")
        console.print(f"Slowest image: {stats['max_time']:.2f}s")

    # Model information
    console.print("\n[bold]Models used:[/bold]")
    console.print(f"Detection: {results.model_info.detection_model}")
    console.print(f"Classification: {results.model_info.classification_model}")
    console.print(f"Region: {results.model_info.region}")

    # Failed images (if any)
    if results.failed_images:
        console.print(
            f"\n[yellow]Warning:[/yellow] {len(results.failed_images)} images failed to process"
        )
        if len(results.failed_images) <= 5:
            for failed_file in results.failed_images:
                console.print(f"  - {failed_file}")
        else:
            for failed_file in results.failed_images[:3]:
                console.print(f"  - {failed_file}")
            console.print(f"  ... and {len(results.failed_images) - 3} more")


if __name__ == "__main__":
    app()
