import redis
import os
import json
import logging

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "hyperopt_redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def queue_optimization(run_id: str, data: dict):
    """
    Queues an optimization job in Redis.
    For this implementation, we can use a simple Redis list or FastAPI BackgroundTasks.
    The prompt mentioned Redis for parallelism, suggesting a worker pattern.
    """
    job_data = {"run_id": run_id, **data}
    redis_client.lpush("hyperopt_jobs", json.dumps(job_data))
    logger.info(f"Job {run_id} queued in Redis")

def get_next_job():
    job = redis_client.brpop("hyperopt_jobs", timeout=5)
    if job:
        return json.loads(job[1])
    return None
