import Link from 'next/link';
import { createClient } from '@/lib/supabase/server';
import { Regione } from '@/types/centro';

export const dynamicParams = false;

export async function generateStaticParams() {
  // Nothing to pre-generate; this is the index page itself.
  return [];
}

export default async function CentriCinofiliIndex() {
  const supabase = await createClient();

  const { data: regioni } = await supabase
    .from('regioni')
    .select('*')
    .order('nome');

  const regioniList: Regione[] = (regioni || []).map((r) => ({
    id: r.id,
    nome: r.nome,
    slug: r.slug,
  }));

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Centri Cinofili per Regione',
    description:
      'Elenco di centri cinofili in Italia organizzati per regione e provincia.',
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
            <li className="font-medium text-zinc-800">Centri Cinofili</li>
          </ol>
        </nav>

        <h1 className="mb-6 text-3xl font-bold tracking-tight text-zinc-900">
          Centri Cinofili
        </h1>

        <p className="mb-10 max-w-2xl text-lg text-zinc-600">
          Scopri i migliori centri cinofili in Italia, organizzati per regione e
          provincia. Ogni scheda include informazioni su indirizzo, metodologie,
          discipline e recensioni dei clienti.
        </p>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {regioniList.map((regione) => (
            <Link
              key={regione.id}
              href={`/centri-cinofili/${regione.slug}`}
              className="rounded-xl border border-zinc-200 bg-white p-5 transition-all hover:border-zinc-400 hover:shadow-md"
            >
              <span className="text-lg font-semibold text-zinc-800">
                {regione.nome}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
