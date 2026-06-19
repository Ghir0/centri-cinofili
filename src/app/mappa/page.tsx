import { searchCentri, getTassonomieForFilters, getProvinceByRegione } from "@/lib/centri";
import { FiltersBar } from "@/components/FiltersBar";
import { Suspense } from "react";
import MapViewWrapper from "@/components/MapViewWrapper";

// Force dynamic rendering
export const dynamic = "force-dynamic";

interface MappaPageProps {
  searchParams: Promise<{
    q?: string;
    regione?: string;
    provincia?: string;
    metodologia?: string | string[];
    disciplina?: string | string[];
    infrastruttura?: string | string[];
    affiliazione?: string | string[];
  }>;
}

function toArray(v: string | string[] | undefined): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export default async function MappaPage({ searchParams }: MappaPageProps) {
  const sp = await searchParams;

  const filters = {
    q: sp.q,
    regione: sp.regione,
    provincia: sp.provincia,
    metodologie: toArray(sp.metodologia),
    discipline: toArray(sp.disciplina),
    infrastrutture: toArray(sp.infrastruttura),
    affiliazioni: toArray(sp.affiliazione),
    sort: "name" as const,
  };

  const [tassonomie, province, results] = await Promise.all([
    getTassonomieForFilters(),
    sp.regione ? getProvinceByRegione(sp.regione) : Promise.resolve([]),
    searchCentri(filters),
  ]);

  // Filter to only centers with GPS coordinates
  const mapMarkers = results
    .filter((c) => c.coordinate_gps)
    .map((c) => ({
      id: c.id,
      slug: c.slug,
      nome: (c.brand_name || c.ragione_sociale),
      indirizzo: c.indirizzo,
      comune: c.comune,
      provincia_sigla: c.provincia_sigla,
      lat: c.coordinate_gps!.lat,
      lon: c.coordinate_gps!.lon,
    }));

  return (
    <>
      {/* Hero compatto */}
      <section className="border-b border-[color:var(--ds-gray-100)] bg-white">
        <div className="mx-auto max-w-7xl px-6 pt-10 pb-8">
          <div className="flex items-center gap-2 mb-4">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]" />
            <span className="text-eyebrow">Navigazione geografica</span>
          </div>
          <h1 className="text-display max-w-2xl">Mappa dei centri cinofili</h1>
          <p className="mt-3 max-w-xl text-base text-[color:var(--ds-gray-500)]">
            Esplora i centri sulla mappa. Usa i filtri per restringere la ricerca e clicca
            sui marker per aprire la scheda completa.
          </p>
        </div>
      </section>

      {/* Filters + Map */}
      <section className="mx-auto max-w-7xl px-6 py-8">
        <Suspense fallback={<div className="card-flat p-4 h-12 animate-pulse mb-4" />}>
          <FiltersBar
            regioni={tassonomie.regioni}
            province={province}
            metodologie={tassonomie.metodologie}
            discipline={tassonomie.discipline}
            infrastrutture={tassonomie.infrastrutture}
            affiliazioni={tassonomie.affiliazioni}
            totalCount={results.length}
          />
        </Suspense>

        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-[color:var(--ds-gray-500)] font-mono">
            {mapMarkers.length} {mapMarkers.length === 1 ? "centro" : "centri"} sulla mappa
          </p>
        </div>

        <div className="mt-4 rounded-lg overflow-hidden border border-[color:var(--ds-gray-100)]" style={{ height: "calc(100vh - 360px)", minHeight: "500px" }}>
          <MapViewWrapper markers={mapMarkers} />
        </div>
      </section>
    </>
  );
}
