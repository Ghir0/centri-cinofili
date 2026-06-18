import Link from "next/link";
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { createStaticClient } from "@/lib/supabase/static";
import { searchCentri } from "@/lib/centri";
import { ResultsGrid } from "@/components/ResultsGrid";
import type { Metadata } from "next";

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

export async function generateMetadata({ params }: ProvinciaPageProps) {
  const { regione: regioneSlug, provincia: provinciaSlug } = await params;
  return {
    title: `Centri Cinofili a ${provinciaSlug
      .split('-')
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
      .join(' ')} | ${regioneSlug}`,
  };
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

  const regioneNome = regioneData.nome;
  const regioneId = regioneData.id;
  const provinciaNome = provinciaData.nome;
  const provinciaSigla = provinciaData.sigla;

  // Use searchCentri (same engine as home) for full consistency with filters
  const centri = await searchCentri({
    regione: regioneSlug,
    provincia: provinciaSlug,
  });

  // JSON-LD ItemList
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Centri Cinofili in provincia di ${provinciaNome} (${provinciaSigla})`,
    description: `Elenco di centri cinofili a ${provinciaNome}, ${regioneNome}.`,
    numberOfItems: centri.length,
    itemListElement: centri.map((centro, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      item: {
        '@type': 'LocalBusiness',
        '@id': `/centro/${centro.slug}`,
        name: centro.brand_name || centro.ragione_sociale,
        address: centro.indirizzo
          ? {
              '@type': 'PostalAddress',
              streetAddress: centro.indirizzo,
              addressLocality: centro.comune || provinciaNome,
              addressRegion: regioneNome,
              postalCode: centro.cap || '',
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

      {/* Hero */}
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
              <li>
                <Link
                  href={`/centri-cinofili/${regioneSlug}/`}
                  className="hover:text-[color:var(--ds-gray-900)]"
                >
                  {regioneNome}
                </Link>
              </li>
              <li aria-hidden>›</li>
              <li className="text-[color:var(--ds-gray-900)] font-medium">
                {provinciaNome} ({provinciaSigla})
              </li>
            </ol>
          </nav>

          <div className="flex items-center gap-2 mb-5">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--ds-verified)]" />
            <span className="text-eyebrow">
              Provincia · {regioneNome}
            </span>
          </div>

          <h1 className="text-display max-w-3xl">
            Centri cinofili a {provinciaNome}.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[color:var(--ds-gray-600)]">
            {centri.length} {centri.length === 1 ? 'centro registrato' : 'centri registrati'} in provincia di{' '}
            {provinciaNome} ({provinciaSigla}). Filtra per metodo, disciplina o infrastruttura
            per trovare il centro più adatto al tuo cane.
          </p>

          <div className="mt-7 flex items-center gap-3 flex-wrap">
            <Link
              href={`/?regione=${regioneSlug}&provincia=${provinciaSlug}`}
              className="btn-primary"
            >
              <span aria-hidden>⌘</span>
              Apri filtri avanzati
            </Link>
            <Link
              href={`/centri-cinofili/${regioneSlug}/`}
              className="btn-secondary"
            >
              ← Tutte le province di {regioneNome}
            </Link>
          </div>
        </div>
      </section>

      {/* Results — riusa lo stesso componente della home per coerenza visiva */}
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex items-baseline justify-between mb-6">
          <div>
            <h2 className="text-h2">
              {centri.length}{" "}
              <span className="text-[color:var(--ds-gray-500)] font-normal">
                {centri.length === 1 ? "centro" : "centri"}
              </span>
            </h2>
            <p className="text-xs text-[color:var(--ds-gray-500)] mt-1 font-mono">
              recordset statico per {provinciaNome} ({provinciaSigla})
            </p>
          </div>
        </div>

        <ResultsGrid centri={centri} />
      </section>
    </>
  );
}