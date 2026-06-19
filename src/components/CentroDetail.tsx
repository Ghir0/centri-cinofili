import type { CentroExpanded, SocialLinks } from "@/types/centro";
import Link from "next/link";
import CentroMapWrapper from "./CentroMapWrapper";
import { PawIcon } from "@/components/PawIcon";

interface CentroDetailProps {
  centro: CentroExpanded;
}

function Stars({ rating }: { rating: number }) {
  const full = Math.round(rating);
  return (
    <span aria-hidden className="text-amber-500 tracking-tight">
      {"★".repeat(full)}
      <span className="text-[color:var(--ds-gray-200)]">{"★".repeat(5 - full)}</span>
    </span>
  );
}

function IconCheck() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"
        fill="currentColor"
      />
    </svg>
  );
}

function MetaItem({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-eyebrow mb-1.5">{label}</div>
      <div className="text-sm text-[color:var(--ds-gray-900)]">{children}</div>
    </div>
  );
}

function socialUrl(raw: string, platform: 'instagram' | 'facebook' | 'tiktok'): string {
  // Already a full URL
  if (/^https?:\/\//i.test(raw)) return raw;

  // Clean up: remove leading @ and trailing slashes
  let handle = raw.replace(/^@/, '').replace(/\/+$/, '');

  // Handle Facebook URLs that are missing the protocol
  if (/^facebook\.com\//i.test(handle)) return `https://${handle}`;
  if (/^(www\.)?facebook\.com\//i.test(handle)) return `https://${handle}`;

  // Build platform-specific URL
  const bases: Record<string, string> = {
    instagram: 'https://instagram.com/',
    facebook: 'https://facebook.com/',
    tiktok: 'https://tiktok.com/@',
  };
  return bases[platform] + handle;
}

export default function CentroDetail({ centro }: CentroDetailProps) {
  const displayName = centro.brand_name || centro.ragione_sociale;
  const isClaimed = centro.claim_status === "claimed";

  // Costruisci URL Google Maps per indicazioni stradali
  let mapsUrl: string | null = null;
  if (centro.coordinate_gps) {
    mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${centro.coordinate_gps.lat},${centro.coordinate_gps.lon}`;
  } else if (centro.indirizzo && centro.comune) {
    const q = encodeURIComponent(`${centro.indirizzo}, ${centro.comune}`);
    mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${q}`;
  }

  const social: SocialLinks | null = centro.social_links;

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="mb-6 text-sm">
        <ol className="flex flex-wrap items-center gap-1.5 text-[color:var(--ds-gray-500)]">
          <li>
            <Link href="/" className="hover:text-[color:var(--ds-gray-900)]">
              Home
            </Link>
          </li>
          <li aria-hidden>›</li>
          {centro.regione && (
            <>
              <li>
                <Link
                  href={`/centri-cinofili/${centro.regione.slug}/`}
                  className="hover:text-[color:var(--ds-gray-900)]"
                >
                  {centro.regione.nome}
                </Link>
              </li>
              <li aria-hidden>›</li>
            </>
          )}
          {centro.provincia && (
            <>
              <li>
                <Link
                  href={`/centri-cinofili/${centro.regione?.slug}/${centro.provincia.slug}/`}
                  className="hover:text-[color:var(--ds-gray-900)]"
                >
                  {centro.provincia.nome} ({centro.provincia.sigla})
                </Link>
              </li>
              <li aria-hidden>›</li>
            </>
          )}
          <li className="text-[color:var(--ds-gray-900)] font-medium truncate max-w-[200px] sm:max-w-none">
            {displayName}
          </li>
        </ol>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
        {/* ===== COLONNA PRINCIPALE ===== */}
        <div className="space-y-6">
          {/* Hero card — anagrafica */}
          <header className="card p-7">
            <div className="flex items-start gap-5">
              <div
                className="h-16 w-16 shrink-0 grid place-items-center rounded-lg bg-[color:var(--ds-gray-900)] text-white"
                aria-hidden
              >
                <PawIcon className="h-8 w-8" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <h1 className="text-h1">{displayName}</h1>
                    {centro.brand_name && centro.brand_name !== centro.ragione_sociale && (
                      <p className="mt-1 text-sm font-mono text-[color:var(--ds-gray-500)]">
                        {centro.ragione_sociale}
                      </p>
                    )}
                    <div className="mt-2 flex items-center gap-3 text-sm text-[color:var(--ds-gray-500)]">
                      <span>
                        {[centro.comune, centro.provincia?.sigla, centro.regione?.nome]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                      {isClaimed && (
                        <span className="pill pill-verified">
                          <span
                            aria-hidden
                            className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]"
                          />
                          Verificato
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Rating */}
                {centro.rating_medio !== null && centro.rating_medio > 0 && (
                  <div className="mt-4 flex items-center gap-2">
                    <Stars rating={centro.rating_medio} />
                    <span className="font-semibold text-[color:var(--ds-gray-900)]">
                      {centro.rating_medio.toFixed(1)}
                    </span>
                    <span className="text-sm text-[color:var(--ds-gray-500)]">
                      · {centro.num_recensioni}{" "}
                      {centro.num_recensioni === 1 ? "recensione" : "recensioni"}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* CTAs rapidi */}
            {centro.telefono && (
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <a href={`tel:${centro.telefono}`} className="btn-primary">
                  <span aria-hidden>☎</span>
                  {centro.telefono}
                </a>
                {centro.email && (
                  <a href={`mailto:${centro.email}`} className="btn-secondary">
                    <span aria-hidden>✉</span>
                    Email
                  </a>
                )}
                {mapsUrl && (
                  <a
                    href={mapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary"
                  >
                    Indicazioni
                    <span aria-hidden>↗</span>
                  </a>
                )}
              </div>
            )}
          </header>

          {/* Descrizione */}
          {centro.descrizione && (
            <section className="card p-7">
              <div className="text-eyebrow mb-3">Chi siamo</div>
              <p className="text-base leading-relaxed text-[color:var(--ds-gray-600)]">
                {centro.descrizione}
              </p>
            </section>
          )}

          {/* Tassonomie in colonne */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Metodologie */}
            <section className="card p-6">
              <div className="text-eyebrow mb-4">Metodo educativo</div>
              {centro.metodologie.length > 0 ? (
                <ul className="space-y-2.5">
                  {centro.metodologie.map((m) => (
                    <li key={m.id} className="flex items-start gap-2.5">
                      <span className="mt-0.5 text-[color:var(--ds-verified)]">
                        <IconCheck />
                      </span>
                      <div className="flex-1">
                        <span className="pill pill-method">{m.nome}</span>
                        {m.descrizione && (
                          <div className="text-xs text-[color:var(--ds-gray-500)] mt-1.5">
                            {m.descrizione}
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[color:var(--ds-gray-400)] italic py-4">
                  Dati non ancora disponibili
                </p>
              )}
            </section>

            {/* Strutture */}
            <section className="card p-6">
              <div className="text-eyebrow mb-4">Strutture</div>
              {centro.infrastrutture.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {centro.infrastrutture.map((i) => (
                    <span key={i.id} className="pill pill-infra">
                      {i.nome}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[color:var(--ds-gray-400)] italic py-4">
                  Dati non ancora disponibili
                </p>
              )}
            </section>

            {/* Discipline / Attività */}
            <section className="card p-6">
              <div className="text-eyebrow mb-4">Attività</div>
              {centro.discipline.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {centro.discipline.map((d) => (
                    <span key={d.id} className="pill pill-discipline">
                      {d.nome}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[color:var(--ds-gray-400)] italic py-4">
                  Dati non ancora disponibili
                </p>
              )}
            </section>

            {/* Affiliazioni */}
            <section className="card p-6">
              <div className="text-eyebrow mb-4">Affiliazioni</div>
              {centro.affiliazioni.length > 0 ? (
                <ul className="space-y-2.5">
                  {centro.affiliazioni.map((a) => (
                    <li key={a.id} className="flex items-start gap-2.5">
                      <span className="mt-0.5 text-[color:var(--ds-verified)]">
                        <IconCheck />
                      </span>
                      <div>
                        <span className="pill pill-affil mr-2">{a.nome}</span>
                        {a.ente_ufficiale && (
                          <span className="text-xs text-[color:var(--ds-gray-500)] font-mono">
                            {a.ente_ufficiale}
                          </span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[color:var(--ds-gray-400)] italic py-4">
                  Dati non ancora disponibili
                </p>
              )}
            </section>
          </div>

          {/* Recensioni */}
          <section className="card p-7">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="text-eyebrow mb-1">Recensioni verificate</div>
                <h2 className="text-h2">
                  {centro.num_recensioni > 0
                    ? `${centro.num_recensioni} ${
                        centro.num_recensioni === 1 ? "recensione" : "recensioni"
                      }`
                    : "Nessuna recensione"}
                </h2>
              </div>
              {centro.num_recensioni > 0 && centro.rating_medio && (
                <div className="text-right">
                  <div className="text-3xl font-semibold tracking-tight">
                    {centro.rating_medio.toFixed(1)}
                  </div>
                  <Stars rating={centro.rating_medio} />
                </div>
              )}
            </div>
            {centro.num_recensioni === 0 ? (
              <div className="rounded-md bg-[color:var(--ds-gray-50)] p-6 text-center">
                <p className="text-sm text-[color:var(--ds-gray-600)]">
                  Ancora nessuna recensione su questa piattaforma. Se hai visitato il centro,
                  lascia la tua per aiutare altri proprietari.
                </p>
                <button className="btn-secondary mt-4" type="button" disabled>
                  Lascia una recensione
                  <span className="text-xs text-[color:var(--ds-gray-400)] font-mono">coming soon</span>
                </button>
              </div>
            ) : (
              <p className="text-sm text-[color:var(--ds-gray-500)]">
                Lista recensioni in caricamento…
              </p>
            )}
          </section>
        </div>

        {/* ===== SIDEBAR ===== */}
        <aside className="space-y-4 lg:sticky lg:top-20 self-start">
          {/* Claim CTA — solo se non claimed */}
          {centro.claim_status === "unclaimed" && (
            <div className="card p-5 border-l-4" style={{ borderLeftColor: "var(--ds-verified)" }}>
              <div className="text-eyebrow mb-2 text-[color:var(--ds-verified)]">
                Sei il proprietario?
              </div>
              <h3 className="text-h3 mb-2">Rivendica questa scheda</h3>
              <p className="text-sm text-[color:var(--ds-gray-600)] mb-4">
                Gestisci i dati del tuo centro direttamente: contatti, metodo educativo,
                infrastrutture, foto. La rivendicazione è gratuita.
              </p>
              <a
                href={`mailto:m.tamanti@webemento.com?subject=Rivendica%20scheda%20-%20${encodeURIComponent(displayName)}`}
                className="btn-primary w-full"
              >
                Rivendica scheda
                <span aria-hidden>→</span>
              </a>
              <p className="text-xs text-[color:var(--ds-gray-400)] mt-3">
                Coming soon — scrivici per inserire o rivendicare il tuo centro.
              </p>
            </div>
          )}

          {/* Indirizzo + mappa */}
          {(centro.indirizzo || centro.coordinate_gps) && (
            <div className="card p-5">
              <div className="text-eyebrow mb-3">Posizione</div>
              <div className="space-y-1 text-sm text-[color:var(--ds-gray-900)] mb-4">
                {centro.indirizzo && <div>{centro.indirizzo}</div>}
                <div>
                  {[centro.cap, centro.comune, centro.provincia?.sigla]
                    .filter(Boolean)
                    .join(" ")}
                </div>
                {centro.regione && (
                  <div className="text-[color:var(--ds-gray-500)]">{centro.regione.nome}</div>
                )}
              </div>
              {centro.coordinate_gps && (
                <div className="h-56 -mx-5 -mb-5 overflow-hidden rounded-b-lg border-t border-[color:var(--ds-gray-100)]">
                  <CentroMapWrapper
                    lat={centro.coordinate_gps.lat}
                    lon={centro.coordinate_gps.lon}
                    nome={displayName}
                  />
                </div>
              )}
            </div>
          )}

          {/* Dati di contatto */}
          <div className="card p-5">
            <div className="text-eyebrow mb-3">Contatti</div>
            <div className="space-y-3">
              {centro.telefono && (
                <MetaItem label="Telefono">
                  <a
                    href={`tel:${centro.telefono}`}
                    className="text-[color:var(--ds-link)] hover:underline"
                  >
                    {centro.telefono}
                  </a>
                </MetaItem>
              )}
              {centro.email && (
                <MetaItem label="Email">
                  <a
                    href={`mailto:${centro.email}`}
                    className="text-[color:var(--ds-link)] hover:underline break-all"
                  >
                    {centro.email}
                  </a>
                </MetaItem>
              )}
              {centro.sito_web && (
                <MetaItem label="Sito web">
                  <a
                    href={centro.sito_web}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[color:var(--ds-link)] hover:underline break-all"
                  >
                    {centro.sito_web.replace(/^https?:\/\//, "")}
                  </a>
                </MetaItem>
              )}
            </div>
          </div>

          {/* Social */}
          {social && (social.instagram || social.facebook || social.tiktok) && (
            <div className="card p-5">
              <div className="text-eyebrow mb-3">Social</div>
              <div className="flex gap-2">
                {social.instagram && (
                  <a
                    href={socialUrl(social.instagram, 'instagram')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary flex-1 justify-center text-xs"
                  >
                    <span>Instagram</span>
                    <span aria-hidden className="text-[color:var(--ds-gray-500)]">↗</span>
                  </a>
                )}
                {social.facebook && (
                  <a
                    href={socialUrl(social.facebook, 'facebook')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary flex-1 justify-center text-xs"
                  >
                    <span>Facebook</span>
                    <span aria-hidden className="text-[color:var(--ds-gray-500)]">↗</span>
                  </a>
                )}
                {social.tiktok && (
                  <a
                    href={socialUrl(social.tiktok, 'tiktok')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary flex-1 justify-center text-xs"
                  >
                    <span>TikTok</span>
                    <span aria-hidden className="text-[color:var(--ds-gray-500)]">↗</span>
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Metadati */}
          <div className="card-flat p-5 text-xs text-[color:var(--ds-gray-500)] font-mono">
            <div className="flex justify-between mb-2">
              <span>Scheda ID</span>
              <span className="text-[color:var(--ds-gray-900)]">#{centro.id}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Ultimo aggiornamento</span>
              <span className="text-[color:var(--ds-gray-900)]">
                {new Date(centro.updated_at).toLocaleDateString("it-IT")}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Fonte dati</span>
              <span className="text-[color:var(--ds-gray-900)]">Anagrafe pubblica</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}