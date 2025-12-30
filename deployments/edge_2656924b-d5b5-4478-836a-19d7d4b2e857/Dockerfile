
FROM python:3.10-slim
WORKDIR /app
COPY model_2656924b-d5b5-4478-836a-19d7d4b2e857.joblib .
RUN pip install joblib scikit-learn pandas flask
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
