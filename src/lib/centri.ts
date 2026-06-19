import { createClient } from '@/lib/supabase/server'
import type { CentroExpanded, Metodologia, Disciplina, Infrastruttura, Affiliazione } from '@/types/centro'

/**
 * Parsa una stringa EWKB hex (PostGIS geography) in { lat, lon }.
 *
 * Formato EWKB little-endian:
 *   byte  0     : 0x01 (little-endian marker)
 *   bytes 1-4   : type uint32 (con SRID flag 0x20000000 se presente)
 *   bytes 5-8   : SRID uint32 (se SRID flag attivo)
 *   bytes 9-16  : lon double
 *   bytes 17-24 : lat double
 *
 * Universale (Node + browser), senza dipendenze.
 */
function parseWkbHex(hex: string): { lat: number; lon: number } | null {
  if (!hex || hex.length < 50) return null

  // Verifica little-endian marker (byte 0 = 0x01)
  if (hex.substring(0, 2) !== '01') return null

  // Type uint32 little-endian a byte 1-4 (8 hex chars)
  const typeHex = hex.substring(2, 10)
  // Little-endian uint32: byte 0 = hex[0:2], byte 1 = hex[2:4], ...
  const type =
    parseInt(typeHex.substring(6, 8), 16) * 0x1000000 +
    parseInt(typeHex.substring(4, 6), 16) * 0x10000 +
    parseInt(typeHex.substring(2, 4), 16) * 0x100 +
    parseInt(typeHex.substring(0, 2), 16)
  const hasSrid = (type & 0x20000000) !== 0

  // Coordinate partono dopo SRID header (se presente)
  const coordByteStart = hasSrid ? 9 : 5

  // Lon (8 byte) little-endian double
  const lon = hexToDoubleLE(hex.substring(coordByteStart * 2, (coordByteStart + 8) * 2))
  // Lat (8 byte)
  const lat = hexToDoubleLE(hex.substring((coordByteStart + 8) * 2, (coordByteStart + 16) * 2))

  if (!isFinite(lat) || !isFinite(lon)) return null
  return { lat, lon }
}

/** Converte 16 caratteri hex (8 byte little-endian) in double IEEE 754. */
function hexToDoubleLE(hex: string): number {
  if (hex.length !== 16) return NaN
  const bytes = new Uint8Array(8)
  for (let i = 0; i < 8; i++) {
    bytes[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16)
  }
  const view = new DataView(bytes.buffer)
  return view.getFloat64(0, true)
}

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

  // Normalizza coordinate da WKB/GeoJSON/WKT se presenti
  let coordinate_gps = null
  if (centro.coordinate_gps) {
    if (typeof centro.coordinate_gps === 'object' && 'coordinates' in centro.coordinate_gps) {
      // GeoJSON da PostgREST (richiede Accept: application/geo+json)
      const coords = (centro.coordinate_gps as any).coordinates
      coordinate_gps = { lat: coords[1], lon: coords[0] }
    } else if (typeof centro.coordinate_gps === 'object' && 'lat' in centro.coordinate_gps) {
      coordinate_gps = centro.coordinate_gps as any
    } else if (typeof centro.coordinate_gps === 'string') {
      // PostgREST default: EWKB hex string per PostGIS geography
      coordinate_gps = parseWkbHex(centro.coordinate_gps)
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

// ============================================================
// List / filter query — for homepage + directory pages
// ============================================================

export interface SearchFilters {
  q?: string
  regione?: string       // region slug
  provincia?: string     // provincia slug
  metodologie?: string[] // slugs
  discipline?: string[]  // slugs
  infrastrutture?: string[]
  affiliazioni?: string[]
  sort?: 'recent' | 'name' | 'rating'
}

export interface SearchResult {
  id: number
  slug: string
  ragione_sociale: string
  brand_name: string | null
  indirizzo: string | null
  comune: string | null
  cap: string | null
  provincia_sigla: string | null
  provincia_nome: string | null
  regione_nome: string | null
  regione_slug: string | null
  claimed: boolean
  rating_medio: number | null
  num_recensioni: number
  metodologie: { nome: string; slug: string }[]
  discipline: { nome: string; slug: string }[]
  infrastrutture: { nome: string; slug: string }[]
  affiliazioni: { nome: string; slug: string }[]
}

/**
 * Search centri with optional filters.
 * Returns lightweight rows suitable for result cards.
 */
export async function searchCentri(filters: SearchFilters): Promise<SearchResult[]> {
  const supabase = await createClient()

  // Resolve regione slug -> id for filter
  let regioneId: number | null = null
  if (filters.regione) {
    const { data } = await supabase.from('regioni').select('id').eq('slug', filters.regione).single()
    regioneId = data?.id ?? null
  }

  // Resolve provincia slug -> id for filter
  let provinciaId: number | null = null
  if (filters.provincia) {
    const { data } = await supabase.from('province').select('id').eq('slug', filters.provincia).single()
    provinciaId = data?.id ?? null
  }

  // Resolve tassonomie slugs -> ids
  async function slugToIds(table: string, slugs: string[] | undefined): Promise<number[]> {
    if (!slugs || slugs.length === 0) return []
    const { data } = await supabase.from(table).select('id, slug').in('slug', slugs)
    return (data || []).map((r) => r.id)
  }

  const [metodologieIds, disciplineIds, infrastruttureIds, affiliazioniIds] = await Promise.all([
    slugToIds('metodologie', filters.metodologie),
    slugToIds('discipline', filters.discipline),
    slugToIds('infrastrutture', filters.infrastrutture),
    slugToIds('affiliazioni', filters.affiliazioni),
  ])

  // If user selected tassonomie, find candidate centro_ids via junction tables
  async function centriWithAll(table: string, fk: string, ids: number[]): Promise<Set<number> | null> {
    if (ids.length === 0) return null
    const { data } = await supabase.from(table).select('centro_id').in(fk, ids)
    const counts = new Map<number, number>()
    for (const r of data || []) {
      counts.set(r.centro_id, (counts.get(r.centro_id) || 0) + 1)
    }
    // Centri che hanno TUTTE le ids selezionate
    const result = new Set<number>()
    for (const [cid, n] of counts.entries()) {
      if (n === ids.length) result.add(cid)
    }
    return result
  }

  const [
    metodCentri,
    discCentri,
    infraCentri,
    affilCentri,
  ] = await Promise.all([
    centriWithAll('centri_metodologie', 'metodologia_id', metodologieIds),
    centriWithAll('centri_discipline', 'disciplina_id', disciplineIds),
    centriWithAll('centri_infrastrutture', 'infrastruttura_id', infrastruttureIds),
    centriWithAll('centri_affiliazioni', 'affiliazione_id', affiliazioniIds),
  ])

  // Intersect all junction results
  let allowedCentriIds: Set<number> | null = null
  for (const set of [metodCentri, discCentri, infraCentri, affilCentri]) {
    if (!set) continue
    if (allowedCentriIds === null) {
      allowedCentriIds = new Set(set)
    } else {
      const next = new Set<number>()
      for (const id of set) if (allowedCentriIds.has(id)) next.add(id)
      allowedCentriIds = next
    }
  }

  // Build base query
  let query = supabase
    .from('centri')
    .select(`
      id, slug, ragione_sociale, brand_name,
      indirizzo, comune, cap,
      claimed_by, claim_status,
      provincia:provincia_id(id, nome, slug, sigla,
        regione:regione_id(id, nome, slug)
      )
    `)
    .order('ragione_sociale', { ascending: true })
    .limit(200)

  if (regioneId) {
    query = query.eq('provincia.regione_id', regioneId)
  }
  if (provinciaId) {
    query = query.eq('provincia_id', provinciaId)
  }
  if (filters.q) {
    const q = filters.q.trim()
    // Search across brand_name, ragione_sociale, comune
    query = query.or(`brand_name.ilike.%${q}%,ragione_sociale.ilike.%${q}%,comune.ilike.%${q}%`)
  }

  const { data: rows, error } = await query
  if (error || !rows) return []

  // Filter by allowed ids
  let results = rows
  if (allowedCentriIds !== null) {
    results = results.filter((r) => allowedCentriIds!.has(r.id))
  }

  // Fetch junction data for filtered set (in one query per type, then map)
  const ids = results.map((r) => r.id)
  if (ids.length === 0) return []

  const [metodRows, discRows, infraRows, affilRows, recStatsRows] = await Promise.all([
    supabase.from('centri_metodologie').select('centro_id, metodologia:metodologia_id(nome, slug)').in('centro_id', ids),
    supabase.from('centri_discipline').select('centro_id, disciplina:disciplina_id(nome, slug)').in('centro_id', ids),
    supabase.from('centri_infrastrutture').select('centro_id, infrastruttura:infrastruttura_id(nome, slug)').in('centro_id', ids),
    supabase.from('centri_affiliazioni').select('centro_id, affiliazione:affiliazione_id(nome, slug)').in('centro_id', ids),
    supabase.from('recensioni').select('centro_id, rating').in('centro_id', ids),
  ])

  // Build lookup maps
  const metodMap = new Map<number, { nome: string; slug: string }[]>()
  for (const r of metodRows.data || []) {
    const list = metodMap.get(r.centro_id) || []
    if (r.metodologia) list.push(r.metodologia as any)
    metodMap.set(r.centro_id, list)
  }
  const discMap = new Map<number, { nome: string; slug: string }[]>()
  for (const r of discRows.data || []) {
    const list = discMap.get(r.centro_id) || []
    if (r.disciplina) list.push(r.disciplina as any)
    discMap.set(r.centro_id, list)
  }
  const infraMap = new Map<number, { nome: string; slug: string }[]>()
  for (const r of infraRows.data || []) {
    const list = infraMap.get(r.centro_id) || []
    if (r.infrastruttura) list.push(r.infrastruttura as any)
    infraMap.set(r.centro_id, list)
  }
  const affilMap = new Map<number, { nome: string; slug: string }[]>()
  for (const r of affilRows.data || []) {
    const list = affilMap.get(r.centro_id) || []
    if (r.affiliazione) list.push(r.affiliazione as any)
    affilMap.set(r.centro_id, list)
  }
  const ratingMap = new Map<number, { sum: number; n: number }>()
  for (const r of recStatsRows.data || []) {
    const cur = ratingMap.get(r.centro_id) || { sum: 0, n: 0 }
    cur.sum += r.rating
    cur.n += 1
    ratingMap.set(r.centro_id, cur)
  }

  // Assemble
  const out: SearchResult[] = results.map((r) => {
    const rec = ratingMap.get(r.id)
    return {
      id: r.id,
      slug: r.slug,
      ragione_sociale: r.ragione_sociale,
      brand_name: r.brand_name,
      indirizzo: r.indirizzo,
      comune: r.comune,
      cap: r.cap,
      provincia_sigla: (r as any).provincia?.sigla ?? null,
      provincia_nome: (r as any).provincia?.nome ?? null,
      regione_nome: (r as any).provincia?.regione?.nome ?? null,
      regione_slug: (r as any).provincia?.regione?.slug ?? null,
      claimed: !!r.claimed_by,
      rating_medio: rec && rec.n > 0 ? Math.round((rec.sum / rec.n) * 10) / 10 : null,
      num_recensioni: rec?.n ?? 0,
      metodologie: metodMap.get(r.id) || [],
      discipline: discMap.get(r.id) || [],
      infrastrutture: infraMap.get(r.id) || [],
      affiliazioni: affilMap.get(r.id) || [],
    }
  })

  // Sort
  if (filters.sort === 'rating') {
    out.sort((a, b) => (b.rating_medio ?? 0) - (a.rating_medio ?? 0))
  } else if (filters.sort === 'recent') {
    out.reverse()
  }
  // Default: alphabetical by brand_name / ragione_sociale

  return out
}

/**
 * Fetch all tassonomie for filter sidebar (cached server-side).
 */
export async function getTassonomieForFilters() {
  const supabase = await createClient()
  const [metodologie, discipline, infrastrutture, affiliazioni, regioni] = await Promise.all([
    supabase.from('metodologie').select('id, nome, slug').order('nome'),
    supabase.from('discipline').select('id, nome, slug').order('nome'),
    supabase.from('infrastrutture').select('id, nome, slug').order('nome'),
    supabase.from('affiliazioni').select('id, nome, slug').order('nome'),
    supabase.from('regioni').select('id, nome, slug').order('nome'),
  ])
  return {
    metodologie: metodologie.data || [],
    discipline: discipline.data || [],
    infrastrutture: infrastrutture.data || [],
    affiliazioni: affiliazioni.data || [],
    regioni: regioni.data || [],
  }
}

export async function getProvinceByRegione(regioneSlug: string) {
  const supabase = await createClient()
  const { data: regione } = await supabase
    .from('regioni')
    .select('id')
    .eq('slug', regioneSlug)
    .single()
  if (!regione) return []
  const { data: province } = await supabase
    .from('province')
    .select('id, nome, slug, sigla')
    .eq('regione_id', regione.id)
    .order('nome')
  return province || []
}