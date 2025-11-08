# Wildlife Camera Processor Design Document

## Overview

The Wildlife Camera Processor is a Python CLI application built with Typer that processes directories of wildlife camera images using Microsoft's PyTorch Wildlife framework. The system combines MegaDetectorV6 for animal detection with regional classification models to identify species, then enriches results with camera location metadata and outputs structured JSON reports.

The application follows a modular architecture with separate components for CLI handling, image processing, model management, and postprocessing to ensure maintainability and extensibility.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Layer     │───▶│  Processing      │───▶│  Output Layer   │
│   (Typer)       │    │  Engine          │    │  (JSON)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  PyTorch         │
                       │  Wildlife        │
                       │  Models          │
                       └──────────────────┘
```

### Component Architecture

```
wildlife_processor/
├── cli/
│   ├── __init__.py
│   └── main.py              # Typer CLI interface
├── core/
│   ├── __init__.py
│   ├── processor.py         # Main processing engine
│   ├── models.py           # PyTorch Wildlife model management
│   └── directory_scanner.py # Directory traversal and image discovery
├── postprocessing/
│   ├── __init__.py
│   └── location_enricher.py # Camera location metadata enrichment
├── utils/
│   ├── __init__.py
│   ├── image_utils.py      # Image loading and validation
│   └── json_output.py      # JSON formatting and output
└── config/
    ├── __init__.py
    └── models_config.py    # Regional model configurations
```

## Components and Interfaces

### CLI Layer (cli/main.py)

**Purpose**: Provides command-line interface using Typer for user interaction and parameter validation.

**Key Functions**:
- `process_directory(directory: Path, model_region: str, output: Path)`: Main CLI command
- `list_models()`: Display available regional models
- Parameter validation and help documentation

**Interface**:
```python
@app.command()
def process_directory(
    directory: Path = typer.Argument(..., help="Directory containing wildlife camera images"),
    model_region: str = typer.Option("general", help="Regional model (amazon, europe, hamelin, general)"),
    output: Path = typer.Option("results.json", help="Output JSON file path"),
    progress: bool = typer.Option(True, help="Show progress indicators")
) -> None
```

### Processing Engine (core/processor.py)

**Purpose**: Orchestrates the entire image processing workflow from directory scanning to result compilation.

**Key Functions**:
- `process_image_directory(directory_path: Path, model_config: ModelConfig) -> ProcessingResults`
- `process_single_image(image_path: Path, models: ModelManager) -> DetectionResult`
- `compile_results(detection_results: List[DetectionResult]) -> Dict`

**Interface**:
```python
class WildlifeProcessor:
    def __init__(self, model_region: str):
        self.model_manager = ModelManager(model_region)
        self.directory_scanner = DirectoryScanner()
        self.location_enricher = LocationEnricher()
    
    def process_directory(self, directory_path: Path) -> ProcessingResults:
        # Main processing workflow
```

### Model Management (core/models.py)

**Purpose**: Manages PyTorch Wildlife model initialization, loading, and inference operations with European species classification support.

**Key Functions**:
- `load_detection_model() -> MegaDetectorV6`: Initialize detection model
- `load_classification_model(region: str) -> ClassificationModel`: Load regional classification model with European species support
- `run_detection(image: np.ndarray) -> DetectionResult`: Execute detection inference
- `run_classification(image: np.ndarray) -> ClassificationResult`: Execute classification inference with species mapping
- `enhance_generic_classification(detection: Dict, region: str) -> EnhancedClassification`: Improve generic "animal" classifications with regional context

**Interface**:
```python
class ModelManager:
    def __init__(self, region: str):
        self.detection_model = pw_detection.MegaDetectorV6()
        self.classification_model = self._load_regional_model(region)
        self.species_mapper = SpeciesMapper(region)
        self.fallback_classifier = FallbackClassifier()
    
    def process_image(self, image: np.ndarray) -> CombinedResult:
        detection_result = self.detection_model.single_image_detection(image)
        
        # Try regional classification first
        classification_result = self.classification_model.single_image_classification(image)
        
        # If generic "animal" result, attempt enhancement
        if self._is_generic_result(classification_result):
            enhanced_result = self._enhance_classification(
                detection_result, classification_result, image
            )
            return self._combine_results(detection_result, enhanced_result)
        
        return self._combine_results(detection_result, classification_result)
    
    def _enhance_classification(self, detection: Dict, classification: Dict, image: np.ndarray) -> Dict:
        """Enhance generic animal classifications with European species context"""
        # Use bounding box features, size analysis, and regional probability
        enhanced_species = self.species_mapper.map_to_european_species(
            detection, classification, image
        )
        return enhanced_species

class SpeciesMapper:
    """Maps generic classifications to specific European species"""
    def __init__(self, region: str):
        self.region = region
        self.species_mapping = EUROPEAN_SPECIES_MAPPING
    
    def map_to_european_species(self, detection: Dict, classification: Dict, image: np.ndarray) -> Dict:
        # Analyze detection features for European species identification
        size_category = self._analyze_animal_size(detection['bbox'])
        habitat_context = self._infer_habitat_from_image(image)
        time_context = self._get_temporal_context(detection.get('timestamp'))
        
        # Map to most likely European species
        probable_species = self._determine_species(size_category, habitat_context, time_context)
        
        return {
            'species': probable_species,
            'confidence': classification['confidence'] * 0.8,  # Reduce confidence for enhanced classification
            'classification_method': 'enhanced_european_mapping',
            'original_classification': classification['species']
        }
```

### Directory Scanner (core/directory_scanner.py)

**Purpose**: Handles directory traversal, image discovery, and metadata extraction from directory structure.

**Key Functions**:
- `scan_directory(path: Path) -> List[ImageMetadata]`: Discover all images with metadata
- `extract_location_from_path(path: Path) -> str`: Parse location from directory structure
- `extract_datetime_from_path(path: Path) -> datetime`: Parse timestamp from directory structure
- `validate_image_format(path: Path) -> bool`: Check supported image formats

**Interface**:
```python
@dataclass
class ImageMetadata:
    file_path: Path
    location: str
    timestamp: datetime
    camera_reference: str

class DirectoryScanner:
    def scan_directory(self, root_path: Path) -> List[ImageMetadata]:
        # Recursive directory scanning with metadata extraction
```

### Location Enricher (postprocessing/location_enricher.py)

**Purpose**: Enriches detection results with additional camera location metadata and geographic information.

**Key Functions**:
- `enrich_results(results: List[DetectionResult]) -> List[EnrichedResult]`: Add location metadata
- `lookup_camera_coordinates(camera_reference: str) -> Optional[Coordinates]`: GPS coordinate lookup
- `add_geographic_context(location: str) -> GeographicContext`: Add regional context

**Interface**:
```python
class LocationEnricher:
    def enrich_detection_result(self, result: DetectionResult) -> EnrichedResult:
        # Add camera location metadata, GPS coordinates, geographic context
```

## Data Models

### Core Data Structures

```python
@dataclass
class DetectionResult:
    image_path: Path
    camera_reference: str
    timestamp: datetime
    detections: List[AnimalDetection]
    processing_time: float
    model_version: str

@dataclass
class AnimalDetection:
    species: str
    confidence: float
    bounding_box: BoundingBox
    classification_model: str
    is_uncertain: bool  # confidence < 0.5

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

@dataclass
class ProcessingResults:
    total_images: int
    successful_detections: int
    failed_images: List[str]
    processing_duration: float
    results_by_camera: Dict[str, List[DetectionResult]]
    model_info: ModelInfo

@dataclass
class ModelInfo:
    detection_model: str
    classification_model: str
    region: str
    model_versions: Dict[str, str]
```

### Regional Model Configuration

```python
@dataclass
class ModelConfig:
    region: str
    classification_model_class: str
    model_name: str
    geographic_coverage: str
    species_categories: List[str]
    fallback_strategy: str

REGIONAL_MODELS = {
    "amazon": ModelConfig(
        region="amazon",
        classification_model_class="AI4GAmazonRainforest",
        model_name="AI4G Amazon Rainforest",
        geographic_coverage="Amazon Basin, South America",
        species_categories=["jaguar", "tapir", "capybara", "ocelot", "peccary"],
        fallback_strategy="generic_animal"
    ),
    "europe": ModelConfig(
        region="europe",
        classification_model_class="EuropeanWildlifeClassifier",
        model_name="European Wildlife Species Classifier",
        geographic_coverage="European continent",
        species_categories=["roe_deer", "red_deer", "wild_boar", "red_fox", "european_badger", "pine_marten", "european_hare", "european_rabbit"],
        fallback_strategy="enhanced_generic_with_context"
    ),
    "general": ModelConfig(
        region="general",
        classification_model_class="GeneralWildlifeClassifier",
        model_name="General Wildlife Classifier",
        geographic_coverage="Global",
        species_categories=["mammal_large", "mammal_medium", "mammal_small", "bird", "reptile"],
        fallback_strategy="basic_generic"
    )
}

# European Species Mapping for Enhanced Classification
EUROPEAN_SPECIES_MAPPING = {
    "deer": ["roe_deer", "red_deer", "fallow_deer"],
    "wild_boar": ["wild_boar", "domestic_pig_feral"],
    "fox": ["red_fox", "arctic_fox"],
    "badger": ["european_badger"],
    "marten": ["pine_marten", "beech_marten"],
    "hare": ["european_hare", "mountain_hare"],
    "rabbit": ["european_rabbit"],
    "squirrel": ["red_squirrel", "grey_squirrel"],
    "bird_large": ["golden_eagle", "white_tailed_eagle", "buzzard"],
    "bird_medium": ["pheasant", "partridge", "woodpecker"],
    "bird_small": ["robin", "blackbird", "finch"]
}
```

## Error Handling

### Error Categories and Responses

1. **Image Processing Errors**:
   - Corrupted image files: Log error, continue processing
   - Unsupported formats: Skip with warning
   - Memory errors: Implement image resizing fallback

2. **Model Loading Errors**:
   - Missing model weights: Automatic download with progress indication
   - Model initialization failures: Clear error messages with troubleshooting steps
   - CUDA/GPU errors: Fallback to CPU processing

3. **Directory Structure Errors**:
   - Invalid directory paths: Validation with helpful error messages
   - Permission errors: Clear access requirement messages
   - Empty directories: Warning with suggestion to check path

4. **Output Errors**:
   - File write permissions: Alternative output location suggestions
   - Disk space issues: Size estimation and cleanup recommendations

### Error Recovery Strategies

```python
class ErrorHandler:
    def handle_image_error(self, image_path: Path, error: Exception) -> None:
        # Log error, add to failed_images list, continue processing
    
    def handle_model_error(self, error: Exception) -> None:
        # Attempt model reinitialization, provide installation guidance
    
    def handle_timeout(self, image_path: Path) -> None:
        # Skip image, log timeout, adjust processing parameters
```

## Testing Strategy

### Unit Testing Approach

1. **Model Management Tests**:
   - Mock PyTorch Wildlife models for isolated testing
   - Test model loading and initialization
   - Validate inference result formatting

2. **Directory Scanner Tests**:
   - Test directory structure parsing with various formats
   - Validate metadata extraction accuracy
   - Test error handling for malformed paths

3. **Processing Engine Tests**:
   - Test end-to-end processing workflow with sample data
   - Validate result compilation and JSON output
   - Test error recovery and timeout handling

4. **CLI Interface Tests**:
   - Test parameter validation and help documentation
   - Validate command execution with various input combinations
   - Test progress indication and user feedback

### Integration Testing

1. **PyTorch Wildlife Integration**:
   - Test with actual model downloads and inference
   - Validate detection and classification accuracy
   - Test regional model switching

2. **File System Integration**:
   - Test with real wildlife camera directory structures
   - Validate large batch processing performance
   - Test output file generation and formatting

### Performance Testing

1. **Batch Processing Performance**:
   - Measure processing time per image across different image sizes
   - Test memory usage with large image batches
   - Validate timeout handling effectiveness

2. **Model Loading Performance**:
   - Measure model initialization time
   - Test model switching overhead
   - Validate automatic download performance

## Implementation Notes

### PyTorch Wildlife Integration with European Species Support

The design leverages PyTorch Wildlife's established patterns while addressing European species classification:

```python
# Detection workflow (unchanged)
detection_model = pw_detection.MegaDetectorV6()
detection_result = detection_model.single_image_detection(img_array)

# Enhanced classification workflow for European species
if region == "europe":
    # Try European-specific model if available
    try:
        classification_model = pw_classification.EuropeanWildlifeClassifier()
        classification_result = classification_model.single_image_classification(img_array)
    except ModelNotAvailableError:
        # Fallback to general model with enhancement
        classification_model = pw_classification.GeneralWildlifeClassifier()
        base_result = classification_model.single_image_classification(img_array)
        classification_result = enhance_for_european_species(base_result, detection_result, img_array)
else:
    # Use region-specific model (Amazon, etc.)
    classification_model = pw_classification.AI4GAmazonRainforest()
    classification_result = classification_model.single_image_classification(img_array)

# European Species Enhancement Strategy
def enhance_for_european_species(base_classification, detection, image):
    """
    Enhance generic 'animal' classifications for European context
    Uses detection bounding box analysis, size estimation, and habitat inference
    """
    if base_classification['species'] == 'animal':
        # Analyze detection features
        bbox_area = detection['bbox']['width'] * detection['bbox']['height']
        relative_size = bbox_area / (image.shape[0] * image.shape[1])
        
        # Size-based European species mapping
        if relative_size > 0.15:  # Large animals
            likely_species = ['wild_boar', 'red_deer', 'roe_deer']
        elif relative_size > 0.05:  # Medium animals  
            likely_species = ['red_fox', 'european_badger', 'pine_marten']
        else:  # Small animals
            likely_species = ['european_hare', 'european_rabbit', 'red_squirrel']
        
        # Return enhanced classification with reduced confidence
        return {
            'species': likely_species[0],  # Most probable for size category
            'confidence': base_classification['confidence'] * 0.7,
            'alternative_species': likely_species[1:],
            'classification_method': 'european_enhancement'
        }
    
    return base_classification
```

### European Species Classification Strategy

Given the current limitation where AI4GAmazonRainforest only returns "animal", the system implements a multi-layered approach:

1. **Primary Strategy**: Use European-specific PyTorch Wildlife models when available
2. **Fallback Strategy**: Enhance generic classifications using:
   - Bounding box size analysis for animal size categorization
   - Temporal context (time of day/season) for behavior-based species probability
   - Basic habitat inference from image background features
   - European species probability mapping based on geographic context

3. **Classification Enhancement Pipeline**:
   ```python
   def classify_european_wildlife(detection_result, image, timestamp):
       # Step 1: Try European-specific model
       if european_model_available():
           return european_model.classify(image)
       
       # Step 2: Enhance generic classification
       generic_result = general_model.classify(image)
       if generic_result['species'] == 'animal':
           return enhance_with_european_context(
               generic_result, detection_result, image, timestamp
           )
       
       return generic_result
   ```

### Performance Considerations

1. **Memory Management**: Implement image batching and memory cleanup for large datasets
2. **Model Caching**: Cache loaded models to avoid reinitialization overhead
3. **Parallel Processing**: Consider multiprocessing for CPU-bound image preprocessing
4. **Progress Tracking**: Implement detailed progress indicators for long-running operations

### European Species Classification Architecture

#### Problem Statement
Current PyTorch Wildlife models like AI4GAmazonRainforest return generic "animal" classifications for European wildlife, limiting research value for species-specific analysis.

#### Solution Architecture

1. **Model Hierarchy**:
   ```
   European Classification Pipeline
   ├── Primary: European-specific PyTorch Wildlife model (if available)
   ├── Secondary: Enhanced generic classification with European context
   └── Fallback: Generic animal detection with size/habitat hints
   ```

2. **Enhancement Components**:
   - **Size Analyzer**: Categorizes animals by relative bounding box size
   - **Habitat Inferencer**: Basic background analysis for forest/meadow/water context  
   - **Temporal Mapper**: Time-based species probability (nocturnal vs diurnal)
   - **European Species Database**: Regional species probability and characteristics

3. **Classification Confidence Adjustment**:
   - Native European model results: Original confidence
   - Enhanced generic results: Confidence × 0.7-0.8 (reduced for uncertainty)
   - Size-based estimates: Confidence × 0.5-0.6 (lowest confidence)

#### Implementation Strategy

```python
class EuropeanSpeciesClassifier:
    def __init__(self):
        self.size_thresholds = {
            'large': 0.15,    # wild_boar, deer
            'medium': 0.05,   # fox, badger, marten  
            'small': 0.01     # hare, rabbit, squirrel
        }
        
        self.species_probabilities = {
            'large': ['wild_boar', 'red_deer', 'roe_deer'],
            'medium': ['red_fox', 'european_badger', 'pine_marten'],
            'small': ['european_hare', 'european_rabbit', 'red_squirrel']
        }
    
    def enhance_classification(self, generic_result, detection, image_context):
        if generic_result['species'] != 'animal':
            return generic_result
            
        size_category = self._categorize_by_size(detection['bbox'], image_context)
        probable_species = self.species_probabilities[size_category]
        
        return {
            'species': probable_species[0],
            'confidence': generic_result['confidence'] * 0.75,
            'alternatives': probable_species[1:],
            'enhancement_method': 'european_size_mapping'
        }
```

### Extensibility Features

1. **Plugin Architecture**: Design model management to easily add new regional models
2. **Configuration System**: External configuration files for model parameters and thresholds
3. **Output Formats**: Modular output system supporting multiple formats (JSON, CSV, XML)
4. **Custom Postprocessing**: Plugin system for additional metadata enrichment
5. **Species Enhancement Pipeline**: Modular system for improving generic classifications with regional context