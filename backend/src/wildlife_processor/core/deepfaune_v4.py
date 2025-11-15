"""Custom DeepFaune v4 classifier wrapper.

This module provides a custom DeepFaune v4 classifier that supports 38 classes
instead of the default 34 classes in the standard DeepfauneClassifier.
"""

import logging
from typing import Any, Optional

from torchvision.transforms.functional import InterpolationMode

logger = logging.getLogger(__name__)

try:
    from PytorchWildlife.models.classification.timm_base.base_classifier import (
        TIMM_BaseClassifierInference,
    )
    from PytorchWildlife.data import transforms as pw_trans

    PYTORCH_WILDLIFE_AVAILABLE = True
except ImportError:
    TIMM_BaseClassifierInference = None
    pw_trans = None
    PYTORCH_WILDLIFE_AVAILABLE = False


# Only define the class if PytorchWildlife is available
if PYTORCH_WILDLIFE_AVAILABLE:

    class DeepfauneV4Classifier(TIMM_BaseClassifierInference):
        """DeepFaune v4 classifier with 38 classes support.

        This is a custom classifier for DeepFaune v4 model which has 38 classes
        instead of the 34 classes in the standard v3 model.
        """

        BACKBONE = "vit_large_patch14_dinov2.lvd142m"
        MODEL_NAME = "deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt"
        IMAGE_SIZE = 182
        # v4 has 38 classes - same 34 classes as v3 plus 4 additional classes
        # The additional classes are: human, vehicle, empty, unknown
        CLASS_NAMES = {
            "en": [
                "bison",
                "badger",
                "ibex",
                "beaver",
                "red deer",
                "golden jackal",
                "chamois",
                "cat",
                "goat",
                "roe deer",
                "dog",
                "raccoon dog",
                "fallow deer",
                "squirrel",
                "moose",
                "equid",
                "genet",
                "wolverine",
                "hedgehog",
                "lagomorph",
                "wolf",
                "otter",
                "lynx",
                "marmot",
                "micromammal",
                "mouflon",
                "sheep",
                "mustelid",
                "bird",
                "bear",
                "porcupine",
                "nutria",
                "muskrat",
                "raccoon",
                "fox",
                "reindeer",
                "wild boar",
                "cow",
            ],
        }

        def __init__(
            self,
            weights: Optional[str] = None,
            device: str = "cpu",
            transform: Optional[Any] = None,
            class_name_lang: str = "en",
        ) -> None:
            """Initialize DeepFaune v4 classifier.

            Args:
                weights: Path to model weights file (required for v4)
                device: Device for inference
                transform: Optional transform
                class_name_lang: Language for class names
            """
            if not PYTORCH_WILDLIFE_AVAILABLE:
                raise RuntimeError(
                    "PyTorch Wildlife is not installed. Install with: uv add PytorchWildlife"
                )

            # Convert class names to dict format BEFORE calling super().__init__()
            # The base class uses len(self.CLASS_NAMES) to determine num_classes
            class_names_list = self.CLASS_NAMES[class_name_lang]
            self.CLASS_NAMES = {str(i): [c] for i, c in enumerate(class_names_list)}  # type: ignore[assignment]

            # Verify we have 38 classes
            if len(self.CLASS_NAMES) != 38:
                raise ValueError(
                    f"Expected 38 classes for DeepFaune v4, got {len(self.CLASS_NAMES)}"
                )

            if transform is None:
                transform = pw_trans.Classification_Inference_Transform(
                    target_size=self.IMAGE_SIZE,
                    interpolation=InterpolationMode.BICUBIC,
                    max_size=None,
                    antialias=None,
                )

            # Don't pass URL - only use weights to prevent download
            super().__init__(
                weights=weights,
                device=device,
                url=None,  # No URL to prevent download
                transform=transform,
                weights_key="state_dict",
                weights_prefix="base_model.",
            )
else:
    # Dummy class when PytorchWildlife is not available
    class DeepfauneV4Classifier:  # type: ignore[no-redef]
        """Dummy DeepFaune v4 classifier when PytorchWildlife is not available."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "PyTorch Wildlife is not installed. Install with: uv add PytorchWildlife"
            )
