"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useMemo, useState, useTransition, useRef, useEffect } from "react";
import { SearchModal } from "@/components/SearchModal";

export interface FilterOption {
  id: number;
  nome: string;
  slug: string;
}

export interface ProvinciaOption extends FilterOption {
  sigla?: string;
}

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
 * Barra orizzontale dei filtri — compatto, si adatta al layout sopra i risultati.
 */
export function FiltersBar({
  regioni,
  province,
  metodologie,
  discipline,
  infrastrutture,
  affiliazioni,
  totalCount,
}: FiltersBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const selectedRegione = searchParams.get("regione") || "";
  const selectedProvincia = searchParams.get("provincia") || "";
  const query = searchParams.get("q") || "";

  const isOn = (key: string, slug: string) => {
    return searchParams.getAll(key).includes(slug);
  };

  const countSelected = (key: string) => searchParams.getAll(key).length;

  const buildNewParams = useCallback(
    (mutator: (params: URLSearchParams) => void) => {
      const params = new URLSearchParams(searchParams.toString());
      mutator(params);
      return params.toString();
    },
    [searchParams]
  );

  const apply = useCallback(
    (queryString: string) => {
      startTransition(() => {
        router.replace(queryString ? `${pathname}?${queryString}` : pathname, { scroll: false });
      });
    },
    [router, pathname]
  );

  const toggleMulti = (key: string, slug: string) => {
    const qs = buildNewParams((params) => {
      const current = params.getAll(key);
      params.delete(key);
      const next = current.includes(slug)
        ? current.filter((s) => s !== slug)
        : [...current, slug];
      for (const s of next) params.append(key, s);
    });
    apply(qs);
  };

  const setRegione = (slug: string) => {
    const qs = buildNewParams((params) => {
      if (slug) {
        params.set("regione", slug);
      } else {
        params.delete("regione");
      }
      params.delete("provincia");
    });
    apply(qs);
  };

  const setProvincia = (slug: string) => {
    const qs = buildNewParams((params) => {
      if (slug) {
        params.set("provincia", slug);
      } else {
        params.delete("provincia");
      }
    });
    apply(qs);
  };

  const setSort = (sort: string) => {
    const qs = buildNewParams((params) => {
      if (sort && sort !== "name") {
        params.set("sort", sort);
      } else {
        params.delete("sort");
      }
    });
    apply(qs);
  };

  const reset = () => {
    apply("");
  };

  const hasFilters =
    !!query ||
    !!searchParams.get("regione") ||
    !!searchParams.get("provincia") ||
    ["metodologia", "disciplina", "infrastruttura", "affiliazione"].some((k) =>
      searchParams.getAll(k).length > 0
    );

  const currentSort = searchParams.get("sort") || "name";

  return (
    <div className="card-flat p-4 pb-3">
      {/* Top row: filter controls */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search — modal on click */}
        <SearchModal defaultQuery={query} />

        {/* Regione */}
        <select
          className="select text-sm h-9 min-w-[120px]"
          value={selectedRegione}
          onChange={(e) => setRegione(e.target.value)}
        >
          <option value="">Tutte le regioni</option>
          {regioni.map((r) => (
            <option key={r.id} value={r.slug}>{r.nome}</option>
          ))}
        </select>

        {/* Provincia */}
        {selectedRegione && province.length > 0 && (
          <select
            className="select text-sm h-9 min-w-[120px]"
            value={selectedProvincia}
            onChange={(e) => setProvincia(e.target.value)}
          >
            <option value="">Tutte le province</option>
            {province.map((p) => (
              <option key={p.id} value={p.slug}>{p.nome} ({p.sigla})</option>
            ))}
          </select>
        )}

        {/* Multi-select popovers */}
        <MultiSelectDropdown
          label="Metodologia"
          options={metodologie}
          selected={(slug) => isOn("metodologia", slug)}
          onToggle={(slug) => toggleMulti("metodologia", slug)}
          count={countSelected("metodologia")}
          open={openDropdown === "metodologia"}
          onOpen={() => setOpenDropdown(openDropdown === "metodologia" ? null : "metodologia")}
        />

        <MultiSelectDropdown
          label="Attività"
          options={discipline}
          selected={(slug) => isOn("disciplina", slug)}
          onToggle={(slug) => toggleMulti("disciplina", slug)}
          count={countSelected("disciplina")}
          open={openDropdown === "discipline"}
          onOpen={() => setOpenDropdown(openDropdown === "discipline" ? null : "discipline")}
        />

        <MultiSelectDropdown
          label="Strutture"
          options={infrastrutture}
          selected={(slug) => isOn("infrastruttura", slug)}
          onToggle={(slug) => toggleMulti("infrastruttura", slug)}
          count={countSelected("infrastruttura")}
          open={openDropdown === "infrastrutture"}
          onOpen={() => setOpenDropdown(openDropdown === "infrastrutture" ? null : "infrastrutture")}
        />

        <MultiSelectDropdown
          label="Affiliazioni"
          options={affiliazioni}
          selected={(slug) => isOn("affiliazione", slug)}
          onToggle={(slug) => toggleMulti("affiliazione", slug)}
          count={countSelected("affiliazione")}
          open={openDropdown === "affiliazioni"}
          onOpen={() => setOpenDropdown(openDropdown === "affiliazioni" ? null : "affiliazioni")}
        />

        {/* Sort */}
        <select
          className="select text-sm h-9 min-w-[100px]"
          value={currentSort}
          onChange={(e) => setSort(e.target.value)}
        >
          <option value="name">A-Z</option>
          <option value="rating">Rating</option>
          <option value="recent">Recenti</option>
        </select>

        {/* Reset */}
        {hasFilters && (
          <button
            type="button"
            onClick={reset}
            disabled={isPending}
            className="btn-secondary text-xs h-9 px-3 whitespace-nowrap"
          >
            {isPending ? "…" : "✕ Azzera"}
          </button>
        )}

        {/* Results count */}
        <span className="text-xs font-mono text-[color:var(--ds-gray-500)] ml-auto whitespace-nowrap">
          {totalCount} {totalCount === 1 ? "risultato" : "risultati"}
        </span>
      </div>
    </div>
  );
}

/** Dropdown comprimibile per filtri multi-selezione. */
function MultiSelectDropdown({
  label,
  options,
  selected,
  onToggle,
  count,
  open,
  onOpen,
}: {
  label: string;
  options: FilterOption[];
  selected: (slug: string) => boolean;
  onToggle: (slug: string) => void;
  count: number;
  open: boolean;
  onOpen: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null!);

  useEffect(() => {
    if (!open) return;
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onOpen(); // close
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, onOpen]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={onOpen}
        className={`btn-secondary text-xs h-9 px-3 whitespace-nowrap flex items-center gap-1.5 ${
          count > 0 ? "border-[color:var(--ds-verified)]" : ""
        }`}
      >
        <span>{label}</span>
        {count > 0 && (
          <span className="inline-flex items-center justify-center h-4 min-w-4 px-1 text-[10px] font-semibold rounded-full bg-[color:var(--ds-verified)] text-white">
            {count}
          </span>
        )}
        <span aria-hidden className="text-[10px] text-[color:var(--ds-gray-400)]">
          {open ? "▲" : "▼"}
        </span>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 card shadow-lg p-3 min-w-[200px] max-h-56 overflow-y-auto">
          <div className="flex flex-col gap-1">
            {options.map((opt) => (
              <label
                key={opt.id}
                className="flex items-center gap-2 text-sm cursor-pointer hover:text-[color:var(--ds-gray-900)] text-[color:var(--ds-gray-600)] px-1 py-0.5 rounded hover:bg-[color:var(--ds-gray-50)]"
              >
                <input
                  type="checkbox"
                  checked={selected(opt.slug)}
                  onChange={() => onToggle(opt.slug)}
                />
                <span className="select-none">{opt.nome}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
