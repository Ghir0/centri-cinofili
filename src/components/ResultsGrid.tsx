import Link from "next/link";

export interface SearchResult {
  id: number;
  slug: string;
  ragione_sociale: string;
  brand_name: string | null;
  indirizzo: string | null;
  comune: string | null;
  cap: string | null;
  provincia_sigla: string | null;
  provincia_nome: string | null;
  regione_nome: string | null;
  regione_slug: string | null;
  claimed: boolean;
  rating_medio: number | null;
  num_recensioni: number;
  metodologie: { nome: string; slug: string }[];
  discipline: { nome: string; slug: string }[];
  infrastrutture: { nome: string; slug: string }[];
  affiliazioni: { nome: string; slug: string }[];
}

function StarRating({ rating, reviews }: { rating: number | null; reviews: number }) {
  if (rating === null || reviews === 0) {
    return (
      <div className="text-xs text-[color:var(--ds-gray-500)] font-mono">
        Nessuna recensione
      </div>
    );
  }
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span aria-hidden className="text-amber-500 tracking-tight">
        {"★".repeat(full)}
        {half ? "½" : ""}
        <span className="text-[color:var(--ds-gray-200)]">
          {"★".repeat(5 - full - (half ? 1 : 0))}
        </span>
      </span>
      <span className="font-medium text-[color:var(--ds-gray-900)]">
        {rating.toFixed(1)}
      </span>
      <span className="text-[color:var(--ds-gray-500)]">({reviews})</span>
    </div>
  );
}

function Avatar({ name, claimed }: { name: string; claimed: boolean }) {
  const initial = (name || "?").trim().charAt(0).toUpperCase();
  return (
    <div
      className={`h-12 w-12 shrink-0 grid place-items-center rounded-lg font-mono text-base font-semibold tracking-tight ${
        claimed
          ? "bg-[color:var(--ds-gray-900)] text-white"
          : "bg-white text-[color:var(--ds-gray-900)]"
      }`}
      style={{ boxShadow: "var(--shadow-border)" }}
      aria-hidden
    >
      {initial}
    </div>
  );
}

function PillVerified({ claimed }: { claimed: boolean }) {
  return (
    <span className={`pill ${claimed ? "pill-verified" : "pill-unclaimed"}`}>
      <span
        aria-hidden
        className={`inline-block h-1.5 w-1.5 rounded-full ${
          claimed ? "bg-[color:var(--ds-verified)]" : "bg-[color:var(--ds-gray-400)]"
        }`}
      />
      {claimed ? "Verificato" : "Non verificato"}
    </span>
  );
}

/**
 * Card singolo centro per la grid dei risultati.
 * Layout denso, gerarchico:
 * - Header: nome completo + chip Verificato in alto
 * - Avatar + localizzazione + ragione sociale (mono)
 * - Rating
 * - Metodo educativo (chip viola, prominente)
 * - Attività (chip ciano)
 * - Infrastrutture (chip arancio, max 3)
 * - CTA
 */
export function CentroCard({ centro }: { centro: SearchResult }) {
  const displayName = centro.brand_name || centro.ragione_sociale;
  const hasBrand =
    !!centro.brand_name && centro.brand_name !== centro.ragione_sociale;

  return (
    <article className="card p-5 flex flex-col gap-4 transition-shadow hover:shadow-[0_0_0_1px_rgba(0,0,0,0.08),0_4px_8px_-2px_rgba(0,0,0,0.06),0_8px_16px_-8px_rgba(0,0,0,0.05)]">
      {/* Top row: chip verificato (sopra) */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-eyebrow">#{centro.id}</span>
        <PillVerified claimed={centro.claimed} />
      </div>

      {/* Header: avatar + full name (sempre completo, niente truncate) */}
      <header className="flex items-start gap-3">
        <Avatar name={displayName} claimed={centro.claimed} />
        <div className="min-w-0 flex-1">
          <h3 className="text-h3 leading-tight">
            <Link
              href={`/centro/${centro.slug}/`}
              className="hover:underline decoration-[color:var(--ds-gray-400)] underline-offset-4 break-words"
            >
              {displayName}
            </Link>
          </h3>
          {hasBrand && (
            <div className="mt-1 text-xs text-[color:var(--ds-gray-500)] font-mono break-words">
              {centro.ragione_sociale}
            </div>
          )}
          <div className="mt-1 text-xs text-[color:var(--ds-gray-500)]">
            {[centro.comune, centro.provincia_sigla ? `(${centro.provincia_sigla})` : null, centro.regione_nome]
              .filter(Boolean)
              .join(" · ")}
          </div>
        </div>
      </header>

      {/* Rating */}
      <StarRating rating={centro.rating_medio} reviews={centro.num_recensioni} />

      {/* Methodologies — chip viola, prominente */}
      {centro.metodologie.length > 0 && (
        <div>
          <div className="text-eyebrow mb-2">Metodo educativo</div>
          <div className="flex flex-wrap gap-1.5">
            {centro.metodologie.map((m) => (
              <span key={m.slug} className="pill pill-method">
                {m.nome}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Activities / disciplines — chip ciano */}
      {centro.discipline.length > 0 && (
        <div>
          <div className="text-eyebrow mb-2">Attività</div>
          <div className="flex flex-wrap gap-1.5">
            {centro.discipline.slice(0, 5).map((d) => (
              <span key={d.slug} className="pill pill-discipline">
                {d.nome}
              </span>
            ))}
            {centro.discipline.length > 5 && (
              <span className="pill pill-unclaimed">
                +{centro.discipline.length - 5}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Infrastrutture — chip arancio, max 3 */}
      {centro.infrastrutture.length > 0 && (
        <div>
          <div className="text-eyebrow mb-2">Struttura</div>
          <div className="flex flex-wrap gap-1.5">
            {centro.infrastrutture.slice(0, 3).map((i) => (
              <span key={i.slug} className="pill pill-infra">
                {i.nome}
              </span>
            ))}
            {centro.infrastrutture.length > 3 && (
              <span className="pill pill-unclaimed">
                +{centro.infrastrutture.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      {/* CTA */}
      <footer className="pt-2 mt-auto">
        <Link href={`/centro/${centro.slug}/`} className="btn-secondary w-full">
          Apri scheda dettagliata
          <span aria-hidden className="text-[color:var(--ds-gray-500)]">
            →
          </span>
        </Link>
      </footer>
    </article>
  );
}

export function ResultsGrid({ centri }: { centri: SearchResult[] }) {
  if (centri.length === 0) {
    return (
      <div className="card p-12 text-center">
        <div className="text-eyebrow mb-3">Nessun risultato</div>
        <h3 className="text-h2 mb-2">Nessun centro corrisponde ai filtri</h3>
        <p className="text-sm text-[color:var(--ds-gray-500)] max-w-md mx-auto">
          Prova a rimuovere alcuni filtri o a cercare un altro comune. Stiamo
          mappando attivamente tutta Italia: se manca una struttura, segnalacela.
        </p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {centri.map((c) => (
        <CentroCard key={c.id} centro={c} />
      ))}
    </div>
  );
}