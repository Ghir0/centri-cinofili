import type { CentroExpanded } from '@/types/centro'
import Link from 'next/link'
import CentroMapWrapper from './CentroMapWrapper'

function Badge({ label, color = 'blue' }: { label: string; color?: 'blue' | 'green' | 'purple' | 'orange' | 'emerald' }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    orange: 'bg-orange-100 text-orange-800',
    emerald: 'bg-emerald-100 text-emerald-800',
  }
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${colors[color]}`}>
      {label}
    </span>
  )
}

function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-yellow-500">
      {'★'.repeat(Math.round(rating))}{'☆'.repeat(5 - Math.round(rating))}
    </span>
  )
}

interface CentroDetailProps {
  centro: CentroExpanded
}

export default function CentroDetail({ centro }: CentroDetailProps) {
  const displayName = centro.brand_name || centro.ragione_sociale
  const hasSocial = centro.social_links && (
    centro.social_links.instagram || centro.social_links.facebook || centro.social_links.tiktok
  )

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 mb-6" aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1">
          <li><Link href="/" className="hover:text-gray-700">Home</Link></li>
          <li className="mx-1">›</li>
          {centro.regione && (
            <>
              <li><Link href={`/regione/${centro.regione.slug}`} className="hover:text-gray-700">{centro.regione.nome}</Link></li>
              <li className="mx-1">›</li>
            </>
          )}
          {centro.provincia && (
            <>
              <li><Link href={`/provincia/${centro.provincia.slug}`} className="hover:text-gray-700">{centro.provincia.nome} ({centro.provincia.sigla})</Link></li>
              <li className="mx-1">›</li>
            </>
          )}
          <li className="text-gray-900 font-medium truncate">{displayName}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{displayName}</h1>
        {centro.brand_name && centro.brand_name !== centro.ragione_sociale && (
          <p className="text-gray-500 mb-1">{centro.ragione_sociale}</p>
        )}
        {centro.rating_medio !== null && centro.rating_medio > 0 && (
          <div className="flex items-center gap-2">
            <Stars rating={centro.rating_medio} />
            <span className="text-sm text-gray-500">
              {centro.rating_medio.toFixed(1)} ({centro.num_recensioni} recensioni)
            </span>
          </div>
        )}

        {/* Claim badge */}
        {centro.claim_status === 'unclaimed' && (
          <div className="mt-3">
            <Link
              href={`/centro/${centro.slug}/rivendica`}
              className="inline-block bg-amber-50 border border-amber-300 text-amber-800 px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-100 transition-colors"
            >
              🔒 Rivendica il tuo centro — Sei il proprietario? Richiedi la gestione di questa scheda
            </Link>
          </div>
        )}
      </div>

      {/* Contatti — tutti visibili senza click */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📞 Contatti</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {centro.telefono && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">☎️</span>
              <a href={`tel:${centro.telefono}`} className="text-blue-600 hover:underline">{centro.telefono}</a>
            </div>
          )}
          {centro.email && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">✉️</span>
              <a href={`mailto:${centro.email}`} className="text-blue-600 hover:underline break-all">{centro.email}</a>
            </div>
          )}
          {centro.sito_web && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">🌐</span>
              <a href={centro.sito_web} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline break-all">
                {centro.sito_web}
              </a>
            </div>
          )}
        </div>

        {/* Social links */}
        {hasSocial && (
          <div className="flex gap-3 mt-4 pt-4 border-t border-gray-100">
            {centro.social_links?.instagram && (
              <a href={centro.social_links.instagram} target="_blank" rel="noopener noreferrer" className="text-pink-600 hover:text-pink-800 text-sm">
                📷 Instagram
              </a>
            )}
            {centro.social_links?.facebook && (
              <a href={centro.social_links.facebook} target="_blank" rel="noopener noreferrer" className="text-blue-700 hover:text-blue-900 text-sm">
                📘 Facebook
              </a>
            )}
            {centro.social_links?.tiktok && (
              <a href={centro.social_links.tiktok} target="_blank" rel="noopener noreferrer" className="text-gray-700 hover:text-gray-900 text-sm">
                🎵 TikTok
              </a>
            )}
          </div>
        )}
      </section>

      {/* Indirizzo e mappa */}
      {centro.indirizzo && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📍 Dove siamo</h2>
          <p className="text-gray-700 mb-2">
            {centro.indirizzo}
            {centro.comune && `, ${centro.comune}`}
            {centro.cap && ` (${centro.cap})`}
          </p>
          {centro.coordinate_gps && (
            <div className="h-64 rounded-lg overflow-hidden border border-gray-200">
              <CentroMapWrapper
                lat={centro.coordinate_gps.lat}
                lon={centro.coordinate_gps.lon}
                nome={displayName}
              />
            </div>
          )}
        </section>
      )}

      {/* Metodologie */}
      {centro.metodologie.length > 0 && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🐕 Metodologie di addestramento</h2>
          <div className="flex flex-wrap gap-2">
            {centro.metodologie.map((m) => (
              <Badge key={m.id} label={m.nome} color="purple" />
            ))}
          </div>
        </section>
      )}

      {/* Discipline */}
      {centro.discipline.length > 0 && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🎯 Discipline cinofile</h2>
          <div className="flex flex-wrap gap-2">
            {centro.discipline.map((d) => (
              <Badge key={d.id} label={d.nome} color="green" />
            ))}
          </div>
        </section>
      )}

      {/* Infrastrutture */}
      {centro.infrastrutture.length > 0 && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🏗️ Infrastrutture e servizi</h2>
          <div className="flex flex-wrap gap-2">
            {centro.infrastrutture.map((i) => (
              <Badge key={i.id} label={i.nome} color="orange" />
            ))}
          </div>
        </section>
      )}

      {/* Affiliazioni */}
      {centro.affiliazioni.length > 0 && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📜 Affiliazioni</h2>
          <div className="flex flex-wrap gap-2">
            {centro.affiliazioni.map((a) => (
              <div key={a.id}>
                <Badge label={a.nome} color="emerald" />
                {a.ente_ufficiale && (
                  <span className="ml-1 text-xs text-gray-400">({a.ente_ufficiale})</span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Descrizione */}
      {centro.descrizione && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📝 Chi siamo</h2>
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{centro.descrizione}</p>
        </section>
      )}

      {/* Recensioni */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          ⭐ Recensioni
          {centro.num_recensioni > 0 && (
            <span className="text-sm font-normal text-gray-500 ml-2">({centro.num_recensioni})</span>
          )}
        </h2>
        {centro.num_recensioni === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-lg">Nessuna recensione ancora</p>
            <p className="text-sm mt-1">Sii il primo a lasciare una recensione!</p>
          </div>
        ) : (
          <p className="text-gray-500">Recensioni in caricamento…</p>
        )}
      </section>
    </div>
  )
}
