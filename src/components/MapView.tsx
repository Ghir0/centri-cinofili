"use client";

import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export interface MapMarker {
  id: number;
  slug: string;
  nome: string;
  indirizzo: string | null;
  comune: string | null;
  provincia_sigla: string | null;
  lat: number;
  lon: number;
}

interface MapViewProps {
  markers: MapMarker[];
}

export default function MapView({ markers }: MapViewProps) {
  useEffect(() => {
    // Fix default marker icon path (Leaflet + bundler issue)
    delete (L.Icon.Default.prototype as any)._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });

    // Initialize map
    const map = L.map("map-container", {
      center: [43.0, 11.5], // Center of Italy
      zoom: 6,
      scrollWheelZoom: true,
    });

    // Tile layer (OpenStreetMap)
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    // Add markers
    const bounds: L.LatLngExpression[] = [];

    for (const m of markers) {
      if (!m.lat || !m.lon) continue;

      const latlng: L.LatLngExpression = [m.lat, m.lon];
      bounds.push(latlng);

      const marker = L.marker(latlng).addTo(map);

      const popupHtml = `
        <div style="font-family:system-ui,sans-serif;min-width:180px">
          <strong style="font-size:14px">${m.nome}</strong>
          <div style="font-size:12px;color:#666;margin:4px 0">
            ${[m.indirizzo, m.comune, m.provincia_sigla ? `(${m.provincia_sigla})` : null]
              .filter(Boolean)
              .join(", ")}
          </div>
          <a href="/centro/${m.slug}/" 
             style="font-size:12px;color:#0369a1;text-decoration:underline">
            Apri scheda →
          </a>
        </div>
      `;
      marker.bindPopup(popupHtml);
    }

    // Fit map to show all markers
    if (bounds.length > 0) {
      map.fitBounds(bounds as L.LatLngBoundsExpression, { padding: [40, 40], maxZoom: 12 });
    }

    return () => {
      map.remove();
    };
  }, [markers]);

  return <div id="map-container" className="h-full w-full" />;
}
