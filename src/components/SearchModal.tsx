'use client';

import { useState, useEffect, useRef, useCallback, type FormEvent } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';

export interface SearchModalProps {
  children?: React.ReactNode;
  defaultQuery?: string;
}

/**
 * SearchModal — al click sulla search bar, espande in overlay animato.
 * L'animazione usa scale + opacity per un effetto morbido.
 */
export function SearchModal({ children, defaultQuery }: SearchModalProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(defaultQuery || '');
  const [animating, setAnimating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync query when default changes
  useEffect(() => {
    if (defaultQuery) setQuery(defaultQuery);
  }, [defaultQuery]);

  // Focus input when opening
  useEffect(() => {
    if (open && inputRef.current) {
      // Small delay for animation to start
      setTimeout(() => inputRef.current?.focus(), 100);
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

  // Prevent body scroll when open
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

  const close = useCallback(() => {
    setAnimating(false);
    setTimeout(() => setOpen(false), 200);
  }, []);

  const submit = useCallback((e: FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    if (query.trim()) {
      params.set('q', query.trim());
    } else {
      params.delete('q');
    }
    params.delete('page');
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    close();
  }, [query, router, pathname, searchParams]);

  return (
    <>
      {/* Compact trigger — shown inside the filters bar */}
      <div ref={containerRef} className="flex-1 min-w-[200px]">
        <button
          type="button"
          onClick={openModal}
          className="w-full input text-sm h-9 text-left text-[color:var(--ds-gray-400)] cursor-text hover:border-[color:var(--ds-gray-400)] transition-colors"
        >
          {query || defaultQuery ? (
            <span className="text-[color:var(--ds-gray-900)]">
              {query || defaultQuery}
            </span>
          ) : (
            'Cerca centro o comune…'
          )}
        </button>
      </div>

      {/* Modal overlay */}
      {open && (
        <div
          className={`fixed inset-0 z-50 flex items-start justify-center pt-[15vh] ${
            animating ? 'opacity-100' : 'opacity-0'
          } transition-opacity duration-200`}
          onClick={close}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

          {/* Modal card */}
          <div
            className={`relative z-10 w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl border border-[color:var(--ds-gray-100)] overflow-hidden ${
              animating ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
            } transition-all duration-300 ease-out`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search form */}
            <form onSubmit={submit} className="p-6">
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
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </button>
              </div>
            </form>

            {/* Extra content (e.g., filter chips, suggestions) */}
            {children && (
              <div className="px-6 pb-6 border-t border-[color:var(--ds-gray-100)] pt-4">
                {children}
              </div>
            )}

            {/* Footer hint */}
            <div className="px-6 py-3 bg-[color:var(--ds-gray-50)] border-t border-[color:var(--ds-gray-100)]">
              <div className="flex items-center justify-between text-xs text-[color:var(--ds-gray-400)]">
                <span>Premi <kbd className="px-1 py-0.5 bg-white rounded border border-[color:var(--ds-gray-200)] text-[10px]">Enter</kbd> per cercare</span>
                <span>
                  <kbd className="px-1 py-0.5 bg-white rounded border border-[color:var(--ds-gray-200)] text-[10px]">Esc</kbd> per chiudere
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
