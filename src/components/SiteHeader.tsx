'use client';

import Link from "next/link";
import { useState } from "react";

export function SiteHeader() {
  const [showToast, setShowToast] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-[1100] bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70 border-b border-[color:var(--ds-gray-100)]">
        <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <span
              aria-hidden
              className="grid place-items-center h-7 w-7 rounded-md bg-[color:var(--ds-gray-900)] text-white font-mono text-[13px] font-semibold tracking-tight transition-transform group-hover:scale-105"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l6.59-6.59L19 9l-8 8z"/></svg>
            </span>
            <span className="text-[15px] font-semibold tracking-tight">
              Centri Cinofili{" "}
              <span className="text-[color:var(--ds-gray-500)] font-normal">
                Italia
              </span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-7 text-sm">
            <Link
              href="/"
              className="text-[color:var(--ds-gray-900)] font-medium hover:underline decoration-[color:var(--ds-gray-400)] underline-offset-4"
            >
              Cerca
            </Link>
            <Link
              href="/mappa"
              className="text-[color:var(--ds-gray-600)] hover:text-[color:var(--ds-gray-900)] hover:underline decoration-[color:var(--ds-gray-400)] underline-offset-4"
            >
              Mappa
            </Link>
          </nav>

          <button
            type="button"
            onClick={() => setShowToast(true)}
            className="btn-primary"
          >
            <span aria-hidden className="text-base leading-none">+</span>
            <span className="hidden sm:inline">Inserisci centro</span>
            <span className="sm:hidden">Inserisci</span>
          </button>
        </div>
      </header>

      {/* Toast — coming soon */}
      {showToast && (
        <div className="fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-50 mx-4 w-full max-w-sm">
          <div className="bg-[color:var(--ds-gray-900)] text-white rounded-xl shadow-2xl p-5 animate-in slide-in-from-bottom-4 duration-300">
            <p className="text-sm font-medium mb-3">
              L&apos;inserimento e la rivendicazione dei centri sono in arrivo.
            </p>
            <p className="text-xs text-[color:var(--ds-gray-400)] mb-3">
              Vuoi aggiornare o inserire il tuo centro? Scrivici:
            </p>
            <div className="flex items-center gap-2">
              <a
                href="mailto:m.tamanti@webemento.com"
                className="flex-1 text-center text-xs bg-white text-[color:var(--ds-gray-900)] rounded-lg py-2 font-medium hover:bg-[color:var(--ds-gray-100)] transition-colors"
              >
                m.tamanti@webemento.com
              </a>
              <button
                type="button"
                onClick={() => setShowToast(false)}
                className="text-[color:var(--ds-gray-400)] hover:text-white transition-colors text-lg leading-none px-1"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
