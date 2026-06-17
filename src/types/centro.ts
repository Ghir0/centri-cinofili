// ============================================================
// Tipi per la piattaforma centri cinofili
// ============================================================

export interface Regione {
  id: number
  nome: string
  slug: string
}

export interface Provincia {
  id: number
  nome: string
  slug: string
  sigla: string
  regione_id: number
}

export interface Metodologia {
  id: number
  nome: string
  slug: string
  descrizione?: string
}

export interface Disciplina {
  id: number
  nome: string
  slug: string
  descrizione?: string
}

export interface Infrastruttura {
  id: number
  nome: string
  slug: string
  icona?: string
}

export interface Affiliazione {
  id: number
  nome: string
  slug: string
  ente_ufficiale?: string
}

export interface SocialLinks {
  instagram?: string
  facebook?: string
  tiktok?: string
}

export interface Centro {
  id: number
  ragione_sociale: string
  brand_name: string | null
  slug: string
  indirizzo: string | null
  comune: string | null
  cap: string | null
  provincia_id: number | null
  coordinate_gps: { lat: number; lon: number } | null
  telefono: string | null
  email: string | null
  sito_web: string | null
  social_links: SocialLinks | null
  descrizione: string | null
  claim_status: 'unclaimed' | 'pending' | 'claimed'
  created_at: string
  updated_at: string
}

// Versione espansa con tutte le relazioni joinate
export interface CentroExpanded extends Centro {
  provincia?: Provincia | null
  regione?: Regione | null
  metodologie: Metodologia[]
  discipline: Disciplina[]
  infrastrutture: Infrastruttura[]
  affiliazioni: Affiliazione[]
  rating_medio: number | null
  num_recensioni: number
}

export interface Recensione {
  id: number
  centro_id: number
  user_id: string | null
  autore_nome: string
  rating: number
  testo: string | null
  data_visita: string | null
  created_at: string
}

export interface ClaimRequest {
  id: number
  centro_id: number
  user_id: string
  nome_proprietario: string
  email: string
  telefono?: string
  documento_url?: string
  status: 'pending' | 'approved' | 'rejected'
  note_admin?: string
  created_at: string
  updated_at: string
}

// ============================================================
// Tipi per le query di ricerca e filtri
// ============================================================

export interface CentriFilters {
  regione?: string
  provincia?: string
  metodologia?: string
  disciplina?: string
  infrastruttura?: string
  affiliazione?: string
  search?: string
}

export interface PaginatedResult<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
}
