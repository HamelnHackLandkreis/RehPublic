"""Regional model configurations for PyTorch Wildlife."""

from typing import Dict, List
from wildlife_processor.core.data_models import ModelConfig

# Regional model configurations
REGIONAL_MODELS = {
    "amazon": ModelConfig(
        region="amazon",
        classification_model_class="AI4GAmazonRainforest",
        model_name="AI4G Amazon Rainforest",
        geographic_coverage="Amazon Basin, South America"
    ),
    "europe": ModelConfig(
        region="europe",
        classification_model_class="AI4GAmazonRainforest",  # Fallback to Amazon for now
        model_name="European Wildlife Classifier",
        geographic_coverage="European continent"
    ),
    "hamelin": ModelConfig(
        region="hamelin",
        classification_model_class="AI4GAmazonRainforest",  # Fallback to Amazon for now
        model_name="Hamelin Regional Wildlife",
        geographic_coverage="Hamelin region, Germany"
    ),
    "general": ModelConfig(
        region="general",
        classification_model_class="AI4GAmazonRainforest",  # Default to Amazon
        model_name="General Wildlife Classifier",
        geographic_coverage="Global"
    )
}


def get_model_config(region: str) -> ModelConfig:
    """Get model configuration for a specific region."""
    if region not in REGIONAL_MODELS:
        raise ValueError(f"Unknown region: {region}. Available regions: {list(REGIONAL_MODELS.keys())}")
    return REGIONAL_MODELS[region]


def list_available_regions() -> List[str]:
    """List all available regional model options."""
    return list(REGIONAL_MODELS.keys())


def get_model_description(region: str) -> str:
    """Get detailed description of a regional model.
    
    Args:
        region: Region name
        
    Returns:
        Formatted description string
    """
    if region not in REGIONAL_MODELS:
        return f"Unknown region: {region}"
    
    config = REGIONAL_MODELS[region]
    return f"{config.model_name} - {config.geographic_coverage}"


def validate_region(region: str) -> bool:
    """Validate if a region is supported.
    
    Args:
        region: Region name to validate
        
    Returns:
        True if region is supported, False otherwise
    """
    return region in REGIONAL_MODELS


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

# Size-based European species probabilities
EUROPEAN_SIZE_CATEGORIES = {
    'large': {
        'threshold': 0.15,  # Relative bounding box area > 15% of image
        'species': ['wild_boar', 'red_deer', 'roe_deer'],
        'probabilities': [0.4, 0.35, 0.25]  # Probability weights for each species
    },
    'medium': {
        'threshold': 0.05,  # Relative bounding box area 5-15% of image
        'species': ['red_fox', 'european_badger', 'pine_marten'],
        'probabilities': [0.5, 0.3, 0.2]
    },
    'small': {
        'threshold': 0.01,  # Relative bounding box area 1-5% of image
        'species': ['european_hare', 'european_rabbit', 'red_squirrel'],
        'probabilities': [0.4, 0.4, 0.2]
    }
}


def get_european_species_mapping() -> Dict[str, List[str]]:
    """Get European species mapping dictionary."""
    return EUROPEAN_SPECIES_MAPPING.copy()


def get_european_size_categories() -> Dict[str, Dict]:
    """Get European size-based species categories."""
    return EUROPEAN_SIZE_CATEGORIES.copy()


def get_default_region() -> str:
    """Get the default region for model selection.
    
    Returns:
        Default region name
    """
    return "general"