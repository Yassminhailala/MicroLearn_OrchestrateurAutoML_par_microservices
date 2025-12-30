
FROM python:3.10-slim
WORKDIR /app
COPY model_d7c140ea-eb8e-49f3-b636-6b3171c37f9f.joblib .
RUN pip install joblib scikit-learn pandas flask
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
