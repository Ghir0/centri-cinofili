'use client';

export interface CentroMapProps {
  lat: number
  lon: number
  nome: string
}

export default function CentroMap({ lat, lon, nome }: CentroMapProps) {
  return (
    <div className="flex h-48 w-full items-center justify-center rounded-lg bg-zinc-100 text-sm text-zinc-500">
      Mappa: {nome} ({lat}, {lon})
    </div>
  );
}
