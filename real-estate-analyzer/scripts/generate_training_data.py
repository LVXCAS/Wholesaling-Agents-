#!/usr/bin/env python3
"""
Script to generate and validate training data for the renovation cost model.
"""
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.data.training_data_generator import TrainingDataGenerator
from app.models.renovation_model import RenovationModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Generating initial training data...")
        generator = TrainingDataGenerator()
        data_dir = os.path.join(project_root, 'app', 'data')
        initial_data_path = os.path.join(data_dir, 'renovation_costs.json')
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate initial dataset
        generator.save_training_data(initial_data_path)
        logger.info(f"Initial training data saved to {initial_data_path}")
        
        logger.info("Initializing renovation model...")
        model = RenovationModel()
        
        logger.info("Validating and augmenting training data...")
        # The model will automatically validate and augment the data during initialization
        
        logger.info("Training model with augmented dataset...")
        # The model will automatically train using the augmented dataset
        
        logger.info("Done! The model is ready to use.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
