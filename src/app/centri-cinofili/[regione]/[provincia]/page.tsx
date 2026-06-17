import Link from 'next/link';
import { notFound } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { createStaticClient } from '@/lib/supabase/static';
import { Provincia, Regione, CentroExpanded, Metodologia } from '@/types/centro';

export const dynamicParams = false;

export async function generateStaticParams() {
  const supabase = createStaticClient();

  // Fetch all region-province pairs
  const { data: province } = await supabase
    .from('province')
    .select('slug, regioni!inner(slug)');

  if (!province) return [];

  return province.map(
    (p: { slug: string; regioni: { slug: string } | { slug: string }[] }) => {
      const regioneSlug = Array.isArray(p.regioni)
        ? (p.regioni[0] as { slug: string }).slug
        : (p.regioni as { slug: string }).slug;
      return {
        regione: regioneSlug,
        provincia: p.slug,
      };
    }
  );
}

interface ProvinciaPageProps {
  params: Promise<{ regione: string; provincia: string }>;
}

export default async function ProvinciaPage({ params }: ProvinciaPageProps) {
  const { regione: regioneSlug, provincia: provinciaSlug } = await params;
  const supabase = await createClient();

  // Fetch regione
  const { data: regioneData } = await supabase
    .from('regioni')
    .select('*')
    .eq('slug', regioneSlug)
    .single();

  if (!regioneData) {
    notFound();
  }

  // Fetch provincia
  const { data: provinciaData } = await supabase
    .from('province')
    .select('*')
    .eq('slug', provinciaSlug)
    .eq('regione_id', regioneData.id)
    .single();

  if (!provinciaData) {
    notFound();
  }

  const provincia: Provincia = {
    id: provinciaData.id,
    nome: provinciaData.nome,
    slug: provinciaData.slug,
    sigla: provinciaData.sigla,
    regione_id: provinciaData.regione_id,
  };

  const regione: Regione = {
    id: regioneData.id,
    nome: regioneData.nome,
    slug: regioneData.slug,
  };

  // Fetch centri in this province with metodologie and rating info
  const { data: centriData } = await supabase
    .from('centri')
    .select(
      `
      *,
      centri_metodologie!left ( metodologie ( * ) ),
      recensioni ( rating )
    `
    )
    .eq('provincia_id', provincia.id)
    .order('ragione_sociale');

  // Process centri data to add computed fields
  const centri: CentroExpanded[] = (centriData || []).map((c: Record<string, unknown>) => {
    // Extract metodologie from junction table
    const metodologie: Metodologia[] = Array.isArray(c.centri_metodologie)
      ? (c.centri_metodologie as Array<{ metodologie: Metodologia | null }>)
          .filter(
            (cm: { metodologie: Metodologia | null }) => cm.metodologie !== null
          )
          .map((cm: { metodologie: Metodologia | null }) => cm.metodologie!)
      : [];

    // Compute average rating
    const recensioni: Array<{ rating: number }> = Array.isArray(c.recensioni)
      ? (c.recensioni as Array<{ rating: number }>)
      : [];
    const rating_medio =
      recensioni.length > 0
        ? recensioni.reduce((sum, r) => sum + r.rating, 0) / recensioni.length
        : 0;
    const num_recensioni = recensioni.length;

    // Parse social_links safely
    let socialLinks = null;
    if (c.social_links && typeof c.social_links === 'object') {
      socialLinks = c.social_links as CentroExpanded['social_links'];
    }

    // Parse coordinate_gps safely
    let coords = null;
    if (c.coordinate_gps && typeof c.coordinate_gps === 'object') {
      coords = c.coordinate_gps as { lat: number; lon: number };
    }

    return {
      id: c.id as number,
      ragione_sociale: c.ragione_sociale as string,
      brand_name: c.brand_name as string | null,
      slug: c.slug as string,
      indirizzo: c.indirizzo as string | null,
      comune: c.comune as string | null,
      cap: c.cap as string | null,
      provincia_id: c.provincia_id as number | null,
      coordinate_gps: coords,
      telefono: c.telefono as string | null,
      email: c.email as string | null,
      sito_web: c.sito_web as string | null,
      social_links: socialLinks,
      descrizione: c.descrizione as string | null,
      claim_status: (c.claim_status || 'unclaimed') as 'unclaimed' | 'pending' | 'claimed',
      created_at: c.created_at as string,
      updated_at: c.updated_at as string,
      provincia: provincia,
      regione: regione,
      metodologie,
      discipline: [],
      infrastrutture: [],
      affiliazioni: [],
      rating_medio: Math.round(rating_medio * 10) / 10,
      num_recensioni,
    };
  });

  // JSON-LD ItemList
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Centri Cinofili in provincia di ${provincia.nome} (${provincia.sigla})`,
    description: `Elenco di centri cinofili in ${provincia.nome}, ${regione.nome}.`,
    numberOfItems: centri.length,
    itemListElement: centri.map((centro, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      item: {
        '@type': 'LocalBusiness',
        '@id': `${process.env.NEXT_PUBLIC_SITE_URL || ''}/centro/${centro.slug}`,
        name: centro.brand_name || centro.ragione_sociale,
        address: centro.indirizzo
          ? {
              '@type': 'PostalAddress',
              streetAddress: centro.indirizzo,
              addressLocality: centro.comune || provincia.nome,
              addressRegion: regione.nome,
              postalCode: centro.cap || '',
            }
          : undefined,
        aggregateRating:
          centro.num_recensioni > 0
            ? {
                '@type': 'AggregateRating',
                ratingValue: centro.rating_medio,
                reviewCount: centro.num_recensioni,
              }
            : undefined,
      },
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="mx-auto max-w-4xl px-4 py-12">
        <nav aria-label="Breadcrumb" className="mb-8 text-sm text-zinc-500">
          <ol className="flex flex-wrap gap-1">
            <li>
              <Link href="/" className="hover:text-zinc-800 transition-colors">
                Home
              </Link>
            </li>
            <li aria-hidden="true">›</li>
            <li>
              <Link
                href="/centri-cinofili"
                className="hover:text-zinc-800 transition-colors"
              >
                Centri Cinofili
              </Link>
            </li>
            <li aria-hidden="true">›</li>
            <li>
              <Link
                href={`/centri-cinofili/${regione.slug}`}
                className="hover:text-zinc-800 transition-colors"
              >
                {regione.nome}
              </Link>
            </li>
            <li aria-hidden="true">›</li>
            <li className="font-medium text-zinc-800">
              {provincia.nome} ({provincia.sigla})
            </li>
          </ol>
        </nav>

        <h1 className="mb-2 text-3xl font-bold tracking-tight text-zinc-900">
          Centri Cinofili in {provincia.nome}
        </h1>
        <p className="mb-8 text-zinc-500">
          Provincia di {provincia.nome} ({provincia.sigla}) — {regione.nome}
        </p>

        {centri.length === 0 ? (
          <p className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 text-center text-zinc-500">
            Nessun centro cinofilo registrato in questa provincia.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-100 rounded-xl border border-zinc-200 bg-white">
            {centri.map((centro) => (
              <li key={centro.id} className="p-5">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <Link
                      href={`/centro/${centro.slug}`}
                      className="text-lg font-semibold text-zinc-800 hover:text-blue-600 transition-colors"
                    >
                      {centro.brand_name || centro.ragione_sociale}
                    </Link>

                    {centro.indirizzo && (
                      <p className="mt-1 text-sm text-zinc-500">
                        {centro.indirizzo}
                        {centro.comune && ` — ${centro.comune}`}
                        {centro.cap && ` ${centro.cap}`}
                      </p>
                    )}

                    {/* Metodologie badges */}
                    {centro.metodologie.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {centro.metodologie.map((met) => (
                          <span
                            key={met.id}
                            className="inline-block rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                          >
                            {met.nome}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Rating */}
                  <div className="flex items-center gap-2 sm:flex-shrink-0 sm:text-right">
                    <div className="flex items-center gap-1">
                      <span
                        className={`text-sm font-medium ${
                          centro.num_recensioni > 0
                            ? 'text-yellow-600'
                            : 'text-zinc-400'
                        }`}
                      >
                        {centro.num_recensioni > 0 ? '★' : '☆'}
                      </span>
                      <span className="text-sm font-medium text-zinc-600">
                        {(centro.rating_medio ?? 0).toFixed(1)}
                      </span>
                    </div>
                    <span className="text-xs text-zinc-400">
                      ({centro.num_recensioni}{' '}
                      {centro.num_recensioni === 1 ? 'recensione' : 'recensioni'})
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
