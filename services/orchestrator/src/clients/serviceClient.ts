import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const URLS: Record<string, string | undefined> = {
    DataPreparer: process.env.DATA_PREPARER_URL,
    ModelSelector: process.env.MODEL_SELECTOR_URL,
    Trainer: process.env.TRAINER_URL,
    Evaluator: process.env.EVALUATOR_URL,
    Deployer: process.env.DEPLOYER_URL
};

export const callService = async (serviceName: string, params: any, pipelineId: string) => {
    const url = URLS[serviceName];
    if (!url) {
        throw new Error(`URL for service ${serviceName} not configured`);
    }

    // Map service names to their specific endpoints if needed
    let endpoint = '/execute'; // Default
    if (serviceName === 'DataPreparer') endpoint = '/process';
    if (serviceName === 'Trainer') endpoint = '/train';
    if (serviceName === 'Deployer') endpoint = '/deploy';

    try {
        const response = await axios.post(`${url}${endpoint}`, {
            ...params,
            pipeline_id: pipelineId
        });
        return response.data;
    } catch (error: any) {
        console.error(`Error calling ${serviceName}:`, error.message);
        throw error;
    }
};

export const getServiceStatus = async (serviceName: string, id: string) => {
    const url = URLS[serviceName];
    if (!url) throw new Error(`URL for service ${serviceName} not configured`);

    let endpoint = `/status/${id}`;
    if (serviceName === 'Trainer') endpoint = `/train/status/${id}`;

    try {
        const response = await axios.get(`${url}${endpoint}`);
        return response.data;
    } catch (error: any) {
        console.error(`Error getting status from ${serviceName}:`, error.message);
        throw error;
    }
};
