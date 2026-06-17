import type { Metadata } from 'next'
import type { CentroExpanded } from '@/types/centro'
import { notFound } from 'next/navigation'
import { getCentroBySlug } from '@/lib/centri'
import { createStaticClient } from '@/lib/supabase/static'
import CentroDetail from '@/components/CentroDetail'

export const dynamicParams = false

export async function generateStaticParams() {
  const supabase = createStaticClient()
  const { data, error } = await supabase.from('centri').select('slug')
  if (error || !data) return []
  return data.map((c: { slug: string }) => ({ slug: c.slug }))
}

function buildJsonLd(centro: CentroExpanded): Record<string, unknown> {
  const displayName = centro.brand_name || centro.ragione_sociale

  const knowsAbout = [
    ...centro.metodologie.map((m) => m.nome),
    ...centro.discipline.map((d) => d.nome),
  ]

  const amenityFeature = centro.infrastrutture.map((i) => ({
    '@type': 'LocationFeatureSpecification',
    name: i.nome,
    value: true,
  }))

  return {
    '@context': 'https://schema.org',
    '@type': 'DogTrainer',
    name: displayName,
    description: centro.descrizione ?? undefined,
    url: `https://centri-cinofili.it/centro/${centro.slug}`,
    telephone: centro.telefono ?? undefined,
    email: centro.email ?? undefined,
    knowsAbout: knowsAbout.length > 0 ? knowsAbout : undefined,
    amenityFeature: amenityFeature.length > 0 ? amenityFeature : undefined,
    ...(centro.indirizzo || centro.comune
      ? {
          address: {
            '@type': 'PostalAddress',
            streetAddress: centro.indirizzo ?? undefined,
            addressLocality: centro.comune ?? undefined,
            postalCode: centro.cap ?? undefined,
            addressRegion: centro.regione?.nome ?? centro.provincia?.sigla ?? undefined,
          },
        }
      : {}),
    ...(centro.coordinate_gps
      ? {
          geo: {
            '@type': 'GeoCoordinates',
            latitude: centro.coordinate_gps.lat,
            longitude: centro.coordinate_gps.lon,
          },
        }
      : {}),
    ...(centro.provincia
      ? {
          areaServed: {
            '@type': 'State',
            name: centro.provincia.nome,
          },
        }
      : {}),
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const centro = await getCentroBySlug(slug)
  if (!centro) return { title: 'Centro non trovato' }
  const displayName = centro.brand_name || centro.ragione_sociale
  return {
    title: `${displayName} | Centri Cinofili`,
    description: centro.descrizione ?? `${displayName} - Centro cinofilo a ${centro.comune ?? 'Italia'}`,
  }
}

export default async function CentroPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const centro = await getCentroBySlug(slug)

  if (!centro) notFound()

  const jsonLd = buildJsonLd(centro)

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CentroDetail centro={centro} />
    </>
  )
}
