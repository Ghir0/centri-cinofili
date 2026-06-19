"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";
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
 * Barra orizzontale compatta — trigger search modal + contatore + azzera filtri.
 */
export function FiltersBar(props: FiltersBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialOpen = searchParams.get("search") === "1";

  const hasFilters =
    !!searchParams.get("q") ||
    !!searchParams.get("regione") ||
    ["metodologia", "disciplina", "infrastruttura", "affiliazione"].some((k) =>
      searchParams.getAll(k).length > 0
    );

  const reset = useCallback(() => {
    router.push(pathname, { scroll: false });
  }, [router, pathname]);

  return (
    <div className="card-flat p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SearchModal {...props} initialOpen={initialOpen} />

        {hasFilters && (
          <button
            type="button"
            onClick={reset}
            className="btn-secondary text-xs h-9 px-3 bg-[color:var(--ds-gray-900)] text-white hover:bg-[color:var(--ds-gray-700)] border-0"
          >
            Azzera filtri
          </button>
        )}

        <span className="text-xs font-mono text-[color:var(--ds-gray-500)] ml-auto whitespace-nowrap">
          {props.totalCount} {props.totalCount === 1 ? "risultato" : "risultati"}
        </span>
      </div>
    </div>
  );
}
