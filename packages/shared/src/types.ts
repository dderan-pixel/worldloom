import { z } from 'zod';

// Enums
export enum MarketState {
  OPEN = 'OPEN',
  FROZEN = 'FROZEN',
  RESOLVED = 'RESOLVED',
}

export enum Outcome {
  INVALID = 'INVALID',
  YES = 'YES',
  NO = 'NO',
}

export enum OrderSide {
  YES = 'YES',
  NO = 'NO',
}

export enum OrderStatus {
  PENDING = 'PENDING',
  OPEN = 'OPEN',
  FILLED = 'FILLED',
  PARTIALLY_FILLED = 'PARTIALLY_FILLED',
  CANCELLED = 'CANCELLED',
}

// Schemas
export const MarketSchema = z.object({
  id: z.number(),
  question: z.string(),
  endTime: z.number(),
  state: z.nativeEnum(MarketState),
  resolvedOutcome: z.nativeEnum(Outcome).optional(),
  oracle: z.string(),
  disputeWindow: z.number(),
  disputeEndsAt: z.number().optional(),
  createdAt: z.number(),
});

export const OrderSchema = z.object({
  id: z.string(),
  marketId: z.number(),
  user: z.string(),
  side: z.nativeEnum(OrderSide),
  price: z.number().min(0).max(1),
  size: z.number().positive(),
  filled: z.number().default(0),
  status: z.nativeEnum(OrderStatus),
  createdAt: z.number(),
});

export const TradeSchema = z.object({
  id: z.string(),
  marketId: z.number(),
  makerOrderId: z.string(),
  takerOrderId: z.string(),
  price: z.number(),
  size: z.number(),
  fee: z.number(),
  txHash: z.string().optional(),
  createdAt: z.number(),
});

export const BalanceSchema = z.object({
  user: z.string(),
  asset: z.string(),
  available: z.string(),
  locked: z.string(),
});

export const CreateOrderRequestSchema = z.object({
  marketId: z.number(),
  side: z.nativeEnum(OrderSide),
  price: z.number().min(0).max(1),
  size: z.number().positive(),
});

export const CreateMarketRequestSchema = z.object({
  question: z.string().min(10),
  endTime: z.number(),
  oracle: z.string(),
  disputeWindow: z.number().default(604800), // 7 days default
});

// Types
export type Market = z.infer<typeof MarketSchema>;
export type Order = z.infer<typeof OrderSchema>;
export type Trade = z.infer<typeof TradeSchema>;
export type Balance = z.infer<typeof BalanceSchema>;
export type CreateOrderRequest = z.infer<typeof CreateOrderRequestSchema>;
export type CreateMarketRequest = z.infer<typeof CreateMarketRequestSchema>;
