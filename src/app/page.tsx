import { Suspense } from "react";
import { searchCentri, getTassonomieForFilters, getProvinceByRegione } from "@/lib/centri";
import { FiltersBar } from "@/components/FiltersBar";
import { ResultsGrid } from "@/components/ResultsGrid";
import { ActiveFiltersBar } from "@/components/ActiveFiltersBar";
import { Pagination } from "@/components/Pagination";
import { MethodologyGuide } from "@/components/MethodologyGuide";

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
    page?: string;
  }>;
}

function toArray(v: string | string[] | undefined): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

const PAGE_SIZE = 15;

function hasActiveFilters(sp: Record<string, any>): boolean {
  return !!(
    sp.q ||
    sp.regione ||
    sp.provincia ||
    toArray(sp.metodologia).length > 0 ||
    toArray(sp.disciplina).length > 0 ||
    toArray(sp.infrastruttura).length > 0 ||
    toArray(sp.affiliazione).length > 0
  );
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const sp = await searchParams;
  const isFiltered = hasActiveFilters(sp);

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
  const page = Math.max(1, parseInt(sp.page || "1", 10) || 1);

  const [tassonomie, province, allResults] = await Promise.all([
    getTassonomieForFilters(),
    sp.regione ? getProvinceByRegione(sp.regione) : Promise.resolve([]),
    isFiltered ? searchCentri(filters) : Promise.resolve([]),
  ]);

  const totalPages = Math.max(1, Math.ceil(allResults.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const results = allResults.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  return (
    <>
      {/* Hero */}
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
                {allResults.length || 0}
              </span>{" "}
              centri
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">{tassonomie.regioni.length}</span>{" "}
              regioni
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">{tassonomie.metodologie.length}</span>{" "}
              metodologie
            </div>
            <div className="h-3 w-px bg-[color:var(--ds-gray-200)]" />
            <div>
              <span className="text-[color:var(--ds-gray-900)] font-semibold text-base">{tassonomie.affiliazioni.length}</span>{" "}
              federazioni
            </div>
          </div>
        </div>
      </section>

      {/* Horizontal filter bar */}
      <section className="mx-auto max-w-7xl px-6 py-10">
        <Suspense fallback={<div className="card-flat p-4 h-12 animate-pulse mb-6" />}>
          <FiltersBar
            regioni={tassonomie.regioni}
            province={province}
            metodologie={tassonomie.metodologie}
            discipline={tassonomie.discipline}
            infrastrutture={tassonomie.infrastrutture}
            affiliazioni={tassonomie.affiliazioni}
            totalCount={allResults.length}
          />
        </Suspense>

        {/* Active filters chips */}
        <Suspense fallback={null}>
          <div className="mt-3 mb-4">
            <ActiveFiltersBar filters={filters} tassonomie={tassonomie} />
          </div>
        </Suspense>

        {isFiltered ? (
          /* When filters are active: show results */
          <>
            <div className="flex items-center justify-between mb-5 mt-5">
              <div>
                <h2 className="text-h2">
                  {allResults.length}{" "}
                  <span className="text-[color:var(--ds-gray-500)] font-normal">
                    {allResults.length === 1 ? "centro" : "centri"}
                  </span>
                </h2>
                <p className="text-xs text-[color:var(--ds-gray-500)] mt-1 font-mono">
                  {totalPages > 1
                    ? `pagina ${safePage} di ${totalPages} — recordset aggiornato in tempo reale`
                    : "recordset aggiornato in tempo reale"}
                </p>
              </div>
            </div>

            <ResultsGrid centri={results} />

            <Suspense fallback={null}>
              <Pagination
                totalItems={allResults.length}
                pageSize={PAGE_SIZE}
                currentPage={safePage}
              />
            </Suspense>
          </>
        ) : (
          /* When no filters: show methodology guide */
          <MethodologyGuide />
        )}
      </section>
    </>
  );
}
