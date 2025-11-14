#!/usr/bin/env python3
"""Test script for European species classification enhancement."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Test with a small subset of images
    test_dir = Path("test_bilder")
    output_file = Path("test_european_results.json")

    print("Testing European species classification enhancement...")
    print(f"Input directory: {test_dir}")
    print(f"Output file: {output_file}")

    # Run the CLI with European region

    try:
        # Simulate CLI call with European enhancement
        from wildlife_processor.core.processor import WildlifeProcessor

        processor = WildlifeProcessor(model_region="europe")
        results = processor.process_directory(test_dir, show_progress=True)

        # Save results
        from wildlife_processor.utils.json_output import JSONOutputHandler

        json_handler = JSONOutputHandler()
        json_handler.save_results(results, output_file)

        print("\nProcessing completed!")
        print(f"Total images: {results.total_images}")
        print(f"Successful detections: {results.successful_detections}")
        print(f"Failed images: {len(results.failed_images)}")
        print(f"Processing duration: {results.processing_duration:.2f}s")

        # Show some example results
        print("\nExample detections:")
        for camera_ref, detections in list(results.results_by_camera.items())[:2]:
            print(f"\nCamera {camera_ref}:")
            for detection in detections[:2]:  # Show first 2 detections per camera
                for animal in detection.detections:
                    enhancement_info = ""
                    if animal.enhancement_metadata:
                        original = animal.enhancement_metadata.get(
                            "original_classification", "N/A"
                        )
                        enhancement_info = f" (enhanced from '{original}')"

                    alternatives = ""
                    if animal.alternative_species:
                        alternatives = (
                            f", alternatives: {', '.join(animal.alternative_species)}"
                        )

                    print(
                        f"  - {animal.species} (confidence: {animal.confidence:.3f}){enhancement_info}{alternatives}"
                    )

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback

        traceback.print_exc()
