# Wildlife Camera Processor

A Python CLI tool for processing wildlife camera images using PyTorch Wildlife for animal detection and classification.

## Features

- Process directories of wildlife camera images
- Extract location and timestamp from directory structure
- Use PyTorch Wildlife MegaDetectorV6 for animal detection
- Support regional classification models (Amazon, Europe, Hamelin)
- Output structured JSON results with metadata
- CLI interface with progress indicators

## Installation

This project uses UV as the Python package manager. Install UV first:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project:

```bash
# Clone and install
git clone <repository-url>
cd wildlife-camera-processor

# Install dependencies
uv sync

# Install PyTorch Wildlife (required for processing)
uv add PytorchWildlife

# Validate installation
python validate_installation.py

# Test core components
python test_workflow.py
```

## Usage

```bash
# Process a directory with default settings
uv run wildlife-processor /path/to/camera/images

# Use a specific regional model
uv run wildlife-processor /path/to/camera/images --model-region amazon

# Specify output file
uv run wildlife-processor /path/to/camera/images --output results.json

# List available models
uv run wildlife-processor list-models
```

## Directory Structure

The tool expects wildlife camera images organized as:
```
/locationName/datetime/image1.jpeg
/locationName/datetime/image2.jpeg
```

Example:
```
/forest_trail_1/2024-01-15_08-30/IMG_001.jpg
/forest_trail_1/2024-01-15_14-22/IMG_002.jpg
/meadow_cam_2/2024-01-16_06-45/IMG_003.jpg
```

## Output Format

Results are saved as JSON with the following structure:
```json
{
  "processing_metadata": {
    "total_images": 150,
    "successful_detections": 147,
    "failed_images": ["path1.jpg", "path2.jpg"],
    "processing_duration": 45.2,
    "model_info": {
      "detection_model": "MegaDetectorV6",
      "classification_model": "AI4GAmazonRainforest",
      "region": "amazon"
    }
  },
  "results_by_camera": {
    "forest_trail_1": [
      {
        "image_path": "/forest_trail_1/2024-01-15_08-30/IMG_001.jpg",
        "camera_reference": "forest_trail_1",
        "timestamp": "2024-01-15T08:30:00",
        "detections": [
          {
            "species": "jaguar",
            "confidence": 0.87,
            "bounding_box": {"x": 100, "y": 150, "width": 200, "height": 180},
            "classification_model": "AI4GAmazonRainforest",
            "is_uncertain": false
          }
        ],
        "processing_time": 2.3
      }
    ]
  }
}
```
##
 Development and Testing

### Validation Scripts

The project includes validation scripts to test the installation and core functionality:

```bash
# Validate installation and dependencies
python validate_installation.py

# Test core workflow components (without PyTorch Wildlife)
python test_workflow.py

# Validate CLI setup
uv run wildlife-processor validate-setup
```

### Project Structure

```
wildlife_processor/
├── cli/                    # CLI interface (Typer)
│   └── main.py
├── core/                   # Core processing components
│   ├── data_models.py      # Data structures
│   ├── models.py           # PyTorch Wildlife integration
│   ├── processor.py        # Main processing engine
│   └── directory_scanner.py # Directory scanning
├── postprocessing/         # Result enrichment
│   └── location_enricher.py
├── utils/                  # Utilities
│   ├── image_utils.py      # Image processing
│   ├── json_output.py      # JSON formatting
│   └── error_handler.py    # Error handling
└── config/                 # Configuration
    └── models_config.py    # Regional model configs
```

### Adding New Regional Models

To add support for new regional models:

1. Update `wildlife_processor/config/models_config.py`
2. Add the new model configuration to `REGIONAL_MODELS`
3. Update the model loading logic in `wildlife_processor/core/models.py`

### Error Handling

The system includes comprehensive error handling:

- **Image errors**: Corrupted files, unsupported formats, permission issues
- **Model errors**: Installation problems, network issues, memory constraints
- **Directory errors**: Invalid paths, permission problems
- **Output errors**: Write permissions, disk space issues
- **Timeout errors**: Processing time limits

Use `--verbose` flag for detailed error information and troubleshooting guidance.

## Troubleshooting

### Common Issues

1. **PyTorch Wildlife not found**
   ```bash
   uv add PytorchWildlife
   ```

2. **CUDA/GPU errors**
   - The system automatically falls back to CPU processing
   - Ensure PyTorch is properly installed: `uv add torch torchvision`

3. **Memory errors**
   - Process smaller image batches
   - Increase timeout with `--timeout` parameter
   - Close other applications to free memory

4. **Permission errors**
   - Check read permissions for input directory
   - Check write permissions for output location
   - Try different output directory

5. **Network errors during model download**
   - Check internet connection
   - Try again later if servers are busy
   - Check firewall settings

### Getting Help

- Run validation: `python validate_installation.py`
- Test setup: `uv run wildlife-processor validate-setup`
- Use verbose mode: `--verbose` flag
- Check logs for detailed error information