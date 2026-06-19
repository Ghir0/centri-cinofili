"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Barra di navigazione fissa in basso — visibile solo su mobile (max-md). */
export function MobileNav() {
  const pathname = usePathname();
  const isMappa = pathname === "/mappa";

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-[1100] md:hidden bg-white border-t border-[color:var(--ds-gray-100)]">
      <div className="flex items-center justify-around h-14 px-2">
        <Link
          href="/"
          className={`flex flex-col items-center justify-center gap-0.5 flex-1 h-full transition-colors ${
            !isMappa ? "text-[color:var(--ds-gray-900)]" : "text-[color:var(--ds-gray-400)]"
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <span className="text-[10px] font-medium">Cerca</span>
        </Link>

        <Link
          href="/mappa"
          className={`flex flex-col items-center justify-center gap-0.5 flex-1 h-full transition-colors ${
            isMappa ? "text-[color:var(--ds-gray-900)]" : "text-[color:var(--ds-gray-400)]"
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          <span className="text-[10px] font-medium">Mappa</span>
        </Link>
      </div>
    </nav>
  );
}
