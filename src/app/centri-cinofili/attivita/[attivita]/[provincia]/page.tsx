import Link from 'next/link'
import type { Metadata } from 'next'
import { createStaticClient } from '@/lib/supabase/static'
import { notFound } from 'next/navigation'

export const dynamicParams = false

const ATTIVITA_SLUG_MAP: Record<string, string> = {
  'agility-dog': 'Agility Dog',
  'rally-o': 'Rally-O',
  'hoopers': 'Hoopers',
  'nosework': 'Nosework',
  'propriocezione': 'Propriocezione / Mobilita',
  'socializzazione': 'Classi di Socializzazione',
  'recupero-comportamentale': 'Recupero Comportamentale',
  'educazione-base': 'Educazione Base Cuccioli',
  'campo-coperto': 'Campo Coperto',
  'campo-recintato': 'Campo Recintato',
  'piscina': 'Piscina Cinofila',
  'asilo-diurno': 'Asilo Diurno',
}

export async function generateStaticParams() {
  const supabase = createStaticClient()
  const { data: province } = await supabase.from('province').select('slug')
  const { data: discipline } = await supabase.from('discipline').select('slug')
  const { data: infrastrutture } = await supabase.from('infrastrutture').select('slug')
  const params: { provincia: string; attivita: string }[] = []
  const slugs = [...(discipline || []).map((d: {slug:string}) => d.slug), ...(infrastrutture || []).map((i: {slug:string}) => i.slug)]
  for (const p of (province || [])) {
    for (const s of slugs) {
      params.push({ provincia: p.slug, attivita: s })
    }
  }
  return params
}

export async function generateMetadata({ params }: { params: Promise<{ provincia: string; attivita: string }> }): Promise<Metadata> {
  const { provincia, attivita } = await params
  const nome = ATTIVITA_SLUG_MAP[attivita] || attivita
  const provDisplay = provincia.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
  return { title: `${nome} a ${provDisplay} | Centri Cinofili`, description: `Trova i migliori centri cinofili a ${provDisplay} specializzati in ${nome}.` }
}

export default async function ProvinciaAttivitaPage({ params }: { params: Promise<{ provincia: string; attivita: string }> }) {
  const { provincia, attivita } = await params
  const nome = ATTIVITA_SLUG_MAP[attivita]
  if (!nome) notFound()
  const supabase = createStaticClient()
  const { data: provData } = await supabase.from('province').select('nome, slug, sigla, regione:regione_id(nome, slug)').eq('slug', provincia).single()
  if (!provData) notFound()
  const { data: result } = await supabase.from('centri').select('id, ragione_sociale, brand_name, slug, indirizzo, comune, cap').eq('provincia_id', (await supabase.from('province').select('id').eq('slug', provincia).single()).data?.id).limit(50)
  const provDisplay = provData.nome
  return (<div className="max-w-4xl mx-auto px-4 py-8"><nav className="text-sm text-gray-500 mb-4"><Link href="/" className="hover:text-blue-600">Home</Link> &rsaquo; <Link href="/centri-cinofili" className="hover:text-blue-600">Centri Cinofili</Link> &rsaquo; <span className="text-gray-800">{nome} a {provDisplay}</span></nav><h1 className="text-3xl font-bold mb-2">{nome} a {provDisplay}</h1><p className="text-gray-600 mb-6">{(result || []).length} centri in provincia di {provDisplay}.</p>{(result || []).length === 0 ? <p className="text-gray-400 italic">Nessun centro trovato.</p> : <ul className="space-y-3">{(result || []).map((c: any) => (<li key={c.id} className="border rounded-lg p-4"><Link href={`/centro/${c.slug}`} className="font-semibold text-blue-700 hover:underline">{c.brand_name || c.ragione_sociale}</Link><p className="text-sm text-gray-500">{c.indirizzo}{c.comune ? `, ${c.comune}` : ''}</p></li>))}</ul>}</div>)
}
