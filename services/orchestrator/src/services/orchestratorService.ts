import { v4 as uuidv4 } from 'uuid';
import { setPipelineState, updatePipelineStatus } from './redisService';
import { publishEvent } from './natsService';
import { callService, getServiceStatus } from '../clients/serviceClient';

export const executePipeline = async (pipelineDefinition: any) => {
    const pipelineId = uuidv4();

    const initialState = {
        id: pipelineId,
        status: 'running',
        currentStep: pipelineDefinition.pipeline[0].step,
        history: [],
        definition: pipelineDefinition,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };

    await setPipelineState(pipelineId, initialState);
    publishEvent('pipeline.start', { pipelineId });

    // Start background orchestration
    runOrchestration(pipelineId, pipelineDefinition).catch(err => {
        console.error(`Pipeline ${pipelineId} fatal error:`, err);
    });

    return pipelineId;
};

const runOrchestration = async (pipelineId: string, definition: any) => {
    const steps = definition.pipeline;
    const context: Record<string, any> = {};

    for (const step of steps) {
        const stepName = step.step;
        let params = { ... (step.params || {}) };

        // 1. Dependency Injection: Look for required fields in context if missing
        if (!params.dataset_id && context.DataPreparer?.dataset_id) {
            params.dataset_id = context.DataPreparer.dataset_id;
        }
        if (!params.recommendation_id && context.ModelSelector?.recommendation_id) {
            params.recommendation_id = context.ModelSelector.recommendation_id;
        }
        // Specific for Evaluator/Deployer
        if (!params.model_ids && context.Trainer?.model_ids) {
            params.model_ids = context.Trainer.model_ids;
        }
        if (!params.model_id && context.Trainer?.best_model_id) {
            params.model_id = context.Trainer.best_model_id;
        }

        try {
            await updatePipelineStatus(pipelineId, 'running', stepName);
            publishEvent('pipeline.step.start', { pipelineId, step: stepName });

            console.log(`Executing step ${stepName} for pipeline ${pipelineId}`);
            let result = await callService(stepName, params, pipelineId);

            // 2. Polling for Async Services
            if (stepName === 'DataPreparer' || stepName === 'Trainer' || stepName === 'Evaluator') {
                const jobId = result.job_id || result.batch_job_id || result.pipeline_id;
                result = await pollServiceStatus(stepName, jobId);
            }

            // 3. Store in Context
            context[stepName] = result;

            await updatePipelineStatus(pipelineId, 'success', stepName);
            publishEvent('pipeline.step.success', { pipelineId, step: stepName, result });

        } catch (error: any) {
            const errorMessage = error.response?.data?.error || error.message;
            await updatePipelineStatus(pipelineId, 'failed', stepName, errorMessage);
            publishEvent('pipeline.step.failed', { pipelineId, step: stepName, error: errorMessage });
            publishEvent('pipeline.failed', { pipelineId, error: errorMessage });
            return; // Stop execution
        }
    }

    await updatePipelineStatus(pipelineId, 'success');
    publishEvent('pipeline.completed', { pipelineId });
};

const pollServiceStatus = async (serviceName: string, jobId: string) => {
    const delay = 3000;
    while (true) {
        await new Promise(resolve => setTimeout(resolve, delay));

        console.log(`Polling status for ${serviceName} ID ${jobId}...`);
        const response = await getServiceStatus(serviceName, jobId);

        const status = (response.status || '').toLowerCase();
        if (status === 'completed' || status === 'success') {
            console.log(`${serviceName} ID ${jobId} finished with success.`);
            return response;
        }
        if (status === 'failed' || status === 'error') {
            throw new Error(`Step ${serviceName} failed: ${response.error || 'Unknown error'}`);
        }
    }
};
