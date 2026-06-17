import Link from 'next/link'
import type { Metadata } from 'next'
import { createStaticClient } from '@/lib/supabase/static'
import { notFound } from 'next/navigation'

export const dynamicParams = false

const METODOLOGIE_VALIDE: Record<string, string> = {
  'cognitivo-relazionale': 'Cognitivo-Relazionale',
  'gentile': 'Gentile',
  'tradizionale': 'Tradizionale/Utilitaristico',
  'non-specificato': 'Non Specificato',
}

export async function generateStaticParams() {
  const supabase = createStaticClient()
  const { data } = await supabase.from('metodologie').select('slug')
  if (!data) return []
  return data.map((m: { slug: string }) => ({ slug: m.slug }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const nome = METODOLOGIE_VALIDE[slug] ?? slug
  return {
    title: `Centri Cinofili ${nome} | Metodo ${nome}`,
    description: `Elenco dei centri cinofili italiani che adottano il metodo ${nome}. Scopri i migliori centri con approccio ${nome.toLowerCase()}.`,
  }
}

export default async function MetodologiaPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  if (!METODOLOGIE_VALIDE[slug]) notFound()

  const supabase = createStaticClient()
  const nomeMetodologia = METODOLOGIE_VALIDE[slug]

  const { data: centri } = await supabase
    .from('centri_metodologie')
    .select(`
      centro:centro_id(
        id, ragione_sociale, brand_name, slug, indirizzo, comune, cap,
        provincia:provincia_id(nome, slug, sigla)
      ),
      metodologia:metodologia_id(nome, slug)
    `)
    .eq('metodologia.slug', slug)
    .limit(100)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Centri Cinofili — Metodo ${nomeMetodologia}`,
    numberOfItems: centri?.length ?? 0,
    itemListElement: (centri ?? []).map((c: any, i: number) => ({
      '@type': 'ListItem',
      position: i + 1,
      item: {
        '@type': 'LocalBusiness',
        name: c.centro.brand_name || c.centro.ragione_sociale,
        url: `/centro/${c.centro.slug}`,
        address: c.centro.indirizzo ? {
          '@type': 'PostalAddress',
          streetAddress: c.centro.indirizzo,
          addressLocality: c.centro.comune,
        } : undefined,
      },
    })),
  }

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <nav className="text-sm text-gray-500 mb-4">
          <Link href="/" className="hover:text-blue-600">Home</Link> &rsaquo;{' '}
          <Link href="/centri-cinofili" className="hover:text-blue-600">Centri Cinofili</Link> &rsaquo;{' '}
          <span className="text-gray-800">Metodo {nomeMetodologia}</span>
        </nav>
        <h1 className="text-3xl font-bold mb-2">Centri Cinofili — Metodo {nomeMetodologia}</h1>
        <p className="text-gray-600 mb-6">
          {centri?.length ?? 0} centri che adottano l&apos;approccio {nomeMetodologia.toLowerCase()}.
        </p>
        {(!centri || centri.length === 0) ? (
          <p className="text-gray-400 italic">Nessun centro trovato per questa metodologia.</p>
        ) : (
          <ul className="space-y-3">
            {centri.map((c: any) => (
              <li key={c.centro.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <Link href={`/centro/${c.centro.slug}`} className="font-semibold text-lg text-blue-700 hover:underline">
                  {c.centro.brand_name || c.centro.ragione_sociale}
                </Link>
                <p className="text-sm text-gray-500">
                  {c.centro.indirizzo}{c.centro.comune ? `, ${c.centro.comune}` : ''}
                  {c.centro.provincia ? ` (${c.centro.provincia.sigla})` : ''}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}
