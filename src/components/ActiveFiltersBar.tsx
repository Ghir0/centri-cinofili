"use client";

import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";

export interface ActiveFilter {
  key: string;
  slug: string;
  label: string;
}

export interface ActiveFiltersBarProps {
  filters: {
    q?: string;
    regione?: string;
    provincia?: string;
    metodologie: string[];
    discipline: string[];
    infrastrutture: string[];
    affiliazioni: string[];
  };
  tassonomie: {
    regioni: { id: number; nome: string; slug: string }[];
    metodologie: { id: number; nome: string; slug: string }[];
    discipline: { id: number; nome: string; slug: string }[];
    infrastrutture: { id: number; nome: string; slug: string }[];
    affiliazioni: { id: number; nome: string; slug: string }[];
  };
}

/**
 * ActiveFiltersBar — chips dei filtri attivi, cliccabili per rimuoverli.
 * Sotto la testata risultati.
 */
export function ActiveFiltersBar({ filters, tassonomie }: ActiveFiltersBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const remove = (key: string, slug?: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (key === "q") {
      params.delete("q");
    } else if (key === "regione") {
      params.delete("regione");
      params.delete("provincia");
    } else if (key === "provincia") {
      params.delete("provincia");
    } else if (slug) {
      const remaining = params.getAll(key).filter((s) => s !== slug);
      params.delete(key);
      for (const s of remaining) params.append(key, s);
    }
    router.replace(params.toString() ? `${pathname}?${params.toString()}` : pathname, {
      scroll: false,
    });
  };

  const chips: { key: string; slug?: string; label: string }[] = [];

  if (filters.q) {
    chips.push({ key: "q", label: `“${filters.q}”` });
  }

  if (filters.regione) {
    const r = tassonomie.regioni.find((x) => x.slug === filters.regione);
    chips.push({ key: "regione", slug: filters.regione, label: r?.nome || filters.regione });
  }

  if (filters.provincia) {
    chips.push({ key: "provincia", slug: filters.provincia, label: filters.provincia });
  }

  for (const slug of filters.metodologie) {
    const m = tassonomie.metodologie.find((x) => x.slug === slug);
    chips.push({ key: "metodologia", slug, label: m?.nome || slug });
  }
  for (const slug of filters.discipline) {
    const d = tassonomie.discipline.find((x) => x.slug === slug);
    chips.push({ key: "disciplina", slug, label: d?.nome || slug });
  }
  for (const slug of filters.infrastrutture) {
    const i = tassonomie.infrastrutture.find((x) => x.slug === slug);
    chips.push({ key: "infrastruttura", slug, label: i?.nome || slug });
  }
  for (const slug of filters.affiliazioni) {
    const a = tassonomie.affiliazioni.find((x) => x.slug === slug);
    chips.push({ key: "affiliazione", slug, label: a?.nome || slug });
  }

  if (chips.length === 0) return null;

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <span className="text-eyebrow mr-1">Filtri attivi</span>
      {chips.map((chip, idx) => (
        <button
          key={`${chip.key}-${chip.slug || chip.label}-${idx}`}
          type="button"
          onClick={() => remove(chip.key, chip.slug)}
          className="pill hover:bg-[color:var(--ds-gray-50)] transition-colors group"
        >
          <span>{chip.label}</span>
          <span
            aria-hidden
            className="text-[color:var(--ds-gray-400)] group-hover:text-[color:var(--ds-gray-900)] ml-0.5"
          >
            ×
          </span>
        </button>
      ))}
    </div>
  );
}