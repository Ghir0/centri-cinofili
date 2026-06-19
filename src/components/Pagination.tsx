"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";

export interface PaginationProps {
  totalItems: number;
  pageSize: number;
  currentPage: number;
}

/**
 * Pagination — compact, Vercel-like.
 * Shows page buttons with ellipsis for large page counts.
 */
export function Pagination({ totalItems, pageSize, currentPage }: PaginationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  const goTo = useCallback(
    (page: number) => {
      const params = new URLSearchParams(searchParams.toString());
      if (page <= 1) {
        params.delete("page");
      } else {
        params.set("page", String(page));
      }
      const qs = params.toString();
      router.push(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [router, pathname, searchParams]
  );

  if (totalPages <= 1) return null;

  // Build page numbers with ellipsis
  const pages: (number | "ellipsis")[] = [];
  const maxVisible = 5;

  if (totalPages <= maxVisible + 2) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (currentPage > 3) pages.push("ellipsis");

    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    for (let i = start; i <= end; i++) pages.push(i);

    if (currentPage < totalPages - 2) pages.push("ellipsis");
    pages.push(totalPages);
  }

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <nav
      aria-label="Navigazione tra le pagine"
      className="flex items-center justify-between pt-6 mt-6 border-t border-[color:var(--ds-gray-100)]"
    >
      <div className="text-xs text-[color:var(--ds-gray-500)] font-mono">
        {startItem}–{endItem} di {totalItems} centri
      </div>

      <div className="flex items-center gap-1">
        {/* Prev */}
        <button
          type="button"
          onClick={() => goTo(currentPage - 1)}
          disabled={currentPage <= 1}
          className="btn-secondary text-xs h-8 w-8 p-0 grid place-items-center disabled:opacity-30 disabled:cursor-default"
          aria-label="Pagina precedente"
        >
          ‹
        </button>

        {pages.map((p, i) => {
          if (p === "ellipsis") {
            return (
              <span
                key={`ellipsis-${i}`}
                className="h-8 w-8 grid place-items-center text-xs text-[color:var(--ds-gray-400)] select-none"
              >
                …
              </span>
            );
          }
          return (
            <button
              key={p}
              type="button"
              onClick={() => goTo(p)}
              className={`h-8 min-w-[2rem] px-1.5 grid place-items-center text-xs rounded-md transition-colors ${
                p === currentPage
                  ? "bg-[color:var(--ds-gray-900)] text-white font-medium"
                  : "hover:bg-[color:var(--ds-gray-100)] text-[color:var(--ds-gray-600)]"
              }`}
              aria-current={p === currentPage ? "page" : undefined}
            >
              {p}
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => goTo(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="btn-secondary text-xs h-8 w-8 p-0 grid place-items-center disabled:opacity-30 disabled:cursor-default"
          aria-label="Pagina successiva"
        >
          ›
        </button>
      </div>
    </nav>
  );
}
