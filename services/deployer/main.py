from flask import Flask
from flask_restx import Api
from api.routes import api as deploy_ns
from db.models import init_db
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app, version='1.0', title='Deployer API',
    description='Microservice for deploying ML models',
    doc='/docs'
)

# Initialize Database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Register Namespace
api.add_namespace(deploy_ns, path='/deploy')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
