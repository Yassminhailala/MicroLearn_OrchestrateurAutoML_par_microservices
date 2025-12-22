from fastapi import FastAPI
from .api.routes import router
from .db.session import engine, Base
import logging

import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables with retry
def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
        except Exception as e:
            logger.error(f"Database connection failed: {e}. Retrying in 5s...")
            retries -= 1
            time.sleep(5)
    logger.error("Could not connect to database after multiple retries")

app = FastAPI(title="AutoML HyperOpt Service")

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("HyperOpt service starting up...")
