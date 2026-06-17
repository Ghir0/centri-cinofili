"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useMemo, useState, useTransition } from "react";

export interface FilterOption {
  id: number;
  nome: string;
  slug: string;
}

export interface ProvinciaOption extends FilterOption {
  sigla?: string;
}

export interface FiltersSidebarProps {
  regioni: FilterOption[];
  province: ProvinciaOption[];
  metodologie: FilterOption[];
  discipline: FilterOption[];
  infrastrutture: FilterOption[];
  affiliazioni: FilterOption[];
  totalCount: number;
}

/**
 * Sidebar filtri recordset.
 * Stato sincronizzato con URL search params (SSR-friendly, condivisibile, indicizzabile).
 */
export function FiltersSidebar({
  regioni,
  province,
  metodologie,
  discipline,
  infrastrutture,
  affiliazioni,
  totalCount,
}: FiltersSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  // Local state for instant checkbox feedback; URL is the source of truth
  const [selectedRegione, setSelectedRegione] = useState(
    searchParams.get("regione") || ""
  );

  const selectedProvince = useMemo(
    () => province.filter((p) => searchParams.get("provincia") === p.slug),
    [province, searchParams]
  );

  const isOn = (key: string, slug: string) => {
    const vals = searchParams.getAll(key);
    return vals.includes(slug);
  };

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
    setSelectedRegione(slug);
    const qs = buildNewParams((params) => {
      if (slug) {
        params.set("regione", slug);
      } else {
        params.delete("regione");
      }
      // Reset provincia when region changes
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

  const reset = () => {
    setSelectedRegione("");
    apply("");
  };

  const query = searchParams.get("q") || "";

  const visibleProvince = selectedRegione
    ? province.filter((p) => {
        // province.filter prop accepts province already filtered by region from server
        return true;
      })
    : province;

  // Determine if any filter is active (for "reset" button visibility)
  const hasFilters =
    !!query ||
    !!searchParams.get("regione") ||
    !!searchParams.get("provincia") ||
    ["metodologia", "disciplina", "infrastruttura", "affiliazione"].some((k) =>
      searchParams.getAll(k).length > 0
    );

  return (
    <aside className="card-flat p-5 lg:sticky lg:top-20 self-start">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <span aria-hidden className="text-[color:var(--ds-verified)] font-mono">⌘</span>
          <h2 className="text-h3">Filtra recordset</h2>
        </div>
        <span className="text-xs font-mono text-[color:var(--ds-gray-500)]">
          {totalCount} {totalCount === 1 ? "risultato" : "risultati"}
        </span>
      </div>

      <hr className="divider mb-5" />

      {/* Text search */}
      <div className="mb-5">
        <label htmlFor="filter-q" className="text-eyebrow block mb-2">
          Cerca testo o comune
        </label>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const value = (e.currentTarget.elements.namedItem("q") as HTMLInputElement).value;
            const qs = buildNewParams((params) => {
              if (value) params.set("q", value);
              else params.delete("q");
            });
            apply(qs);
          }}
        >
          <input
            id="filter-q"
            name="q"
            type="search"
            placeholder="Es. Zampa, Roma, Firenze"
            defaultValue={query}
            className="input"
          />
        </form>
      </div>

      {/* Region */}
      <div className="mb-5">
        <label htmlFor="filter-regione" className="text-eyebrow block mb-2">
          Regione
        </label>
        <select
          id="filter-regione"
          className="select"
          value={selectedRegione}
          onChange={(e) => setRegione(e.target.value)}
        >
          <option value="">Tutte le regioni</option>
          {regioni.map((r) => (
            <option key={r.id} value={r.slug}>
              {r.nome}
            </option>
          ))}
        </select>
      </div>

      {/* Province (visible only if region selected, but server passes all) */}
      {selectedRegione && province.length > 0 && (
        <div className="mb-5">
          <label htmlFor="filter-provincia" className="text-eyebrow block mb-2">
            Provincia
          </label>
          <select
            id="filter-provincia"
            className="select"
            value={searchParams.get("provincia") || ""}
            onChange={(e) => setProvincia(e.target.value)}
          >
            <option value="">Tutte le province</option>
            {visibleProvince.map((p) => (
              <option key={p.id} value={p.slug}>
                {p.nome} ({p.sigla})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Methodology */}
      <CheckboxGroup
        label="Metodologia educativa"
        options={metodologie}
        selected={(slug) => isOn("metodologia", slug)}
        onToggle={(slug) => toggleMulti("metodologia", slug)}
        maxHeight="max-h-none"
      />

      {/* Discipline */}
      <CheckboxGroup
        label="Discipline e attività"
        options={discipline}
        selected={(slug) => isOn("disciplina", slug)}
        onToggle={(slug) => toggleMulti("disciplina", slug)}
        maxHeight="max-h-64 overflow-y-auto"
      />

      {/* Infrastrutture */}
      <CheckboxGroup
        label="Infrastrutture e comfort"
        options={infrastrutture}
        selected={(slug) => isOn("infrastruttura", slug)}
        onToggle={(slug) => toggleMulti("infrastruttura", slug)}
        maxHeight="max-h-none"
      />

      {/* Affiliazioni */}
      <CheckboxGroup
        label="Federazioni e affiliazioni"
        options={affiliazioni}
        selected={(slug) => isOn("affiliazione", slug)}
        onToggle={(slug) => toggleMulti("affiliazione", slug)}
        maxHeight="max-h-56 overflow-y-auto"
      />

      <hr className="divider my-5" />

      {/* Reset */}
      <button
        type="button"
        onClick={reset}
        disabled={!hasFilters || isPending}
        className="btn-secondary w-full disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isPending ? "Aggiornamento…" : "Azzera filtri"}
      </button>
    </aside>
  );
}

interface CheckboxGroupProps {
  label: string;
  options: FilterOption[];
  selected: (slug: string) => boolean;
  onToggle: (slug: string) => void;
  maxHeight?: string;
}

function CheckboxGroup({ label, options, selected, onToggle, maxHeight = "max-h-none" }: CheckboxGroupProps) {
  return (
    <div className="mb-5">
      <div className="text-eyebrow block mb-2">{label}</div>
      <div className={`flex flex-col gap-2 ${maxHeight} pr-1`}>
        {options.map((opt) => (
          <label
            key={opt.id}
            className="flex items-center gap-2.5 text-sm cursor-pointer hover:text-[color:var(--ds-gray-900)] text-[color:var(--ds-gray-600)]"
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
  );
}