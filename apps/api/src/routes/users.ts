import { FastifyInstance } from 'fastify';

export async function userRoutes(fastify: FastifyInstance) {
  // Get user balances
  fastify.get('/:address/balances', async (request, reply) => {
    const { address } = request.params as { address: string };
    // TODO: Query from database or chain
    return { balances: [] };
  });

  // Get user positions
  fastify.get('/:address/positions', async (request, reply) => {
    const { address } = request.params as { address: string };
    // TODO: Query from database and outcome tokens
    return { positions: [] };
  });

  // Get user trades
  fastify.get('/:address/trades', async (request, reply) => {
    const { address } = request.params as { address: string };
    // TODO: Query from database
    return { trades: [] };
  });
}
