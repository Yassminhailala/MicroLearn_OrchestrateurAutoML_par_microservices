
import joblib
import pandas as pd
import sys

def run_inference(input_csv, output_csv):
    model = joblib.load('model_bb1656f9-5635-4f40-ae8f-e746e2e23ce4.joblib')
    data = pd.read_csv(input_csv)
    preds = model.predict(data)
    pd.DataFrame(preds).to_csv(output_csv, index=False)
    print("Batch inference completed.")

if __name__ == "__main__":
    run_inference(sys.argv[1], sys.argv[2])
