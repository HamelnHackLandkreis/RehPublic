#!/usr/bin/env python3
"""Download DeepFaune v4 model from PBIL server.

This script downloads the large DeepFaune v4 model file (~1.2GB) from PBIL
instead of storing it in the Git repository.
"""

import logging
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_model() -> bool:
    """Download DeepFaune v4 model from PBIL server.

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

    logger.info("Downloading DeepFaune v4 model from PBIL server...")
    logger.info("This may take a few minutes (~1.2GB file)...")

    try:
        # Direct download from PBIL server
        url = "https://pbil.univ-lyon1.fr/software/download/deepfaune/v1.4/deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"
        logger.info(f"Downloading from {url}")
        
        # Download with progress indication
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, block_num * block_size * 100 / total_size)
                downloaded_mb = block_num * block_size / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                logger.info(f"Progress: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
        
        urllib.request.urlretrieve(url, model_path, reporthook=progress_hook)
        
        # Verify download
        file_size = model_path.stat().st_size
        if file_size > 1_000_000:
            logger.info(f"Model downloaded successfully to {model_path} ({file_size:,} bytes)")
            return True
        else:
            logger.error(f"Downloaded file is too small ({file_size} bytes), may be incomplete")
            model_path.unlink()
            return False

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        logger.error(
            "Please download the model manually from https://pbil.univ-lyon1.fr/software/download/deepfaune/v1.4/"
        )
        logger.error(f"Place it at: {model_path}")
        return False


if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
