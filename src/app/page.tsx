import { Suspense } from "react";
import { searchCentri, getTassonomieForFilters, getProvinceByRegione } from "@/lib/centri";
import { FiltersSidebar } from "@/components/FiltersSidebar";
import { ResultsGrid } from "@/components/ResultsGrid";
import { ActiveFiltersBar } from "@/components/ActiveFiltersBar";
import { SortSelector } from "@/components/SortSelector";

// Force dynamic rendering because we read searchParams
export const dynamic = "force-dynamic";

interface HomePageProps {
  searchParams: Promise<{
    q?: string;
    regione?: string;
    provincia?: string;
    metodologia?: string | string[];
    disciplina?: string | string[];
    infrastruttura?: string | string[];
    affiliazione?: string | string[];
    sort?: "recent" | "name" | "rating";
  }>;
}

function toArray(v: string | string[] | undefined): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const sp = await searchParams;

  const filters = {
    q: sp.q,
    regione: sp.regione,
    provincia: sp.provincia,
    metodologie: toArray(sp.metodologia),
    discipline: toArray(sp.disciplina),
    infrastrutture: toArray(sp.infrastruttura),
    affiliazioni: toArray(sp.affiliazione),
    sort: sp.sort,
  };

  const [tassonomie, province, results] = await Promise.all([
    getTassonomieForFilters(),
    sp.regione ? getProvinceByRegione(sp.regione) : Promise.resolve([]),
    searchCentri(filters),
  ]);

  return (
    <>
      {/* Hero — minimal, monoline, branded */}
      <section className="border-b border-[color:var(--ds-gray-100)] bg-white">
        <div className="mx-auto max-w-7xl px-6 pt-14 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]" />
            <span className="text-eyebrow">Anagrafe Nazionale · v0.1</span>
          </div>
          <h1 className="text-display max-w-3xl">
            Per una cinofilia raggiungibile e trasparente.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[color:var(--ds-gray-600)]">
            Registro aperto dei centri cinofili italiani. Clicca su un centro per consultare
            dettagli descrittivi e metodi educativi certificati.
          </p>
          <div className="mt-7 flex items-center gap-6 text-xs font-mono text-[color:var(--ds-gray-500)]">
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">
                {results.length > 0 ? `${results.length}+` : "10"}
              </span>{" "}
              centri
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">20</span>{" "}
              regioni
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">4</span>{" "}
              metodologie
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">7</span>{" "}
              federazioni
            </div>
          </div>
        </div>
      </section>

      {/* Layout: sidebar filtri (sinistra) + risultati (destra) */}
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
          {/* Sidebar */}
          <Suspense fallback={<div className="card-flat p-5 h-96 animate-pulse" />}>
            <FiltersSidebar
              regioni={tassonomie.regioni}
              province={province}
              metodologie={tassonomie.metodologie}
              discipline={tassonomie.discipline}
              infrastrutture={tassonomie.infrastrutture}
              affiliazioni={tassonomie.affiliazioni}
              totalCount={results.length}
            />
          </Suspense>

          {/* Results */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-h2">
                  {results.length}{" "}
                  <span className="text-[color:var(--ds-gray-500)] font-normal">
                    {results.length === 1 ? "centro" : "centri"}
                  </span>
                </h2>
                <p className="text-xs text-[color:var(--ds-gray-500)] mt-1 font-mono">
                  recordset aggiornato in tempo reale
                </p>
              </div>

              {/* Sort selector — client-side URL update */}
              <SortSelectorServer currentSort={sp.sort || "name"} />
            </div>

            {/* Active filters chips */}
            <Suspense fallback={null}>
              <ActiveFiltersBar filters={filters} tassonomie={tassonomie} />
            </Suspense>

            <ResultsGrid centri={results} />
          </div>
        </div>
      </section>
    </>
  );
}

function SortSelectorServer({ currentSort }: { currentSort: string }) {
  // Wrapped because SortSelector is a client component
  return <SortSelector currentSort={currentSort} />;
}