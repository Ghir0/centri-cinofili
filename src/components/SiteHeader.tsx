import Link from "next/link";

/**
 * SiteHeader — top-level navigation, sticky, white background, subtle border.
 * Logo + nav Cerca/Directory + CTA "Inserisci centro".
 */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70 border-b border-[color:var(--ds-gray-100)]">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <span
            aria-hidden
            className="grid place-items-center h-7 w-7 rounded-md bg-[color:var(--ds-gray-900)] text-white font-mono text-[13px] font-semibold tracking-tight transition-transform group-hover:scale-105"
          >
            ◎
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
            href="/centri-cinofili/"
            className="text-[color:var(--ds-gray-600)] hover:text-[color:var(--ds-gray-900)] transition-colors"
          >
            Directory
          </Link>
        </nav>

        <Link href="/inserisci" className="btn-primary">
          <span aria-hidden className="text-base leading-none">
            +
          </span>
          <span className="hidden sm:inline">Inserisci centro</span>
          <span className="sm:hidden">Inserisci</span>
        </Link>
      </div>
    </header>
  );
}