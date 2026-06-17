import { createClient } from '@/lib/supabase/server'
import type { CentroExpanded } from '@/types/centro'

export async function getCentroBySlug(slug: string): Promise<CentroExpanded | null> {
  const supabase = await createClient()

  const { data: centro, error } = await supabase
    .from('centri')
    .select(`
      *,
      provincia:provincia_id(*,
        regione:regione_id(*)
      ),
      metodologie:centri_metodologie(
        metodologia:metodologia_id(*)
      ),
      discipline:centri_discipline(
        disciplina:disciplina_id(*)
      ),
      infrastrutture:centri_infrastrutture(
        infrastruttura:infrastruttura_id(*)
      ),
      affiliazioni:centri_affiliazioni(
        affiliazione:affiliazione_id(*)
      )
    `)
    .eq('slug', slug)
    .single()

  if (error || !centro) return null

  // Costruisci rating da recensioni
  const { data: recStats, error: recError } = await supabase
    .from('recensioni')
    .select('rating', { count: 'exact' })
    .eq('centro_id', centro.id)

  let rating_medio: number | null = null
  let num_recensioni = 0

  if (!recError && recStats) {
    num_recensioni = recStats.length
    if (num_recensioni > 0) {
      const sum = recStats.reduce((acc, r) => acc + r.rating, 0)
      rating_medio = Math.round((sum / num_recensioni) * 10) / 10
    }
  }

  // Estrai regione dalla provincia
  const regione = centro.provincia?.regione ?? null
  const provincia = centro.provincia
    ? { id: centro.provincia.id, nome: centro.provincia.nome, slug: centro.provincia.slug, sigla: centro.provincia.sigla, regione_id: centro.provincia.regione_id }
    : null

  // Normalizza coordinate da WKB/GeoJSON se presenti
  let coordinate_gps = null
  if (centro.coordinate_gps) {
    if (typeof centro.coordinate_gps === 'object' && 'coordinates' in centro.coordinate_gps) {
      // GeoJSON format
      const coords = (centro.coordinate_gps as any).coordinates
      coordinate_gps = { lat: coords[1], lon: coords[0] }
    } else if (typeof centro.coordinate_gps === 'object' && 'lat' in centro.coordinate_gps) {
      coordinate_gps = centro.coordinate_gps as any
    }
  }

  return {
    ...centro,
    provincia,
    regione,
    coordinate_gps,
    rating_medio,
    num_recensioni,
    metodologie: (centro.metodologie || []).map((m: any) => m.metodologia || m),
    discipline: (centro.discipline || []).map((d: any) => d.disciplina || d),
    infrastrutture: (centro.infrastrutture || []).map((i: any) => i.infrastruttura || i),
    affiliazioni: (centro.affiliazioni || []).map((a: any) => a.affiliazione || a),
  } as CentroExpanded
}
