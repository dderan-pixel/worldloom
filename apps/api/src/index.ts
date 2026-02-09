import Fastify from 'fastify';
import cors from '@fastify/cors';
import websocket from '@fastify/websocket';
import { config } from 'dotenv';
import { marketRoutes } from './routes/markets';
import { orderRoutes } from './routes/orders';
import { userRoutes } from './routes/users';

config();

const server = Fastify({
  logger: true,
});

// Register plugins
server.register(cors, {
  origin: process.env.CORS_ORIGIN || '*',
});

server.register(websocket);

// Health check
server.get('/health', async () => {
  return { status: 'ok', timestamp: Date.now() };
});

// Register routes
server.register(marketRoutes, { prefix: '/api/markets' });
server.register(orderRoutes, { prefix: '/api/orders' });
server.register(userRoutes, { prefix: '/api/users' });

// WebSocket for orderbook updates
server.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, req) => {
    connection.socket.on('message', (message) => {
      // Handle subscription to market orderbooks
      const data = JSON.parse(message.toString());
      if (data.type === 'subscribe' && data.marketId) {
        // TODO: Subscribe to Redis pub/sub for market updates
        connection.socket.send(JSON.stringify({
          type: 'subscribed',
          marketId: data.marketId,
        }));
      }
    });
  });
});

const start = async () => {
  try {
    const port = parseInt(process.env.PORT || '3001', 10);
    await server.listen({ port, host: '0.0.0.0' });
    console.log(`Server listening on port ${port}`);
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();
