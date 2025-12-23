#!/usr/bin/env python3
"""Debug script to check what the AI4GAmazonRainforest model is actually detecting."""

import logging
import sys
from pathlib import Path

# Add the backend/src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

try:
    from wildlife_processor.utils.image_utils import (
        load_image,
        preprocess_image_for_pytorch_wildlife,
    )
except ImportError:
    # Fallback imports
    import numpy as np
    from PIL import Image
    from typing import Any

    def load_image(file_path: Path) -> Any | None:
        return np.array(Image.open(file_path))

    def preprocess_image_for_pytorch_wildlife(image: Any, max_size: int = 1280) -> Any:
        return image


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def debug_single_image(image_path: str):
    """Debug a single image to see raw model outputs."""
    print(f"\n=== Debugging image: {image_path} ===")

    try:
        # Import PyTorch Wildlife
        from PytorchWildlife.models import detection as pw_detection
        from PytorchWildlife.models import classification as pw_classification

        # Load models
        print("Loading MegaDetectorV6...")
        detection_model = pw_detection.MegaDetectorV6(
            weights=None, device="cpu", pretrained=True, version="MDV6-yolov9-c"
        )

        print("Loading AI4GAmazonRainforest...")
        classification_model = pw_classification.AI4GAmazonRainforest()

        # Load and preprocess image
        print(f"Loading image: {image_path}")
        image = load_image(Path(image_path))
        if image is None:
            print("Failed to load image!")
            return

        processed_image = preprocess_image_for_pytorch_wildlife(image)
        print(f"Image shape: {processed_image.shape}")

        # Run detection
        print("\n--- Detection Results ---")
        detection_result = detection_model.single_image_detection(processed_image)
        print(f"Detection result keys: {list(detection_result.keys())}")

        if "detections" in detection_result:
            detections_obj = detection_result["detections"]
            print(f"Detections object type: {type(detections_obj)}")

            if hasattr(detections_obj, "xyxy"):
                print(f"Number of detections: {len(detections_obj.xyxy)}")
                print(f"Bounding boxes: {detections_obj.xyxy}")
                print(f"Confidences: {detections_obj.confidence}")
                print(f"Class IDs: {detections_obj.class_id}")

        # Run classification
        print("\n--- Classification Results ---")
        classification_result = classification_model.single_image_classification(
            processed_image
        )
        print(f"Classification result keys: {list(classification_result.keys())}")
        print(f"Prediction: {classification_result.get('prediction', 'N/A')}")
        print(f"Confidence: {classification_result.get('confidence', 'N/A')}")
        print(f"Class ID: {classification_result.get('class_id', 'N/A')}")

        # Show top 10 predictions and look for specific species
        if "all_confidences" in classification_result:
            all_confs = classification_result["all_confidences"]
            print("\nTop 10 predictions:")
            sorted_preds = sorted(all_confs, key=lambda x: x[1], reverse=True)[:10]
            for species, conf in sorted_preds:
                print(f"  {species}: {conf:.4f}")

            # Look for raccoon-related species
            print("\nLooking for raccoon-related species:")
            for species, conf in all_confs:
                if "procyon" in species.lower() or "raccoon" in species.lower():
                    print(f"  FOUND: {species}: {conf:.4f}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Test the raccoon image specifically
    raccoon_image = "backend/bilder/Aufnahme_250605_2029_BYWP9.jpg"
    debug_single_image(raccoon_image)
