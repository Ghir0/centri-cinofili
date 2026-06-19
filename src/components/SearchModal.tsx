'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useState, useEffect, useRef, useCallback, type FormEvent } from 'react';

export interface FilterOption {
  id: number;
  nome: string;
  slug: string;
}

export interface ProvinciaOption extends FilterOption {
  sigla?: string;
}

export interface SearchModalProps {
  regioni: FilterOption[];
  province: ProvinciaOption[];
  metodologie: FilterOption[];
  discipline: FilterOption[];
  infrastrutture: FilterOption[];
  affiliazioni: FilterOption[];
  totalCount: number;
  /** Se true, il modal parte aperto */
  initialOpen?: boolean;
}

/**
 * SearchModal — overlay a tutto schermo con:
 * - Barra di ricerca grande
 * - Tutti i filtri (regione, provincia, metodologia, attività, strutture, affiliazioni)
 * - Ordinamento
 * - Animazione scale + fade
 */
export function SearchModal({
  regioni,
  province,
  metodologie,
  discipline,
  infrastrutture,
  affiliazioni,
  totalCount,
  initialOpen = false,
}: SearchModalProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(initialOpen);
  const [animating, setAnimating] = useState(false);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync initialOpen
  useEffect(() => { setOpen(initialOpen); }, [initialOpen]);

  // Sync query from URL
  useEffect(() => {
    setQuery(searchParams.get('q') || '');
  }, [searchParams]);

  // Focus input when opening
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  // Prevent body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const openModal = useCallback(() => {
    setAnimating(true);
    setOpen(true);
  }, []);

  // Close modal without touching URL (used from submit/filter clicks)
  const closeModal = useCallback(() => {
    setAnimating(false);
    setTimeout(() => setOpen(false), 200);
  }, []);

  const close = useCallback(() => {
    closeModal();
  }, [closeModal]);

  // ---- Filter logic (same as FiltersBar) ----
  const selectedRegione = searchParams.get('regione') || '';
  const selectedProvincia = searchParams.get('provincia') || '';

  const isOn = (key: string, slug: string) => searchParams.getAll(key).includes(slug);
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
      router.replace(queryString ? `${pathname}?${queryString}` : pathname, { scroll: false });
    },
    [router, pathname]
  );

  const toggleMulti = (key: string, slug: string) => {
    const qs = buildNewParams((params) => {
      const current = params.getAll(key);
      params.delete(key);
      const next = current.includes(slug) ? current.filter((s) => s !== slug) : [...current, slug];
      for (const s of next) params.append(key, s);
    });
    apply(qs);
  };

  const setRegione = (slug: string) => {
    const qs = buildNewParams((params) => {
      if (slug) { params.set('regione', slug); } else { params.delete('regione'); }
      params.delete('provincia');
    });
    apply(qs);
  };

  const setProvincia = (slug: string) => {
    const qs = buildNewParams((params) => {
      if (slug) { params.set('provincia', slug); } else { params.delete('provincia'); }
    });
    apply(qs);
  };

  const setSort = (sort: string) => {
    const qs = buildNewParams((params) => {
      if (sort && sort !== 'name') { params.set('sort', sort); } else { params.delete('sort'); }
    });
    apply(qs);
  };

  const reset = () => apply('');

  const submit = useCallback((e: FormEvent) => {
    e.preventDefault();
    const qs = buildNewParams((params) => {
      params.delete('page');
      params.delete('search'); // evita che il modal si riapra dopo submit
      if (query.trim()) { params.set('q', query.trim()); } else { params.delete('q'); }
    });
    apply(qs);
    closeModal();
  }, [query, buildNewParams, apply, closeModal]);

  const hasFilters = !!searchParams.get('q') || !!selectedRegione ||
    ['metodologia', 'disciplina', 'infrastruttura', 'affiliazione'].some(k => searchParams.getAll(k).length > 0);
  const currentSort = searchParams.get('sort') || 'name';

  return (
    <>
      {/* Compact trigger */}
      <button
        type="button"
        onClick={openModal}
        className="flex-1 min-w-[200px] input text-sm h-9 text-left text-[color:var(--ds-gray-400)] cursor-text hover:border-[color:var(--ds-gray-400)] transition-colors"
      >
        {query ? (
          <span className="text-[color:var(--ds-gray-900)]">{query}</span>
        ) : (
          'Cerca centro o comune…'
        )}
      </button>

      {/* Modal overlay */}
      {open && (
        <div
          className={`fixed inset-0 z-[9998] flex items-start justify-center pt-[10vh] ${
            animating ? 'opacity-100' : 'opacity-0'
          } transition-opacity duration-200`}
          onClick={close}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

          {/* Modal card */}
          <div
            className={`relative z-10 w-full max-w-3xl mx-4 bg-white rounded-2xl shadow-2xl border border-[color:var(--ds-gray-100)] overflow-hidden ${
              animating ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
            } transition-all duration-300 ease-out max-h-[85vh] flex flex-col`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header — search bar */}
            <div className="p-6 pb-4 shrink-0">
              <form onSubmit={submit}>
                <div className="relative">
                  <input
                    ref={inputRef}
                    type="search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Cerca centro cinofilo o comune…"
                    className="w-full text-xl font-medium bg-transparent border-0 border-b-2 border-[color:var(--ds-gray-200)] pb-3 pr-12 outline-none focus:border-[color:var(--ds-gray-900)] transition-colors placeholder:text-[color:var(--ds-gray-400)]"
                  />
                  <button
                    type="submit"
                    className="absolute right-0 top-0 h-full px-2 text-[color:var(--ds-gray-500)] hover:text-[color:var(--ds-gray-900)] transition-colors"
                    aria-label="Cerca"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                  </button>
                </div>
              </form>
            </div>

            {/* Filters — scrollable */}
            <div className="px-6 pb-6 overflow-y-auto flex-1 space-y-5">
              {/* Row: Regione + Provincia */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-1.5">Regione</label>
                  <select
                    className="w-full input text-sm h-9"
                    value={selectedRegione}
                    onChange={(e) => setRegione(e.target.value)}
                  >
                    <option value="">Tutte le regioni</option>
                    {regioni.map((r) => (
                      <option key={r.id} value={r.slug}>{r.nome}</option>
                    ))}
                  </select>
                </div>
                <div className={!selectedRegione ? 'opacity-40 pointer-events-none' : ''}>
                  <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-1.5">Provincia</label>
                  <select
                    className="w-full input text-sm h-9"
                    value={selectedProvincia}
                    onChange={(e) => setProvincia(e.target.value)}
                    disabled={!selectedRegione}
                  >
                    <option value="">
                      {selectedRegione ? 'Tutte le province' : 'Seleziona una regione'}
                    </option>
                    {province.map((p) => (
                      <option key={p.id} value={p.slug}>{p.nome} ({p.sigla})</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Multi-selects */}
              <div>
                <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-2">Metodologia</label>
                <div className="flex flex-wrap gap-1.5">
                  {metodologie.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => toggleMulti('metodologia', m.slug)}
                      className={`pill text-xs ${isOn('metodologia', m.slug) ? 'pill-method' : 'pill-unclaimed'}`}
                    >
                      {m.nome}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-2">Attività</label>
                <div className="flex flex-wrap gap-1.5">
                  {discipline.map((d) => (
                    <button
                      key={d.id}
                      type="button"
                      onClick={() => toggleMulti('disciplina', d.slug)}
                      className={`pill text-xs ${isOn('disciplina', d.slug) ? 'pill-discipline' : 'pill-unclaimed'}`}
                    >
                      {d.nome}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-2">Strutture</label>
                <div className="flex flex-wrap gap-1.5">
                  {infrastrutture.map((i) => (
                    <button
                      key={i.id}
                      type="button"
                      onClick={() => toggleMulti('infrastruttura', i.slug)}
                      className={`pill text-xs ${isOn('infrastruttura', i.slug) ? 'pill-infra' : 'pill-unclaimed'}`}
                    >
                      {i.nome}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[color:var(--ds-gray-500)] mb-2">Affiliazioni</label>
                <div className="flex flex-wrap gap-1.5">
                  {affiliazioni.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => toggleMulti('affiliazione', a.slug)}
                      className={`pill text-xs ${isOn('affiliazione', a.slug) ? 'pill-affil' : 'pill-unclaimed'}`}
                    >
                      {a.nome}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort + Reset + Count */}
              <div className="flex items-center justify-between pt-3 border-t border-[color:var(--ds-gray-100)]">
                <div className="flex items-center gap-2">
                  <label className="text-xs font-medium text-[color:var(--ds-gray-500)]">Ordina:</label>
                  <select
                    className="input text-xs h-8"
                    value={currentSort}
                    onChange={(e) => setSort(e.target.value)}
                  >
                    <option value="name">A-Z</option>
                    <option value="rating">Rating</option>
                    <option value="recent">Recenti</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  {hasFilters && (
                    <button type="button" onClick={reset} className="btn-secondary text-xs h-8 px-3">
                      ✕ Azzera filtri
                    </button>
                  )}
                  <span className="text-xs font-mono text-[color:var(--ds-gray-500)]">
                    {totalCount} risultati
                  </span>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-[color:var(--ds-gray-50)] border-t border-[color:var(--ds-gray-100)] shrink-0">
              <div className="flex items-center justify-between text-xs text-[color:var(--ds-gray-400)]">
                <span>Premi <kbd className="px-1 py-0.5 bg-white rounded border border-[color:var(--ds-gray-200)] text-[10px]">Enter</kbd> per cercare</span>
                <span><kbd className="px-1 py-0.5 bg-white rounded border border-[color:var(--ds-gray-200)] text-[10px]">Esc</kbd> per chiudere</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

