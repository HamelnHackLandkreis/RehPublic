"""European species mapping and classification enhancement with intelligent analysis."""

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
    """Maps generic classifications to specific European species using intelligent analysis."""
    
    def __init__(self, region: str):
        """Initialize species mapper for a specific region.
        
        Args:
            region: Geographic region for species mapping
        """
        self.region = region
        self.species_mapping = get_european_species_mapping()
        self.size_categories = get_european_size_categories()
        
        # European species that might appear in Amazon model predictions
        self.european_species_keywords = {
            'procyon': 'red_fox',  # Procyon (raccoon) -> European fox
            'canis': 'red_fox',    # Canis -> European fox
            'equus': 'red_deer',   # Horse -> Large European ungulate
            'capra': 'roe_deer',   # Goat -> European deer
            'sylvilagus': 'european_hare',  # Cottontail -> European hare
            'lepus': 'european_hare',       # Hare genus
            'sciurus': 'red_squirrel',      # Squirrel
            'vulpes': 'red_fox',            # Fox genus
            'cervus': 'red_deer',           # Deer genus
            'sus': 'wild_boar',             # Pig genus
            'meles': 'european_badger',     # Badger genus
            'martes': 'pine_marten',        # Marten genus
        }
        
        # Amazon to European species mapping with confidence thresholds
        self.amazon_to_european = {
            'bos': {
                'threshold': 0.6,  # Only map if confidence is reasonable
                'large': 'wild_boar',
                'medium': 'red_deer', 
                'small': 'roe_deer'
            },
            'equus': {
                'threshold': 0.5,
                'large': 'red_deer',
                'medium': 'roe_deer',
                'small': 'roe_deer'
            },
            'procyon': {  # Raccoon - direct mapping regardless of size
                'threshold': 0.01,  # Very low threshold since it's a good match
                'large': 'red_fox',
                'medium': 'red_fox',
                'small': 'red_fox'
            },
            'mazama': {  # Brocket deer
                'threshold': 0.3,
                'large': 'red_deer',
                'medium': 'roe_deer',
                'small': 'roe_deer'
            },
            'sylvilagus': {  # Cottontail rabbit
                'threshold': 0.2,
                'large': 'european_hare',
                'medium': 'european_hare',
                'small': 'european_rabbit'
            },
            'leopardus': {  # Small cats
                'threshold': 0.4,
                'large': 'red_fox',
                'medium': 'red_fox',
                'small': 'pine_marten'
            }
        }
    
    def map_to_european_species(
        self, 
        detection: Dict[str, Any], 
        classification: Dict[str, Any], 
        image: np.ndarray,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Map animal classification to specific European species using intelligent analysis.
        
        Args:
            detection: Detection result with bounding box information
            classification: Classification result from model
            image: Original image as numpy array
            timestamp: Optional timestamp for temporal context
            
        Returns:
            Enhanced classification with European species information
        """
        # Get primary species and all confidence scores
        primary_species = classification.get('prediction', 
                         classification.get('class_name', 
                         classification.get('species', 'unknown')))
        
        all_confidences = classification.get('all_confidences', [])
        primary_confidence = float(classification.get('confidence', 0.5))
        
        logger.debug(f"Analyzing classification: primary='{primary_species}' (conf: {primary_confidence:.3f})")
        
        # Step 1: Look for direct European species matches in the confidence distribution
        european_species_found = self._find_european_species_in_predictions(all_confidences)
        if european_species_found:
            species_name, confidence, method = european_species_found
            logger.debug(f"Found European species in predictions: {species_name} (conf: {confidence:.3f})")
            return self._create_enhanced_result(species_name, confidence, method, primary_species, classification)
        
        # Step 2: Look for Amazon species that can be mapped to European equivalents
        amazon_mapping = self._find_amazon_species_mapping(all_confidences, detection, image)
        if amazon_mapping:
            species_name, confidence, method = amazon_mapping
            logger.debug(f"Mapped Amazon species to European: {species_name} (conf: {confidence:.3f})")
            return self._create_enhanced_result(species_name, confidence, method, primary_species, classification)
        
        # Step 3: Fallback to size-based mapping if no specific species found
        logger.debug(f"Using fallback size-based mapping for '{primary_species}'")
        size_category = self._analyze_animal_size(detection, image)
        habitat_context = self._infer_habitat_from_image(image)
        time_context = self._get_temporal_context(timestamp)
        
        probable_species, confidence_multiplier = self._determine_species_by_size(
            size_category, habitat_context, time_context
        )
        
        enhanced_confidence = primary_confidence * confidence_multiplier
        
        return self._create_enhanced_result(
            probable_species, enhanced_confidence, 'size_based_mapping', 
            primary_species, classification, size_category, habitat_context, time_context
        )
    
    def _find_european_species_in_predictions(self, all_confidences: List[List]) -> Optional[Tuple[str, float, str]]:
        """Look for European species keywords in the prediction confidence list.
        
        Args:
            all_confidences: List of [species_name, confidence] pairs
            
        Returns:
            Tuple of (european_species, confidence, method) or None
        """
        if not all_confidences:
            return None
        
        # Look for European species keywords
        for species_name, confidence in all_confidences:
            species_lower = species_name.lower()
            
            # Check if any European species keyword matches
            for keyword, european_species in self.european_species_keywords.items():
                if keyword in species_lower:
                    # Use the original confidence but boost it slightly for being a good match
                    boosted_confidence = min(confidence * 1.2, 0.95)
                    logger.debug(f"Found European keyword '{keyword}' in '{species_name}' -> {european_species}")
                    return european_species, boosted_confidence, 'keyword_mapping'
        
        return None
    
    def _find_amazon_species_mapping(
        self, 
        all_confidences: List[List], 
        detection: Dict[str, Any], 
        image: np.ndarray
    ) -> Optional[Tuple[str, float, str]]:
        """Look for Amazon species that can be mapped to European equivalents.
        
        Args:
            all_confidences: List of [species_name, confidence] pairs
            detection: Detection result for size analysis
            image: Original image
            
        Returns:
            Tuple of (european_species, confidence, method) or None
        """
        if not all_confidences:
            return None
        
        size_category = self._analyze_animal_size(detection, image)
        
        # Look through all predictions for mappable Amazon species
        for species_name, confidence in all_confidences:
            species_lower = species_name.lower()
            
            # Check if this Amazon species can be mapped
            for amazon_species, mapping_info in self.amazon_to_european.items():
                if amazon_species in species_lower:
                    # Check if confidence meets threshold
                    if confidence >= mapping_info['threshold']:
                        european_species = mapping_info.get(size_category, mapping_info['medium'])
                        
                        # Adjust confidence based on mapping quality
                        if amazon_species == 'procyon':  # Raccoon is a good match for fox
                            adjusted_confidence = confidence * 0.9
                        elif amazon_species in ['mazama', 'equus']:  # Deer-like animals
                            adjusted_confidence = confidence * 0.8
                        else:
                            adjusted_confidence = confidence * 0.7
                        
                        logger.debug(f"Mapped Amazon '{species_name}' -> European '{european_species}' (size: {size_category})")
                        return european_species, adjusted_confidence, f'amazon_mapping_{amazon_species}'
        
        return None
    
    def _create_enhanced_result(
        self, 
        species: str, 
        confidence: float, 
        method: str, 
        original_species: str,
        original_classification: Dict[str, Any],
        size_category: str = None,
        habitat_context: str = None,
        time_context: str = None
    ) -> Dict[str, Any]:
        """Create enhanced classification result.
        
        Args:
            species: Enhanced species name
            confidence: Enhanced confidence score
            method: Enhancement method used
            original_species: Original species classification
            original_classification: Original classification dict
            size_category: Size category if available
            habitat_context: Habitat context if available
            time_context: Temporal context if available
            
        Returns:
            Enhanced classification dictionary
        """
        # Get alternative species
        alternatives = self._get_alternative_species_for_result(species, size_category)
        
        enhanced_result = {
            'species': species,
            'confidence': min(confidence, 0.95),  # Cap confidence at 95%
            'classification_method': f'enhanced_european_mapping_{method}',
            'original_classification': original_species,
            'alternative_species': alternatives,
            'enhancement_factors': {
                'method': method,
                'size_analysis': size_category or 'unknown',
                'habitat_context': habitat_context or 'unknown',
                'temporal_context': time_context or 'unknown'
            }
        }
        
        logger.debug(f"Enhanced classification: {species} (confidence: {confidence:.3f}, method: {method})")
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
    
    def _determine_species_by_size(
        self, 
        size_category: str, 
        habitat_context: str, 
        time_context: str
    ) -> Tuple[str, float]:
        """Determine European species based on size and context (fallback method).
        
        Args:
            size_category: Animal size category
            habitat_context: Habitat inference
            time_context: Temporal context
            
        Returns:
            Tuple of (species_name, confidence_multiplier)
        """
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
            confidence_multiplier = 0.6  # Lower confidence for fallback method
        elif max_prob > 0.4:
            confidence_multiplier = 0.5  # Medium confidence
        else:
            confidence_multiplier = 0.4  # Lower confidence
        
        logger.debug(f"Selected {selected_species} from {species_list} with confidence multiplier {confidence_multiplier}")
        return selected_species, confidence_multiplier
    
    def _get_alternative_species_for_result(self, selected_species: str, size_category: str = None) -> List[str]:
        """Get alternative species suggestions.
        
        Args:
            selected_species: The selected primary species
            size_category: Size category if available
            
        Returns:
            List of alternative species names
        """
        alternatives = []
        
        # If we have size category, get alternatives from same category
        if size_category and size_category in self.size_categories:
            all_species = self.size_categories[size_category]['species']
            alternatives = [species for species in all_species if species != selected_species]
        
        # Add some general European alternatives if not enough
        if len(alternatives) < 2:
            general_alternatives = ['red_fox', 'roe_deer', 'european_hare', 'wild_boar']
            for alt in general_alternatives:
                if alt != selected_species and alt not in alternatives:
                    alternatives.append(alt)
                if len(alternatives) >= 2:
                    break
        
        return alternatives[:2]  # Return top 2 alternatives
    
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