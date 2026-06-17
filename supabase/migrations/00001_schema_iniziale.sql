-- Migration 00001: Schema iniziale piattaforma centri cinofili
-- Richiede estensione PostGIS

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- TABELLE DI LOOKUP GEOGRAFICHE
-- ============================================================

CREATE TABLE regioni (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE province (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  sigla CHAR(2) NOT NULL,
  regione_id INTEGER NOT NULL REFERENCES regioni(id)
);

-- ============================================================
-- TABELLE DI LOOKUP TASSONOMIA CINOFILA
-- ============================================================

CREATE TABLE metodologie (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  descrizione TEXT
);

CREATE TABLE discipline (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  descrizione TEXT
);

CREATE TABLE infrastrutture (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  icona VARCHAR(50)
);

CREATE TABLE affiliazioni (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  ente_ufficiale VARCHAR(200)
);

-- ============================================================
-- TABELLA PRINCIPALE CENTRI
-- ============================================================

CREATE TABLE centri (
  id SERIAL PRIMARY KEY,
  ragione_sociale VARCHAR(300) NOT NULL,
  brand_name VARCHAR(300),
  slug VARCHAR(300) NOT NULL UNIQUE,
  indirizzo VARCHAR(500),
  comune VARCHAR(200),
  cap VARCHAR(10),
  provincia_id INTEGER REFERENCES province(id),
  coordinate_gps GEOGRAPHY(POINT, 4326),
  telefono VARCHAR(50),
  email VARCHAR(200),
  sito_web VARCHAR(500),
  social_links JSONB DEFAULT '{}',
  descrizione TEXT,
  osm_id VARCHAR(50),
  osm_type VARCHAR(20),
  claimed_by UUID REFERENCES auth.users(id),
  claim_status VARCHAR(20) DEFAULT 'unclaimed' CHECK (claim_status IN ('unclaimed', 'pending', 'claimed')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indici su centri
CREATE INDEX idx_centri_provincia ON centri(provincia_id);
CREATE INDEX idx_centri_claim_status ON centri(claim_status);
CREATE INDEX idx_centri_slug ON centri(slug);
CREATE INDEX idx_centri_coordinate ON centri USING GIST (coordinate_gps);
CREATE INDEX idx_centri_fulltext ON centri USING GIN (
  to_tsvector('italian', COALESCE(ragione_sociale, '') || ' ' || COALESCE(brand_name, ''))
);

-- ============================================================
-- JUNCTION TABLES (MANY-TO-MANY)
-- ============================================================

CREATE TABLE centri_metodologie (
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  metodologia_id INTEGER NOT NULL REFERENCES metodologie(id) ON DELETE CASCADE,
  PRIMARY KEY (centro_id, metodologia_id)
);

CREATE TABLE centri_discipline (
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  disciplina_id INTEGER NOT NULL REFERENCES discipline(id) ON DELETE CASCADE,
  PRIMARY KEY (centro_id, disciplina_id)
);

CREATE TABLE centri_infrastrutture (
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  infrastruttura_id INTEGER NOT NULL REFERENCES infrastrutture(id) ON DELETE CASCADE,
  PRIMARY KEY (centro_id, infrastruttura_id)
);

CREATE TABLE centri_affiliazioni (
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  affiliazione_id INTEGER NOT NULL REFERENCES affiliazioni(id) ON DELETE CASCADE,
  PRIMARY KEY (centro_id, affiliazione_id)
);

-- ============================================================
-- RECENSIONI
-- ============================================================

CREATE TABLE recensioni (
  id SERIAL PRIMARY KEY,
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id),
  autore_nome VARCHAR(200) NOT NULL,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  testo TEXT,
  data_visita DATE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_recensioni_centro ON recensioni(centro_id);

-- ============================================================
-- CLAIM REQUESTS
-- ============================================================

CREATE TABLE claim_requests (
  id SERIAL PRIMARY KEY,
  centro_id INTEGER NOT NULL REFERENCES centri(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  nome_proprietario VARCHAR(200) NOT NULL,
  email VARCHAR(200) NOT NULL,
  telefono VARCHAR(50),
  documento_url TEXT,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  note_admin TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_claim_requests_centro ON claim_requests(centro_id);
CREATE INDEX idx_claim_requests_status ON claim_requests(status);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE centri ENABLE ROW LEVEL SECURITY;
ALTER TABLE recensioni ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE metodologie ENABLE ROW LEVEL SECURITY;
ALTER TABLE discipline ENABLE ROW LEVEL SECURITY;
ALTER TABLE infrastrutture ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliazioni ENABLE ROW LEVEL SECURITY;
ALTER TABLE regioni ENABLE ROW LEVEL SECURITY;
ALTER TABLE province ENABLE ROW LEVEL SECURITY;

-- Lookup tables: SELECT pubblico, modifiche solo service_role
CREATE POLICY "select_lookup" ON metodologie FOR SELECT USING (true);
CREATE POLICY "select_lookup" ON discipline FOR SELECT USING (true);
CREATE POLICY "select_lookup" ON infrastrutture FOR SELECT USING (true);
CREATE POLICY "select_lookup" ON affiliazioni FOR SELECT USING (true);
CREATE POLICY "select_lookup" ON regioni FOR SELECT USING (true);
CREATE POLICY "select_lookup" ON province FOR SELECT USING (true);

-- Centri: SELECT pubblica, UPDATE solo proprietario
CREATE POLICY "select_centri" ON centri FOR SELECT USING (true);
CREATE POLICY "update_centri_proprietario" ON centri
  FOR UPDATE USING (claimed_by = auth.uid())
  WITH CHECK (claimed_by = auth.uid());

-- Recensioni: SELECT pubblica, INSERT autenticati
CREATE POLICY "select_recensioni" ON recensioni FOR SELECT USING (true);
CREATE POLICY "insert_recensioni" ON recensioni FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Claim requests: SELECT/INSERT per autenticati
CREATE POLICY "select_claim_requests" ON claim_requests FOR SELECT
  USING (auth.role() = 'authenticated' AND user_id = auth.uid());
CREATE POLICY "insert_claim_requests" ON claim_requests FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- ============================================================
-- FUNZIONE TRIGGER PER updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_centri
  BEFORE UPDATE ON centri
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_claim_requests
  BEFORE UPDATE ON claim_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
