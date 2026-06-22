export interface AmenityTagProps {
  amenity: string;
}

export function AmenityTag({ amenity }: AmenityTagProps): JSX.Element {
  const label = amenity.replace(/_/g, ' ');
  return (
    <span className="rounded-md bg-gray-100 px-2 py-1 text-xs capitalize text-gray-600">{label}</span>
  );
}
