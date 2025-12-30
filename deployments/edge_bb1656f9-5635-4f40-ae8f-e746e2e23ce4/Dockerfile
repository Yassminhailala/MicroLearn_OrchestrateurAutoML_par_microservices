
FROM python:3.10-slim
WORKDIR /app
COPY model_bb1656f9-5635-4f40-ae8f-e746e2e23ce4.joblib .
RUN pip install joblib scikit-learn pandas flask
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
