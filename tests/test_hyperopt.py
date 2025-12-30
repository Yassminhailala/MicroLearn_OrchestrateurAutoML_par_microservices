import requests
import time
import json

BASE_URL = "http://localhost:8005"

def test_hyperopt():
    print("Testing HyperOpt Microservice...")
    
    # 1. Check Health
    try:
        health = requests.get(f"{BASE_URL}/health").json()
        print(f"Health Status: {health['status']}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Start Optimization
    payload = {
        "model": "XGBoost",
        "target_metric": "accuracy",
        "search_space": {
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1, 0.3],
            "max_depth": [3, 6, 9]
        },
        "n_trials": 5
    }
    
    print("\nStarting optimization task...")
    try:
        response = requests.post(f"{BASE_URL}/optimize", json=payload)
        response.raise_for_status()
        data = response.json()
        run_id = data["run_id"]
        print(f"Task accepted. Run ID: {run_id}")
    except Exception as e:
        print(f"Failed to start optimization: {e}")
        return

    # 3. Poll Status
    print("\nPolling status...")
    for _ in range(10):
        time.sleep(2)
        try:
            status_res = requests.get(f"{BASE_URL}/optimize/{run_id}")
            status_data = status_res.json()
            status = status_data["status"]
            print(f"Status: {status} | Completed: {status_data['trials_completed']}/5")
            
            if status == "completed":
                print("\nSUCCESS! Optimization finished.")
                print(f"Best Params: {status_data['best_params']}")
                print(f"Best Score: {status_data['best_score']}")
                return
            elif status == "failed":
                print("\nFAILURE! Task failed.")
                return
        except Exception as e:
            print(f"Error polling status: {e}")
            break
            
    print("\nTimeout waiting for completion (Task might still be running in background)")

if __name__ == "__main__":
    test_hyperopt()
