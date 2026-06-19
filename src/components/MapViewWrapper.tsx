"use client";

import dynamic from "next/dynamic";
import type { MapMarker } from "./MapView";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => (
    <div className="h-full bg-[color:var(--ds-gray-50)] rounded-lg flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin h-8 w-8 border-2 border-[color:var(--ds-gray-300)] border-t-[color:var(--ds-gray-900)] rounded-full mx-auto mb-3" />
        <p className="text-sm text-[color:var(--ds-gray-500)] font-mono">Caricamento mappa…</p>
      </div>
    </div>
  ),
});

interface MapViewWrapperProps {
  markers: MapMarker[];
}

export default function MapViewWrapper({ markers }: MapViewWrapperProps) {
  return <MapView markers={markers} />;
}
