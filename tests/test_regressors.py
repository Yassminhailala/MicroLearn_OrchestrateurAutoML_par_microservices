import sys
import os
from unittest.mock import MagicMock

# 1. Mock Modules BEFORE interactions
sys.modules["torch"] = MagicMock()
sys.modules["pytorch_lightning"] = MagicMock()
sys.modules["pytorch_lightning.loggers"] = MagicMock()
sys.modules["ray"] = MagicMock()
sys.modules["ray.train"] = MagicMock()
sys.modules["ray.train.torch"] = MagicMock()
sys.modules["minio"] = MagicMock()
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()
sys.modules["src.database"] = MagicMock()
sys.modules["src.models"] = MagicMock()
sys.modules["services.trainer.src.database"] = MagicMock()
sys.modules["services.trainer.src.models"] = MagicMock()
sys.modules["xgboost"] = MagicMock()
sys.modules["joblib"] = MagicMock()
sys.modules["numpy"] = MagicMock()

# Mock Pandas
pandas_mock = MagicMock()
sys.modules["pandas"] = pandas_mock

# Helper to create mock DataFrames
def mock_dataframe(data):
    df = MagicMock()
    df.columns = list(data.keys())
    
    # Mock drop -> returns new mock (X)
    X_mock = MagicMock()
    X_mock.values.astype.return_value = "numpy_X" # placeholder
    df.drop.return_value = X_mock
    
    # Mock __getitem__ -> returns new mock (y)
    y_mock = MagicMock()
    y_mock.values.astype.return_value = "numpy_y"
    y_mock.dtype = "float" # Simulating numeric
    
    df.__getitem__.return_value = y_mock
    
    return df

pandas_mock.DataFrame = mock_dataframe
pandas_mock.read_csv = MagicMock(return_value=mock_dataframe({"feature": [1], "target": [10]}))

# Mock src.utils
utils_mock = MagicMock()
sys.modules["src.utils"] = utils_mock
utils_mock.update_job_status = MagicMock()
utils_mock.save_checkpoint_to_minio = MagicMock()
utils_mock.get_minio_client = MagicMock()

# Mock sklearn imports logic
sklearn_mock = MagicMock()
sys.modules["sklearn.svm"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()
sys.modules["sklearn.metrics"] = MagicMock()
sys.modules["sklearn.model_selection"] = MagicMock()
sys.modules["sklearn.preprocessing"] = MagicMock()

# Params capture
params_captured = {}

class MockModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        name = self.__class__.__name__
        params_captured[name] = kwargs
        
    def fit(self, X, y):
        pass
    def predict(self, X):
        return [1] * 5

class MockSVR(MockModel): pass
class MockRF(MockModel): pass
class MockXGB(MockModel): pass
class MockSVC(MockModel): pass

sys.modules["sklearn.svm"].SVR = MockSVR
sys.modules["sklearn.svm"].SVC = MockSVC
sys.modules["sklearn.ensemble"].RandomForestRegressor = MockRF
sys.modules["sklearn.ensemble"].RandomForestClassifier = MockRF
sys.modules["xgboost"].XGBRegressor = MockXGB
sys.modules["xgboost"].XGBClassifier = MockXGB

# Mock train_test_split
sys.modules["sklearn.model_selection"].train_test_split = MagicMock(return_value=(
    "X_train", "X_test", "y_train", "y_test"
))

# 2. Setup Path
trainer_path = os.path.join(os.getcwd(), "services", "trainer")
sys.path.append(trainer_path)

# 3. Import
from src.trainer_logic import start_training
import src.trainer_logic
src.trainer_logic.load_dataset_from_minio = MagicMock(return_value=mock_dataframe({
    "feature": [1], "target": [10]
}))

def test_param_filtering():
    print("\n--- Testing Param Filtering ---")
    
    full_params = {
        "C": 1.0, 
        "data_id": "123", 
        "target_column": "target",
        "metrics": ["rmse"]
    }
    
    try:
        start_training("job_svr_real", "SVM Regressor", "123", full_params)
        
        svr_params = params_captured.get("MockSVR")
        print(f"Captured SVR Params: {svr_params}")
        
        if svr_params is None:
             print("❌ FAILURE: MockSVR not initialized")
             return

        if "data_id" in svr_params:
            print("❌ FAILURE: data_id leaked into SVR params")
        elif "C" in svr_params and svr_params["C"] == 1.0:
            print("✅ SUCCESS: SVR params clean")
        else:
            print("❌ FAILURE: SVR params missing or incorrect")
            
    except Exception as e:
        print(f"❌ Exception during training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_param_filtering()
