const INR = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) {
    return '—';
  }
  return INR.format(amount);
}

export function formatTime(value: string): string {
  const [hh, mm] = value.split(':');
  const hour = Number(hh);
  const period = hour >= 12 ? 'PM' : 'AM';
  const display = hour % 12 === 0 ? 12 : hour % 12;
  return `${display}:${mm} ${period}`;
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function formatSlotRange(start: string, end: string): string {
  return `${formatTime(start)} - ${formatTime(end)}`;
}

export function toISODate(date: Date): string {
  return date.toISOString().slice(0, 10);
}
