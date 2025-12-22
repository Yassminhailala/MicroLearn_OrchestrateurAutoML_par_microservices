import sys
import os
from unittest.mock import MagicMock

# 1. Mock Modules BEFORE import
sys.modules["torch"] = MagicMock()
sys.modules["pytorch_lightning"] = MagicMock()
sys.modules["pytorch_lightning.loggers"] = MagicMock()
sys.modules["ray"] = MagicMock()
sys.modules["ray.train"] = MagicMock()
sys.modules["ray.train.torch"] = MagicMock()

# Mock sklearn
sklearn_mock = MagicMock()
sys.modules["sklearn"] = sklearn_mock
sys.modules["sklearn.svm"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()

# Specific classes checks
svc_mock = MagicMock()
svr_mock = MagicMock()
rf_clf_mock = MagicMock()
rf_reg_mock = MagicMock()

sys.modules["sklearn.svm"].SVC = MagicMock(return_value=svc_mock)
sys.modules["sklearn.svm"].SVR = MagicMock(return_value=svr_mock)
sys.modules["sklearn.ensemble"].RandomForestClassifier = MagicMock(return_value=rf_clf_mock)
sys.modules["sklearn.ensemble"].RandomForestRegressor = MagicMock(return_value=rf_reg_mock)

# Mock joblib
joblib_mock = MagicMock()
sys.modules["joblib"] = joblib_mock

# Mock numpy
sys.modules["numpy"] = MagicMock()

# Mock MinIO and DB deps for utils
sys.modules["minio"] = MagicMock()
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()

# Mock src.utils completely to avoid import issues and side effects
utils_mock = MagicMock()
sys.modules["src.utils"] = utils_mock
# Ensure attributes exist
utils_mock.update_job_status = MagicMock()
utils_mock.save_checkpoint_to_minio = MagicMock()

# Mock local modules just in case (though utils mock might suffice if imports specific attributes)
sys.modules["src.database"] = MagicMock()
sys.modules["src.models"] = MagicMock()
sys.modules["services.trainer.src.database"] = MagicMock()
sys.modules["services.trainer.src.models"] = MagicMock()

# 2. Setup Path
trainer_path = os.path.join(os.getcwd(), "services", "trainer")
sys.path.append(trainer_path)

# 3. Import System-Under-Test
from src.trainer_logic import start_training

# 4. Helpers alias for verification
utils = utils_mock

def test_svm_flow():
    print("\n--- Testing SVM Flow ---")
    start_training("job_svm_1", "SVM Classifier", "data_1", {"C": 1.0})
    
    # Debug
    print("Update Job Status Calls:", utils.update_job_status.call_args_list)
    
    # Verify SVC initialized
    try:
        sys.modules["sklearn.svm"].SVC.assert_called()
    except AssertionError as e:
        print(f"SVC Mock Call Count: {sys.modules['sklearn.svm'].SVC.call_count}")
        raise e

    # Verify save
    joblib_mock.dump.assert_called()
    utils.save_checkpoint_to_minio.assert_called()
    utils.update_job_status.assert_called_with("job_svm_1", "completed", result={'status': 'success', 'accuracy': 0.95})
    print("✅ SVM Flow Verified")

def test_rf_flow():
    print("\n--- Testing RandomForest Flow ---")
    start_training("job_rf_1", "RandomForest Classifier", "data_1", {"n_estimators": 10})
    
    # Verify RF initialized
    sys.modules["sklearn.ensemble"].RandomForestClassifier.assert_called()
    print("✅ RandomForest Flow Verified")

if __name__ == "__main__":
    try:
        test_svm_flow()
        test_rf_flow()
        print("\nSUCCESS: All logic flows verified.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
