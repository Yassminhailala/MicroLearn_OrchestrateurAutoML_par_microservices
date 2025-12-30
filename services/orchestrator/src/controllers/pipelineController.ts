import { Request, Response } from 'express';
import { executePipeline } from '../services/orchestratorService';
import { getPipelineState } from '../services/redisService';

export const execute = async (req: Request, res: Response) => {
    try {
        const pipelineDefinition = req.body;
        if (!pipelineDefinition || !pipelineDefinition.pipeline) {
            return res.status(400).json({ error: 'Invalid pipeline definition' });
        }

        const pipelineId = await executePipeline(pipelineDefinition);
        res.status(202).json({ pipeline_id: pipelineId, status: 'running' });
    } catch (error: any) {
        res.status(500).json({ error: error.message });
    }
};

export const getStatus = async (req: Request, res: Response) => {
    try {
        const { pipeline_id } = req.params;
        const state = await getPipelineState(pipeline_id);

        if (!state) {
            return res.status(404).json({ error: 'Pipeline not found' });
        }

        res.json(state);
    } catch (error: any) {
        res.status(500).json({ error: error.message });
    }
};
