import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

export const registerSchema = z
  .object({
    email: z.string().email('Enter a valid email'),
    phone: z.string().regex(/^\+?[1-9]\d{9,14}$/, 'Enter a valid phone number'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    name: z.string().min(2, 'Name is required'),
    role: z.enum(['turf_owner', 'player']),
    business_name: z.string().max(255).optional(),
  })
  .refine((data) => data.role !== 'turf_owner' || !!data.business_name, {
    message: 'Business name is required for turf owners',
    path: ['business_name'],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
