import { FastifyInstance } from 'fastify';
import { MarketSchema, CreateMarketRequestSchema } from '@predictx/shared';

export async function marketRoutes(fastify: FastifyInstance) {
  // Get all markets
  fastify.get('/', async (request, reply) => {
    // TODO: Query from database
    return { markets: [] };
  });

  // Get market by ID
  fastify.get('/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    // TODO: Query from database
    return { market: null };
  });

  // Create market (admin only)
  fastify.post('/', async (request, reply) => {
    try {
      const data = CreateMarketRequestSchema.parse(request.body);
      // TODO: Validate admin, create on-chain, store in DB
      return { success: true, marketId: 1 };
    } catch (error) {
      reply.code(400).send({ error: 'Invalid request' });
    }
  });

  // Get market orderbook
  fastify.get('/:id/orderbook', async (request, reply) => {
    const { id } = request.params as { id: string };
    // TODO: Fetch from Redis
    return {
      marketId: parseInt(id),
      bids: [],
      asks: [],
    };
  });

  // Get market trades
  fastify.get('/:id/trades', async (request, reply) => {
    const { id } = request.params as { id: string };
    // TODO: Query from database
    return { trades: [] };
  });
}
