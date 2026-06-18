import Link from 'next/link';
import type { Metadata } from 'next';
import { createStaticClient } from '@/lib/supabase/static';
import { notFound } from 'next/navigation';
import { searchCentri } from '@/lib/centri';
import { ResultsGrid } from '@/components/ResultsGrid';

export const dynamicParams = false;

type AttivitaKind = 'disciplina' | 'infrastruttura';
const ATTIVITA_SLUG_MAP: Record<string, { nome: string; kind: AttivitaKind }> = {
  'agility-dog': { nome: 'Agility Dog', kind: 'disciplina' },
  'rally-o': { nome: 'Rally-O', kind: 'disciplina' },
  'hoopers': { nome: 'Hoopers', kind: 'disciplina' },
  'nosework': { nome: 'Nosework / Ricerca Olfattiva', kind: 'disciplina' },
  'propriocezione': { nome: 'Propriocezione / Mobilità', kind: 'disciplina' },
  'socializzazione': { nome: 'Classi di Socializzazione', kind: 'disciplina' },
  'recupero-comportamentale': { nome: 'Recupero Comportamentale', kind: 'disciplina' },
  'educazione-base': { nome: 'Educazione Base Cuccioli', kind: 'disciplina' },
  'campo-coperto': { nome: 'Campo Coperto (Indoor)', kind: 'infrastruttura' },
  'campo-recintato': { nome: 'Campo Recintato in Sicurezza', kind: 'infrastruttura' },
  'piscina': { nome: 'Piscina Cinofila', kind: 'infrastruttura' },
  'asilo-diurno': { nome: 'Area Asilo Diurno', kind: 'infrastruttura' },
};

export async function generateStaticParams() {
  const supabase = createStaticClient();
  const { data: province } = await supabase.from('province').select('slug');
  if (!province) return [];
  const slugs = Object.keys(ATTIVITA_SLUG_MAP);
  const params: { provincia: string; attivita: string }[] = [];
  for (const p of province) {
    for (const s of slugs) {
      params.push({ provincia: p.slug, attivita: s });
    }
  }
  return params;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ provincia: string; attivita: string }>;
}): Promise<Metadata> {
  const { provincia, attivita } = await params;
  const info = ATTIVITA_SLUG_MAP[attivita];
  if (!info) return { title: 'Non trovato' };
  const provDisplay = provincia
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');
  return {
    title: `${info.nome} a ${provDisplay} | Centri Cinofili`,
    description: `Trova i centri cinofili a ${provDisplay} che offrono ${info.nome.toLowerCase()}. Filtra per metodo educativo e consulta le schede dettagliate.`,
  };
}

export default async function ProvinciaAttivitaPage({
  params,
}: {
  params: Promise<{ provincia: string; attivita: string }>;
}) {
  const { provincia, attivita } = await params;
  const info = ATTIVITA_SLUG_MAP[attivita];
  if (!info) notFound();

  const supabase = createStaticClient();
  const { data: provData } = await supabase
    .from('province')
    .select('nome, slug, sigla, regione:regione_id(nome, slug)')
    .eq('slug', provincia)
    .single();
  if (!provData) notFound();

  // Filter centri that ACTUALLY have this attivita (discipline OR infrastrutture).
  // `searchCentri` accepts the plural form internally.
  const filters =
    info.kind === 'disciplina'
      ? { discipline: [attivita], provincia: provincia }
      : { infrastrutture: [attivita], provincia: provincia };

  const centri = await searchCentri(filters);

  const provDisplay = provData.nome;
  const regione = (provData as any).regione;
  const regioneNome = regione?.nome || '';
  const regioneSlug = regione?.slug || '';

  return (
    <>
      <section className="border-b border-[color:var(--ds-gray-100)] bg-white">
        <div className="mx-auto max-w-7xl px-6 pt-14 pb-12">
          <nav aria-label="Breadcrumb" className="mb-6 text-sm">
            <ol className="flex flex-wrap items-center gap-1.5 text-[color:var(--ds-gray-500)]">
              <li>
                <Link href="/" className="hover:text-[color:var(--ds-gray-900)]">
                  Home
                </Link>
              </li>
              <li aria-hidden>›</li>
              {regioneSlug && (
                <>
                  <li>
                    <Link
                      href={`/centri-cinofili/${regioneSlug}/`}
                      className="hover:text-[color:var(--ds-gray-900)]"
                    >
                      {regioneNome}
                    </Link>
                  </li>
                  <li aria-hidden>›</li>
                </>
              )}
              <li>
                <Link
                  href={`/centri-cinofili/${regioneSlug}/${provincia}/`}
                  className="hover:text-[color:var(--ds-gray-900)]"
                >
                  {provDisplay} ({provData.sigla})
                </Link>
              </li>
              <li aria-hidden>›</li>
              <li className="text-[color:var(--ds-gray-900)] font-medium">{info.nome}</li>
            </ol>
          </nav>

          <div className="flex items-center gap-2 mb-5">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${
                info.kind === 'disciplina'
                  ? 'bg-[color:var(--ds-verified)]'
                  : 'bg-[color:var(--ds-accent-infra,#de1d8d)]'
              }`}
            />
            <span className="text-eyebrow">
              {info.kind === 'disciplina' ? 'Disciplina' : 'Infrastruttura'} ·{' '}
              {provDisplay} ({provData.sigla})
            </span>
          </div>

          <h1 className="text-display max-w-3xl">
            {info.nome} a {provDisplay}.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[color:var(--ds-gray-600)]">
            {centri.length === 0
              ? `Al momento nessun centro a ${provDisplay} offre ${info.nome.toLowerCase()}.`
              : `${centri.length} ${centri.length === 1 ? 'centro offre' : 'centri offrono'} ${info.nome.toLowerCase()} a ${provDisplay}. Schede complete con metodo educativo, contatti e mappa.`}
          </p>

          <div className="mt-7 flex items-center gap-3 flex-wrap">
            <Link
              href={
                info.kind === 'disciplina'
                  ? `/?regione=${regioneSlug}&provincia=${provincia}&disciplina=${attivita}`
                  : `/?regione=${regioneSlug}&provincia=${provincia}&infrastruttura=${attivita}`
              }
              className="btn-primary"
            >
              <span aria-hidden>⌘</span>
              Filtra recordset
            </Link>
            <Link
              href={`/centri-cinofili/${regioneSlug}/${provincia}/`}
              className="btn-secondary"
            >
              ← Tutti i centri a {provDisplay}
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex items-baseline justify-between mb-6">
          <div>
            <h2 className="text-h2">
              {centri.length}{' '}
              <span className="text-[color:var(--ds-gray-500)] font-normal">
                {centri.length === 1 ? 'centro' : 'centri'}
              </span>
            </h2>
            <p className="text-xs text-[color:var(--ds-gray-500)] mt-1 font-mono">
              recordset per {info.nome} · {provDisplay} ({provData.sigla})
            </p>
          </div>
        </div>

        <ResultsGrid centri={centri} />
      </section>
    </>
  );
}