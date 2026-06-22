import type { HTMLAttributes } from 'react';

type Tone = 'green' | 'red' | 'gray' | 'amber' | 'blue';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const TONES: Record<Tone, string> = {
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
  gray: 'bg-gray-100 text-gray-700',
  amber: 'bg-amber-100 text-amber-800',
  blue: 'bg-blue-100 text-blue-800',
};

export function Badge({ tone = 'gray', className = '', children, ...rest }: BadgeProps): JSX.Element {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}
      {...rest}
    >
      {children}
    </span>
  );
}
