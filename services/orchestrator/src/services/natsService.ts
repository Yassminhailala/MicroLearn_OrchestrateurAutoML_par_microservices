import { connect, NatsConnection, JSONCodec } from 'nats';
import dotenv from 'dotenv';

dotenv.config();

const natsUrl = process.env.NATS_URL || 'nats://localhost:4222';
let nc: NatsConnection;
const jc = JSONCodec();

export const connectNats = async () => {
    try {
        nc = await connect({ servers: natsUrl });
        console.log(`Connected to NATS at ${natsUrl}`);
    } catch (err) {
        console.error('Error connecting to NATS:', err);
    }
};

export const publishEvent = (subject: string, data: any) => {
    if (nc) {
        nc.publish(subject, jc.encode(data));
        console.log(`Published to ${subject}:`, data);
    } else {
        console.warn('NATS not connected, cannot publish');
    }
};
