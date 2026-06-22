import { Card } from '@/components/ui/Card';
import { formatCurrency } from '@/utils/formatters';
import { PLATFORM_CONVENIENCE_FEE_PER_HOUR } from '@/utils/constants';

export interface PriceBreakdownProps {
  pricePerHour: number;
  advanceDepositPercentage: number;
  hours: number;
}

export function PriceBreakdown({
  pricePerHour,
  advanceDepositPercentage,
  hours,
}: PriceBreakdownProps): JSX.Element {
  const totalPrice = pricePerHour * hours;
  const advance = (totalPrice * advanceDepositPercentage) / 100;
  const convenience = PLATFORM_CONVENIENCE_FEE_PER_HOUR * hours;
  const payableNow = advance + convenience;
  const dueAtVenue = totalPrice - advance;

  return (
    <Card>
      <h3 className="mb-3 font-semibold text-gray-900">Price summary</h3>
      <dl className="space-y-2 text-sm">
        <Row label={`Slot total (${hours} hr)`} value={formatCurrency(totalPrice)} />
        <Row label={`Advance deposit (${advanceDepositPercentage}%)`} value={formatCurrency(advance)} />
        <Row label="Convenience fee" value={formatCurrency(convenience)} />
        <div className="my-2 border-t border-dashed" />
        <Row label="Payable now" value={formatCurrency(payableNow)} strong />
        <Row label="Due at venue" value={formatCurrency(dueAtVenue)} muted />
      </dl>
    </Card>
  );
}

function Row({
  label,
  value,
  strong,
  muted,
}: {
  label: string;
  value: string;
  strong?: boolean;
  muted?: boolean;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between">
      <dt className={muted ? 'text-gray-400' : 'text-gray-600'}>{label}</dt>
      <dd className={`${strong ? 'text-base font-semibold text-gray-900' : 'text-gray-800'}`}>{value}</dd>
    </div>
  );
}
