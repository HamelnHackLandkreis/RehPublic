# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create directory structure for CLI, core, postprocessing, utils, and config modules
  - Define base data models and interfaces for DetectionResult, AnimalDetection, and ProcessingResults
  - Set up project dependencies including PyTorch Wildlife, Typer, and image processing libraries
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Implement PyTorch Wildlife model management with European species support
  - [x] 2.1 Create ModelManager class with MegaDetectorV6 integration
    - Implement model initialization and automatic weight downloading
    - Create single_image_detection wrapper with error handling
    - _Requirements: 3.1, 5.3, 7.2_

  - [x] 2.2 Implement regional classification model support
    - Create regional model configuration system with AI4GAmazonRainforest and other models
    - Implement model selection logic based on region parameter
    - Add model validation and fallback mechanisms
    - _Requirements: 3.2, 5.1, 5.2_

  - [x] 2.3 Create combined detection and classification workflow
    - Implement image preprocessing for PyTorch Wildlife models
    - Combine detection and classification results into unified output
    - Add confidence score processing and uncertainty marking
    - _Requirements: 3.3, 3.4, 3.5_

  - [x] 2.4 Implement European species classification enhancement
    - Create SpeciesMapper class for converting generic "animal" classifications to European species
    - Implement size-based animal categorization using bounding box analysis
    - Add European species probability mapping for large, medium, and small animals
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 2.5 Create classification enhancement pipeline
    - Implement multi-layered classification strategy (European model → enhanced generic → fallback)
    - Add confidence adjustment for enhanced classifications
    - Create alternative species suggestions for uncertain classifications
    - _Requirements: 6.3, 6.4, 6.5_

- [ ] 3. Implement directory scanning and metadata extraction
  - [x] 3.1 Create DirectoryScanner class for image discovery
    - Implement recursive directory traversal with image format validation
    - Support JPEG, JPG, PNG, and TIFF file formats
    - Add file accessibility and corruption checks
    - _Requirements: 1.2, 1.3, 6.1_

  - [x] 3.2 Implement location and timestamp extraction
    - Parse camera reference from locationName directory structure
    - Extract datetime information from directory paths with fallback to file modification time
    - Validate timestamp ranges for wildlife monitoring
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_



- [ ] 4. Create main processing engine
  - [x] 4.1 Implement WildlifeProcessor orchestration class
    - Create main processing workflow that coordinates all components
    - Implement batch processing with progress tracking and timeout handling
    - Add error recovery for individual image processing failures
    - _Requirements: 1.5, 6.1, 6.4, 6.5_

  - [x] 4.2 Implement single image processing pipeline
    - Create image loading and preprocessing utilities
    - Integrate model inference with error handling and timeout protection
    - Format detection results with all required metadata fields
    - _Requirements: 1.4, 1.5, 4.2, 4.5_



- [ ] 5. Implement location enrichment postprocessing
  - [x] 5.1 Create LocationEnricher class for metadata enhancement
    - Implement camera location metadata enrichment system
    - Add GPS coordinate lookup functionality for camera references
    - Create geographic context addition for regional information
    - _Requirements: 4.3, 4.4_

  - [x] 5.2 Integrate postprocessing with main workflow
    - Connect LocationEnricher to main processing pipeline
    - Ensure enriched metadata is included in final JSON output
    - Add postprocessing error handling and fallback mechanisms
    - _Requirements: 4.3, 4.5_

- [ ] 6. Create CLI interface with Typer and European species support
  - [x] 6.1 Implement main CLI command structure
    - Create Typer application with process_directory command
    - Add parameter validation for directory paths and model regions
    - Implement help documentation and usage examples
    - _Requirements: 1.1, 5.4_

  - [x] 6.2 Add regional model selection and validation
    - Implement model region parameter with supported options (amazon, europe, general)
    - Create list_models command to display available regional models
    - Add model availability validation before processing starts
    - _Requirements: 5.1, 5.2, 5.5, 7.2_

  - [x] 6.3 Implement progress indicators and user feedback
    - Add progress bars for batch processing operations
    - Create informative error messages with troubleshooting guidance
    - Implement verbose logging options for debugging
    - _Requirements: 7.4, 7.3_

  - [ ] 6.4 Add European species classification options
    - Implement CLI flags for enabling/disabling species enhancement
    - Add options for confidence thresholds and alternative species reporting
    - Create help documentation for European species classification features
    - _Requirements: 6.1, 6.2, 6.4_

- [ ] 7. Create JSON output formatting and file handling
  - [x] 7.1 Implement structured JSON output generation
    - Create JSON formatter that groups results by camera reference
    - Include all required fields: image paths, timestamps, animal types, confidence scores
    - Add processing metadata including total images, duration, and model information
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [x] 7.2 Add output file handling and validation
    - Implement output file writing with permission and disk space checks
    - Create backup and recovery mechanisms for output failures
    - Add JSON validation to ensure well-formed output
    - _Requirements: 4.1, 4.5_

- [ ] 8. Implement comprehensive error handling and logging
  - [x] 8.1 Create centralized error handling system
    - Implement ErrorHandler class for consistent error processing
    - Add specific handlers for image, model, directory, and output errors
    - Create user-friendly error messages with actionable guidance
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 8.2 Add logging and debugging capabilities
    - Implement structured logging for processing operations and errors
    - Add debug mode with detailed processing information
    - Create log file output options for troubleshooting
    - _Requirements: 6.1, 6.4_

- [ ] 9. Integration and end-to-end testing with European species validation
  - [x] 9.1 Create sample wildlife camera directory structure
    - Set up test data with realistic directory organization
    - Include various image formats and edge cases for testing
    - Create test cases for different regional model scenarios
    - _Requirements: 1.2, 1.3, 5.1, 5.2_

  - [x] 9.2 Implement end-to-end workflow validation
    - Test complete CLI workflow from directory input to JSON output
    - Validate PyTorch Wildlife model integration and automatic downloading
    - Test error handling and recovery across all components
    - _Requirements: 1.1, 1.4, 1.5, 4.1, 7.2_

  - [x] 9.3 Validate European species classification enhancement
    - Test species enhancement pipeline with real European wildlife images
    - Validate that generic "animal" classifications are converted to specific species
    - Test confidence score adjustments and alternative species suggestions
    - Compare results between Amazon model and European enhancement
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 9.4 Test European species accuracy and validation
    - Validate species identification accuracy for common European wildlife
    - Test size-based categorization with different animal types
    - Verify confidence score reliability for enhanced classifications
    - Create test cases for edge cases and uncertain detections
    - _Requirements: 6.1, 6.4, 6.5_

