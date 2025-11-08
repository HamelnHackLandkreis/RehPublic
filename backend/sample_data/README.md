# Sample Wildlife Camera Data

This directory contains sample data for testing the wildlife camera processor.

## Directory Structure

The sample data follows the expected structure:
```
/locationName/datetime/image.jpg
```

Example structure:
```
sample_data/
├── forest_trail_1/
│   ├── 2024-01-15_08-30/
│   │   ├── IMG_001.jpg
│   │   └── IMG_002.jpg
│   └── 2024-01-15_14-22/
│       └── IMG_003.jpg
├── meadow_cam_2/
│   ├── 2024-01-16_06-45/
│   │   └── IMG_004.jpg
│   └── 2024-01-16_18-30/
│       ├── IMG_005.jpg
│       └── IMG_006.jpg
└── river_crossing/
    └── 2024-01-17_12-15/
        └── IMG_007.jpg
```

## Testing the Processor

To test with this sample data:

```bash
# Process the sample directory
uv run wildlife-processor sample_data --output sample_results.json

# Use a specific regional model
uv run wildlife-processor sample_data --model-region amazon --output amazon_results.json

# Enable verbose logging
uv run wildlife-processor sample_data --verbose --output verbose_results.json
```

## Creating Your Own Test Data

To create your own test data:

1. Create directories following the `/location/datetime/` structure
2. Place wildlife camera images in the appropriate directories
3. Supported formats: JPEG, JPG, PNG, TIFF
4. Datetime directories can use various formats:
   - `2024-01-15_08-30`
   - `2024-01-15T08:30:00`
   - `20240115_0830`
   - `2024_01_15_08_30`

## Note on Sample Images

The actual image files are not included in this repository due to size constraints.
To test with real images:

1. Add your own wildlife camera images to the directory structure
2. Or download sample wildlife images from public datasets
3. Ensure images are in supported formats (JPEG, PNG, TIFF)

The processor will work with any images, but wildlife camera images will give the most meaningful results.