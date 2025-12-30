# AutoML Orchestrator Microservice

This microservice coordinates the AutoML pipeline by calling individual microservices in sequence and tracking their state.

## Features
- **Async Orchestration**: Receives a pipeline definition and executes it in the background.
- **State Management**: Uses Redis to store pipeline status, current step, and history.
- **Event Driven**: Publishes events to NATS for every state change (monitoring/notifications).
- **Service Coordination**: Calls DataPreparer, ModelSelector, Trainer, Evaluator, and Deployer via HTTP.

## API Endpoints

### Execute Pipeline
`POST /pipeline/execute`
Request Body:
```json
{
  "pipeline": [
    { "step": "DataPreparer", "params": { ... } },
    { "step": "ModelSelector", "params": { ... } },
    { "step": "Trainer", "params": { ... } },
    { "step": "Evaluator" },
    { "step": "Deployer", "params": { "type": "rest" } }
  ]
}
```
Response:
```json
{
  "pipeline_id": "uuid-v4",
  "status": "running"
}
```

### Get Pipeline Status
`GET /status/:pipeline_id`
Returns the full state of the pipeline including history and errors.

## Environment Variables
- `PORT`: Server port (default 8080)
- `NATS_URL`: NATS server address
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `DATA_PREPARER_URL`: DataPreparer service URL
... (and other service URLs)
