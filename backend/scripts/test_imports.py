
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.predictor.retraining import IncrementalRetrainer
    print("IncrementalRetrainer imported successfully.")
except ImportError as e:
    print(f"Failed to import IncrementalRetrainer: {e}")

try:
    from app.predictor.drift_detection import DriftDetector
    print("DriftDetector imported successfully.")
except ImportError as e:
    print(f"Failed to import DriftDetector: {e}")

try:
    from app.predictor.betting import VarianceReductionStrategy
    print("VarianceReductionStrategy imported successfully.")
except ImportError as e:
    print(f"Failed to import VarianceReductionStrategy: {e}")
