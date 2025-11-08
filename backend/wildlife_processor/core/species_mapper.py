"""European species mapping and classification enhancement."""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from wildlife_processor.config.models_config import (
    get_european_size_categories,
    get_european_species_mapping,
)

logger = logging.getLogger(__name__)


class SpeciesMapper:
    """Maps generic classifications to specific European species."""
    
    def __init__(self, region: str):
        """Initialize species mapper for a specific region.
        
        Args:
            region: Geographic region for species mapping
        """
        self.region = region
        self.species_mapping = get_european_species_mapping()
        self.size_categories = get_european_size_categories()
        
    def map_to_european_species(
        self, 
        detection: Dict[str, Any], 
        classification: Dict[str, Any], 
        image: np.ndarray,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Map generic animal classification to specific European species.
        
        Args:
            detection: Detection result with bounding box information
            classification: Classification result from model
            image: Original image as numpy array
            timestamp: Optional timestamp for temporal context
            
        Returns:
            Enhanced classification with European species information
        """
        # Get species from different possible fields
        species = classification.get('prediction', 
                  classification.get('class_name', 
                  classification.get('species', 'unknown')))
        
        # Check if this species should be enhanced for European context
        if not self._should_enhance_species(species):
            logger.debug(f"Species '{species}' does not need European enhancement")
            return classification
        
        logger.debug(f"Enhancing '{species}' classification for European context")
        
        # Analyze detection features for European species identification
        size_category = self._analyze_animal_size(detection, image)
        habitat_context = self._infer_habitat_from_image(image)
        time_context = self._get_temporal_context(timestamp)
        
        # Map to most likely European species
        probable_species, confidence_multiplier = self._determine_species(
            size_category, habitat_context, time_context, species
        )
        
        # Calculate enhanced confidence (reduced for uncertainty)
        original_confidence = float(classification.get('confidence', 0.5))
        enhanced_confidence = original_confidence * confidence_multiplier
        
        # Get alternative species for this size category
        alternatives = self._get_alternative_species(size_category, probable_species)
        
        enhanced_result = {
            'species': probable_species,
            'confidence': enhanced_confidence,
            'classification_method': 'enhanced_european_mapping',
            'original_classification': species,
            'size_category': size_category,
            'alternative_species': alternatives,
            'enhancement_factors': {
                'size_analysis': size_category,
                'habitat_context': habitat_context,
                'temporal_context': time_context
            }
        }
        
        logger.debug(f"Enhanced classification: {probable_species} (confidence: {enhanced_confidence:.3f})")
        return enhanced_result
    
    def _analyze_animal_size(self, detection: Dict[str, Any], image: np.ndarray) -> str:
        """Analyze animal size based on bounding box relative to image.
        
        Args:
            detection: Detection result with bbox information
            image: Original image
            
        Returns:
            Size category: 'large', 'medium', or 'small'
        """
        try:
            # Extract bounding box - handle different formats
            if 'bbox' in detection:
                bbox = detection['bbox']
                if len(bbox) == 4:
                    # Format: [x1, y1, x2, y2] or [x, y, width, height]
                    if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                        # Assume [x1, y1, x2, y2] format
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                    else:
                        # Assume [x, y, width, height] format
                        width = bbox[2]
                        height = bbox[3]
                else:
                    logger.warning(f"Unexpected bbox format: {bbox}")
                    return 'medium'  # Default fallback
            else:
                logger.warning("No bbox found in detection")
                return 'medium'  # Default fallback
            
            # Calculate relative size
            image_area = image.shape[0] * image.shape[1]
            bbox_area = width * height
            relative_size = bbox_area / image_area
            
            logger.debug(f"Bbox area: {bbox_area}, Image area: {image_area}, Relative size: {relative_size:.4f}")
            
            # Categorize by size thresholds
            if relative_size >= self.size_categories['large']['threshold']:
                return 'large'
            elif relative_size >= self.size_categories['medium']['threshold']:
                return 'medium'
            else:
                return 'small'
                
        except Exception as e:
            logger.error(f"Error analyzing animal size: {e}")
            return 'medium'  # Safe fallback
    
    def _infer_habitat_from_image(self, image: np.ndarray) -> str:
        """Infer basic habitat context from image characteristics.
        
        Args:
            image: Original image as numpy array
            
        Returns:
            Habitat context: 'forest', 'meadow', 'mixed', or 'unknown'
        """
        try:
            # Simple color-based habitat inference
            # This is a basic implementation - could be enhanced with more sophisticated analysis
            
            # Convert to RGB if needed and calculate color statistics
            if len(image.shape) == 3:
                # Calculate average color values
                avg_colors = np.mean(image, axis=(0, 1))
                
                # Normalize to 0-1 range
                if avg_colors.max() > 1.0:
                    avg_colors = avg_colors / 255.0
                
                # Simple heuristics based on color composition
                green_dominance = avg_colors[1] - np.mean([avg_colors[0], avg_colors[2]])
                brightness = np.mean(avg_colors)
                
                if green_dominance > 0.1 and brightness < 0.4:
                    return 'forest'  # Dark and green
                elif green_dominance > 0.05 and brightness > 0.4:
                    return 'meadow'  # Bright and green
                else:
                    return 'mixed'   # Mixed habitat
            else:
                return 'unknown'
                
        except Exception as e:
            logger.debug(f"Could not infer habitat from image: {e}")
            return 'unknown'
    
    def _get_temporal_context(self, timestamp: Optional[str]) -> str:
        """Get temporal context for species behavior patterns.
        
        Args:
            timestamp: Optional timestamp string
            
        Returns:
            Temporal context: 'diurnal', 'nocturnal', 'crepuscular', or 'unknown'
        """
        if not timestamp:
            return 'unknown'
        
        try:
            # Extract hour from timestamp (assuming ISO format or similar)
            # This is a simplified implementation
            if 'T' in timestamp:
                time_part = timestamp.split('T')[1]
                hour = int(time_part.split(':')[0])
            elif '_' in timestamp:
                # Handle format like "250612_0001" (YYMMDD_HHMM)
                parts = timestamp.split('_')
                if len(parts) >= 2 and len(parts[1]) >= 2:
                    hour = int(parts[1][:2])
                else:
                    return 'unknown'
            else:
                return 'unknown'
            
            # Categorize by time of day
            if 6 <= hour <= 18:
                return 'diurnal'    # Daytime
            elif 22 <= hour or hour <= 4:
                return 'nocturnal'  # Night time
            else:
                return 'crepuscular'  # Dawn/dusk
                
        except Exception as e:
            logger.debug(f"Could not parse temporal context from {timestamp}: {e}")
            return 'unknown'
    
    def _determine_species(
        self, 
        size_category: str, 
        habitat_context: str, 
        time_context: str,
        original_species: str = 'animal'
    ) -> Tuple[str, float]:
        """Determine most likely European species based on analysis factors.
        
        Args:
            size_category: Animal size category
            habitat_context: Habitat inference
            time_context: Temporal context
            original_species: Original species classification from model
            
        Returns:
            Tuple of (species_name, confidence_multiplier)
        """
        # First, try Amazon-to-European species mapping if applicable
        amazon_mapped_species = self._map_amazon_to_european_species(original_species, size_category)
        if amazon_mapped_species:
            logger.debug(f"Mapped Amazon species '{original_species}' to European species '{amazon_mapped_species}'")
            return amazon_mapped_species, 0.8  # High confidence for direct mapping
        
        # Fallback to size-based mapping
        if size_category not in self.size_categories:
            logger.warning(f"Unknown size category: {size_category}")
            return 'unknown_animal', 0.3
        
        category_info = self.size_categories[size_category]
        species_list = category_info['species']
        base_probabilities = category_info['probabilities']
        
        # Adjust probabilities based on context
        adjusted_probabilities = base_probabilities.copy()
        
        # Habitat-based adjustments
        if habitat_context == 'forest':
            # Increase probability for forest-dwelling species
            if 'wild_boar' in species_list:
                idx = species_list.index('wild_boar')
                adjusted_probabilities[idx] *= 1.3
            if 'pine_marten' in species_list:
                idx = species_list.index('pine_marten')
                adjusted_probabilities[idx] *= 1.2
        elif habitat_context == 'meadow':
            # Increase probability for open-area species
            if 'roe_deer' in species_list:
                idx = species_list.index('roe_deer')
                adjusted_probabilities[idx] *= 1.2
            if 'european_hare' in species_list:
                idx = species_list.index('european_hare')
                adjusted_probabilities[idx] *= 1.3
        
        # Temporal-based adjustments
        if time_context == 'nocturnal':
            # Increase probability for nocturnal species
            if 'wild_boar' in species_list:
                idx = species_list.index('wild_boar')
                adjusted_probabilities[idx] *= 1.4
            if 'red_fox' in species_list:
                idx = species_list.index('red_fox')
                adjusted_probabilities[idx] *= 1.3
            if 'european_badger' in species_list:
                idx = species_list.index('european_badger')
                adjusted_probabilities[idx] *= 1.5
        elif time_context == 'diurnal':
            # Increase probability for diurnal species
            if 'red_deer' in species_list:
                idx = species_list.index('red_deer')
                adjusted_probabilities[idx] *= 1.2
            if 'roe_deer' in species_list:
                idx = species_list.index('roe_deer')
                adjusted_probabilities[idx] *= 1.2
        
        # Normalize probabilities
        total_prob = sum(adjusted_probabilities)
        if total_prob > 0:
            normalized_probs = [p / total_prob for p in adjusted_probabilities]
        else:
            normalized_probs = base_probabilities
        
        # Select species based on weighted probability
        selected_idx = np.random.choice(len(species_list), p=normalized_probs)
        selected_species = species_list[selected_idx]
        
        # Calculate confidence multiplier based on how certain we are
        max_prob = max(normalized_probs)
        if max_prob > 0.6:
            confidence_multiplier = 0.8  # High confidence in enhancement
        elif max_prob > 0.4:
            confidence_multiplier = 0.7  # Medium confidence
        else:
            confidence_multiplier = 0.6  # Lower confidence
        
        logger.debug(f"Selected {selected_species} from {species_list} with confidence multiplier {confidence_multiplier}")
        return selected_species, confidence_multiplier
    
    def _get_alternative_species(self, size_category: str, selected_species: str) -> List[str]:
        """Get alternative species suggestions for the same size category.
        
        Args:
            size_category: Animal size category
            selected_species: The selected primary species
            
        Returns:
            List of alternative species names
        """
        if size_category not in self.size_categories:
            return []
        
        all_species = self.size_categories[size_category]['species']
        alternatives = [species for species in all_species if species != selected_species]
        
        return alternatives[:2]  # Return top 2 alternatives
    
    def _map_amazon_to_european_species(self, amazon_species: str, size_category: str) -> Optional[str]:
        """Map Amazon rainforest species to European equivalents.
        
        Args:
            amazon_species: Original Amazon species classification
            size_category: Size category for additional context
            
        Returns:
            European species name or None if no mapping available
        """
        # Direct Amazon to European species mapping
        amazon_to_european_mapping = {
            'bos': {  # Cattle
                'large': 'wild_boar',
                'medium': 'red_deer', 
                'small': 'roe_deer'
            },
            'equus': {  # Horse
                'large': 'red_deer',
                'medium': 'roe_deer',
                'small': 'roe_deer'
            },
            'capra': {  # Goat
                'large': 'wild_boar',
                'medium': 'roe_deer',
                'small': 'roe_deer'
            },
            'mazama': {  # Brocket deer
                'large': 'red_deer',
                'medium': 'roe_deer',
                'small': 'roe_deer'
            },
            'pecari': {  # Peccary
                'large': 'wild_boar',
                'medium': 'wild_boar',
                'small': 'wild_boar'
            },
            'tapirus': {  # Tapir
                'large': 'wild_boar',
                'medium': 'red_deer',
                'small': 'roe_deer'
            },
            'sylvilagus': {  # Cottontail rabbit
                'large': 'european_hare',
                'medium': 'european_hare',
                'small': 'european_rabbit'
            },
            'dasyprocta': {  # Agouti
                'large': 'european_hare',
                'medium': 'european_rabbit',
                'small': 'red_squirrel'
            },
            'procyon': {  # Raccoon
                'large': 'european_badger',
                'medium': 'red_fox',
                'small': 'pine_marten'
            },
            'leopardus': {  # Small cats
                'large': 'red_fox',
                'medium': 'red_fox',
                'small': 'pine_marten'
            },
            'cerdocyon': {  # Crab-eating fox
                'large': 'red_fox',
                'medium': 'red_fox',
                'small': 'red_fox'
            },
            'didelphis': {  # Opossum
                'large': 'european_badger',
                'medium': 'pine_marten',
                'small': 'red_squirrel'
            }
        }
        
        species_lower = amazon_species.lower()
        if species_lower in amazon_to_european_mapping:
            size_mapping = amazon_to_european_mapping[species_lower]
            return size_mapping.get(size_category, list(size_mapping.values())[0])  # Default to first option
        
        return None
    
    def _should_enhance_species(self, species: str) -> bool:
        """Check if a species classification should be enhanced for European context.
        
        Args:
            species: Species name from classification
            
        Returns:
            True if species should be enhanced, False otherwise
        """
        if not species or species.lower() == 'unknown':
            return False
        
        # Always enhance generic terms
        generic_terms = ['animal', 'mammal', 'creature']
        if species.lower() in generic_terms:
            return True
        
        # For European regions, enhance Amazon species to European equivalents
        if self.region.lower() == 'europe':
            # Amazon species that should be mapped to European species
            amazon_to_european = {
                'bos': True,        # Cattle -> European ungulates (deer, wild boar)
                'equus': True,      # Horse -> European ungulates  
                'capra': True,      # Goat -> European ungulates
                'mazama': True,     # Brocket deer -> European deer
                'pecari': True,     # Peccary -> Wild boar
                'tapirus': True,    # Tapir -> Large European mammals
                'sylvilagus': True, # Cottontail rabbit -> European rabbit/hare
                'dasyprocta': True, # Agouti -> European small mammals
                'procyon': True,    # Raccoon -> European carnivores
                'leopardus': True,  # Small cats -> European carnivores
                'cerdocyon': True,  # Crab-eating fox -> European fox
                'didelphis': True,  # Opossum -> European small mammals
            }
            
            return amazon_to_european.get(species.lower(), False)
        
        return False
    
    def is_enhancement_applicable(self, region: str) -> bool:
        """Check if European species enhancement is applicable for the given region.
        
        Args:
            region: Geographic region
            
        Returns:
            True if enhancement should be applied, False otherwise
        """
        return region.lower() in ['europe', 'european', 'eu']