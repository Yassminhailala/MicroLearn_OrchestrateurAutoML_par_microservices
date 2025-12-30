from flask import request
from flask_restx import Namespace, Resource, fields
from db.models import SessionLocal, Deployment
from services.deployment_service import process_deployment
import logging

logger = logging.getLogger(__name__)

api = Namespace('deploy', description='Deployment operations')

deploy_model = api.model('DeployRequest', {
    'model_id': fields.String(required=True, description='The ID of the trained model'),
    'type': fields.String(required=True, enum=['rest', 'batch', 'edge'], description='Deployment type')
})

@api.route('/')
class DeployList(Resource):
    @api.doc('list_deployments')
    def get(self):
        """List all deployments"""
        db = SessionLocal()
        try:
            deployments = db.query(Deployment).all()
            return [{
                "id": str(d.id),
                "model_id": d.model_id,
                "type": d.deployment_type,
                "url": d.endpoint_url,
                "status": d.status,
                "created_at": d.created_at.isoformat()
            } for d in deployments], 200
        finally:
            db.close()

    @api.expect(deploy_model)
    def post(self):
        """Deploy a model"""
        data = request.json
        model_id = data.get('model_id')
        deploy_type = data.get('type')
        
        db = SessionLocal()
        new_deployment = Deployment(
            model_id=model_id,
            deployment_type=deploy_type,
            status="processing"
        )
        db.add(new_deployment)
        db.commit()
        db.refresh(new_deployment)
        
        try:
            logger.info(f"Starting deployment for model {model_id} (type: {deploy_type})")
            url = process_deployment(model_id, deploy_type)
            
            new_deployment.status = "success"
            new_deployment.endpoint_url = url
            db.commit()
            
            return {
                "deployment_id": str(new_deployment.id),
                "model_id": model_id,
                "type": deploy_type,
                "url": url,
                "status": "success"
            }, 201
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            new_deployment.status = "failed"
            db.commit()
            return {"error": str(e)}, 500
        finally:
            db.close()

@api.route('/health')
class Health(Resource):
    def get(self):
        """Service health check"""
        # Could add DB connectivity check here
        return {"status": "healthy"}, 200
