"use client";

import { useSearchParams } from "next/navigation";
import { SearchModal, type FilterOption, type ProvinciaOption } from "@/components/SearchModal";

export type { FilterOption, ProvinciaOption } from "@/components/SearchModal";

export interface FiltersBarProps {
  regioni: FilterOption[];
  province: ProvinciaOption[];
  metodologie: FilterOption[];
  discipline: FilterOption[];
  infrastrutture: FilterOption[];
  affiliazioni: FilterOption[];
  totalCount: number;
}

/**
 * Barra orizzontale compatta — solo il trigger della search modal + contatore.
 * Tutti i filtri sono dentro il SearchModal.
 */
export function FiltersBar(props: FiltersBarProps) {
  const searchParams = useSearchParams();
  const initialOpen = searchParams.get("search") === "1";

  return (
    <div className="card-flat p-4">
      <div className="flex flex-wrap items-center gap-2">
        {/* Search modal trigger — cliccandolo apre l'overlay con tutti i filtri */}
        <SearchModal {...props} initialOpen={initialOpen} />

        {/* Results count */}
        <span className="text-xs font-mono text-[color:var(--ds-gray-500)] ml-auto whitespace-nowrap">
          {props.totalCount} {props.totalCount === 1 ? "risultato" : "risultati"}
        </span>
      </div>
    </div>
  );
}
