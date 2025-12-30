import { createClient } from 'redis';
import dotenv from 'dotenv';

dotenv.config();

const redisHost = process.env.REDIS_HOST || 'localhost';
const redisPort = process.env.REDIS_PORT || '6379';

const client = createClient({
    url: `redis://${redisHost}:${redisPort}`
});

client.on('error', (err) => console.error('Redis Client Error', err));

export const connectRedis = async () => {
    if (!client.isOpen) {
        await client.connect();
        console.log('Connected to Redis');
    }
};

const PREFIX = 'orchestrator:';

export const setPipelineState = async (pipelineId: string, data: any) => {
    await client.set(`${PREFIX}pipeline:${pipelineId}`, JSON.stringify(data));
};

export const getPipelineState = async (pipelineId: string) => {
    const data = await client.get(`${PREFIX}pipeline:${pipelineId}`);
    return data ? JSON.parse(data) : null;
};

export const updatePipelineStatus = async (pipelineId: string, status: string, step?: string, error?: string) => {
    const state = await getPipelineState(pipelineId);
    if (state) {
        state.status = status;
        if (step) state.currentStep = step;
        if (error) state.error = error;
        state.updatedAt = new Date().toISOString();
        state.history.push({
            status,
            step: step || state.currentStep,
            timestamp: state.updatedAt,
            error
        });
        await setPipelineState(pipelineId, state);
    }
};
