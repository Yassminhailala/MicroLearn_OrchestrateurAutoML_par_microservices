import express from 'express';
import dotenv from 'dotenv';
import { execute, getStatus } from './controllers/pipelineController';
import { connectRedis } from './services/redisService';
import { connectNats } from './services/natsService';

dotenv.config();

const app = express();
const port = process.env.PORT || 8080;

app.use(express.json());

// Routes
app.post('/pipeline/execute', execute);
app.get('/status/:pipeline_id', getStatus);

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

const start = async () => {
    try {
        await connectRedis();
        await connectNats();

        app.listen(port, () => {
            console.log(`Orchestrator listening at http://localhost:${port}`);
        });
    } catch (error) {
        console.error('Failed to start Orchestrator:', error);
        process.exit(1);
    }
};

start();
