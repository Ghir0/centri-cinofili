import Link from 'next/link';
import { notFound } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';
import { createStaticClient } from '@/lib/supabase/static';
import { Provincia, Regione } from '@/types/centro';

export const dynamicParams = false;

export async function generateStaticParams() {
  const supabase = createStaticClient();
  const { data: regioni } = await supabase
    .from('regioni')
    .select('slug');

  if (!regioni) return [];

  return regioni.map((r: { slug: string }) => ({
    regione: r.slug,
  }));
}

interface RegionePageProps {
  params: Promise<{ regione: string }>;
}

export default async function RegionePage({ params }: RegionePageProps) {
  const { regione: regioneSlug } = await params;
  const supabase = await createClient();

  // Fetch the region
  const { data: regioneData } = await supabase
    .from('regioni')
    .select('*')
    .eq('slug', regioneSlug)
    .single();

  if (!regioneData) {
    notFound();
  }

  const regione: Regione = {
    id: regioneData.id,
    nome: regioneData.nome,
    slug: regioneData.slug,
  };

  // Fetch provinces belonging to this region
  const { data: provinceData } = await supabase
    .from('province')
    .select('*')
    .eq('regione_id', regione.id)
    .order('nome');

  const province: Provincia[] = (provinceData || []).map((p) => ({
    id: p.id,
    nome: p.nome,
    slug: p.slug,
    sigla: p.sigla,
    regione_id: p.regione_id,
  }));

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `Centri Cinofili in ${regione.nome}`,
    description: `Elenco di centri cinofili in ${regione.nome} organizzati per provincia.`,
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
            <li className="font-medium text-zinc-800">{regione.nome}</li>
          </ol>
        </nav>

        <h1 className="mb-6 text-3xl font-bold tracking-tight text-zinc-900">
          Centri Cinofili in {regione.nome}
        </h1>

        {province.length === 0 ? (
          <p className="text-zinc-500">
            Nessuna provincia trovata per questa regione.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {province.map((prov) => (
              <Link
                key={prov.id}
                href={`/centri-cinofili/${regione.slug}/${prov.slug}`}
                className="rounded-xl border border-zinc-200 bg-white p-5 transition-all hover:border-zinc-400 hover:shadow-md"
              >
                <span className="text-lg font-semibold text-zinc-800">
                  {prov.nome}
                </span>
                <span className="ml-2 text-sm text-zinc-400">({prov.sigla})</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
