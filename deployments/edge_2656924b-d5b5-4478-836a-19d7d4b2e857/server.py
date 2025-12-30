
from flask import Flask, request, jsonify
import joblib
import os
app = Flask(__name__)
model = joblib.load(os.listdir('.')[0]) # loads first file (the model)
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json['data']
    return jsonify({'prediction': model.predict([data]).tolist()})
app.run(host='0.0.0.0', port=8080)
