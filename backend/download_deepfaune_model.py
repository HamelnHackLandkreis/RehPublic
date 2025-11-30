#!/usr/bin/env python3
"""Download DeepFaune v4 model from Hugging Face Hub.

This script downloads the large DeepFaune v4 model file (~1.2GB) from Hugging Face
instead of storing it in the Git repository.
"""

import logging
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_model() -> bool:
    """Download DeepFaune v4 model from Hugging Face Hub.

    Returns:
        True if successful, False otherwise
    """
    model_dir = Path(__file__).parent / "models"
    model_path = model_dir / "deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"

    # Check if model already exists
    if model_path.exists():
        file_size = model_path.stat().st_size
        # Check if it's the actual model (>1GB) and not a Git LFS pointer (<1KB)
        if file_size > 1_000_000:  # >1MB means it's the real file
            logger.info(f"Model already exists at {model_path} ({file_size:,} bytes)")
            return True
        else:
            logger.warning(
                f"Found Git LFS pointer file ({file_size} bytes), will download actual model"
            )
            model_path.unlink()  # Remove the pointer file

    # Create models directory if it doesn't exist
    model_dir.mkdir(exist_ok=True)

    logger.info("Downloading DeepFaune v4 model from Hugging Face Hub...")
    logger.info("This may take a few minutes (~1.2GB file)...")

    try:
        # Download from Hugging Face Hub
        logger.info(
            "Downloading from Deepfaune_v1.4/deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"
        )

        downloaded_path = hf_hub_download(
            repo_id="Addax-Data-Science/Deepfaune_v1.4",
            filename="deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt",
            local_dir=model_dir,
            local_dir_use_symlinks=False,
        )

        # Verify download
        final_path = Path(downloaded_path)
        file_size = final_path.stat().st_size
        if file_size > 1_000_000:
            # Move to expected location if needed
            if final_path != model_path:
                final_path.rename(model_path)
            logger.info(
                f"Model downloaded successfully to {model_path} ({file_size:,} bytes)"
            )
            return True
        else:
            logger.error(
                f"Downloaded file is too small ({file_size} bytes), may be incomplete"
            )
            if final_path.exists():
                final_path.unlink()
            return False

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        logger.error(
            "Please download the model manually from https://huggingface.co/Deepfaune_v1.4/deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"
        )
        logger.error(f"Place it at: {model_path}")
        return False


if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
