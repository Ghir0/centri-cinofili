-- Migration 00002: Seed tabelle di lookup

-- REGIONI
INSERT INTO regioni (nome, slug) VALUES
  ('Abruzzo', 'abruzzo'), ('Basilicata', 'basilicata'), ('Calabria', 'calabria'),
  ('Campania', 'campania'), ('Emilia-Romagna', 'emilia-romagna'),
  ('Friuli-Venezia Giulia', 'friuli-venezia-giulia'), ('Lazio', 'lazio'),
  ('Liguria', 'liguria'), ('Lombardia', 'lombardia'), ('Marche', 'marche'),
  ('Molise', 'molise'), ('Piemonte', 'piemonte'), ('Puglia', 'puglia'),
  ('Sardegna', 'sardegna'), ('Sicilia', 'sicilia'), ('Toscana', 'toscana'),
  ('Trentino-Alto Adige', 'trentino-alto-adige'), ('Umbria', 'umbria'),
  ('Valle d''Aosta', 'valle-d-aosta'), ('Veneto', 'veneto')
ON CONFLICT DO NOTHING;

-- PROVINCE (abbreviate: solo capoluoghi + le più rilevanti)
INSERT INTO province (nome, slug, sigla, regione_id) VALUES
  ('Agrigento', 'agrigento', 'AG', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Alessandria', 'alessandria', 'AL', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Ancona', 'ancona', 'AN', (SELECT id FROM regioni WHERE slug='marche')),
  ('Aosta', 'aosta', 'AO', (SELECT id FROM regioni WHERE slug='valle-d-aosta')),
  ('Arezzo', 'arezzo', 'AR', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Ascoli Piceno', 'ascoli-piceno', 'AP', (SELECT id FROM regioni WHERE slug='marche')),
  ('Asti', 'asti', 'AT', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Avellino', 'avellino', 'AV', (SELECT id FROM regioni WHERE slug='campania')),
  ('Bari', 'bari', 'BA', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Barletta-Andria-Trani', 'barletta-andria-trani', 'BT', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Belluno', 'belluno', 'BL', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Benevento', 'benevento', 'BN', (SELECT id FROM regioni WHERE slug='campania')),
  ('Bergamo', 'bergamo', 'BG', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Biella', 'biella', 'BI', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Bologna', 'bologna', 'BO', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Bolzano', 'bolzano', 'BZ', (SELECT id FROM regioni WHERE slug='trentino-alto-adige')),
  ('Brescia', 'brescia', 'BS', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Brindisi', 'brindisi', 'BR', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Cagliari', 'cagliari', 'CA', (SELECT id FROM regioni WHERE slug='sardegna')),
  ('Caltanissetta', 'caltanissetta', 'CL', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Campobasso', 'campobasso', 'CB', (SELECT id FROM regioni WHERE slug='molise')),
  ('Caserta', 'caserta', 'CE', (SELECT id FROM regioni WHERE slug='campania')),
  ('Catania', 'catania', 'CT', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Catanzaro', 'catanzaro', 'CZ', (SELECT id FROM regioni WHERE slug='calabria')),
  ('Chieti', 'chieti', 'CH', (SELECT id FROM regioni WHERE slug='abruzzo')),
  ('Como', 'como', 'CO', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Cosenza', 'cosenza', 'CS', (SELECT id FROM regioni WHERE slug='calabria')),
  ('Cremona', 'cremona', 'CR', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Crotone', 'crotone', 'KR', (SELECT id FROM regioni WHERE slug='calabria')),
  ('Cuneo', 'cuneo', 'CN', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Enna', 'enna', 'EN', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Fermo', 'fermo', 'FM', (SELECT id FROM regioni WHERE slug='marche')),
  ('Ferrara', 'ferrara', 'FE', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Firenze', 'firenze', 'FI', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Foggia', 'foggia', 'FG', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Forli-Cesena', 'forli-cesena', 'FC', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Frosinone', 'frosinone', 'FR', (SELECT id FROM regioni WHERE slug='lazio')),
  ('Genova', 'genova', 'GE', (SELECT id FROM regioni WHERE slug='liguria')),
  ('Gorizia', 'gorizia', 'GO', (SELECT id FROM regioni WHERE slug='friuli-venezia-giulia')),
  ('Grosseto', 'grosseto', 'GR', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Imperia', 'imperia', 'IM', (SELECT id FROM regioni WHERE slug='liguria')),
  ('Isernia', 'isernia', 'IS', (SELECT id FROM regioni WHERE slug='molise')),
  ('L''Aquila', 'l-aquila', 'AQ', (SELECT id FROM regioni WHERE slug='abruzzo')),
  ('La Spezia', 'la-spezia', 'SP', (SELECT id FROM regioni WHERE slug='liguria')),
  ('Latina', 'latina', 'LT', (SELECT id FROM regioni WHERE slug='lazio')),
  ('Lecce', 'lecce', 'LE', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Lecco', 'lecco', 'LC', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Livorno', 'livorno', 'LI', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Lodi', 'lodi', 'LO', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Lucca', 'lucca', 'LU', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Macerata', 'macerata', 'MC', (SELECT id FROM regioni WHERE slug='marche')),
  ('Mantova', 'mantova', 'MN', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Massa-Carrara', 'massa-carrara', 'MS', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Matera', 'matera', 'MT', (SELECT id FROM regioni WHERE slug='basilicata')),
  ('Messina', 'messina', 'ME', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Milano', 'milano', 'MI', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Modena', 'modena', 'MO', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Monza-Brianza', 'monza-brianza', 'MB', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Napoli', 'napoli', 'NA', (SELECT id FROM regioni WHERE slug='campania')),
  ('Novara', 'novara', 'NO', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Nuoro', 'nuoro', 'NU', (SELECT id FROM regioni WHERE slug='sardegna')),
  ('Oristano', 'oristano', 'OR', (SELECT id FROM regioni WHERE slug='sardegna')),
  ('Padova', 'padova', 'PD', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Palermo', 'palermo', 'PA', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Parma', 'parma', 'PR', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Pavia', 'pavia', 'PV', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Perugia', 'perugia', 'PG', (SELECT id FROM regioni WHERE slug='umbria')),
  ('Pesaro-Urbino', 'pesaro-urbino', 'PU', (SELECT id FROM regioni WHERE slug='marche')),
  ('Pescara', 'pescara', 'PE', (SELECT id FROM regioni WHERE slug='abruzzo')),
  ('Piacenza', 'piacenza', 'PC', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Pisa', 'pisa', 'PI', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Pistoia', 'pistoia', 'PT', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Pordenone', 'pordenone', 'PN', (SELECT id FROM regioni WHERE slug='friuli-venezia-giulia')),
  ('Potenza', 'potenza', 'PZ', (SELECT id FROM regioni WHERE slug='basilicata')),
  ('Prato', 'prato', 'PO', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Ragusa', 'ragusa', 'RG', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Ravenna', 'ravenna', 'RA', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Reggio Calabria', 'reggio-calabria', 'RC', (SELECT id FROM regioni WHERE slug='calabria')),
  ('Reggio Emilia', 'reggio-emilia', 'RE', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Rieti', 'rieti', 'RI', (SELECT id FROM regioni WHERE slug='lazio')),
  ('Rimini', 'rimini', 'RN', (SELECT id FROM regioni WHERE slug='emilia-romagna')),
  ('Roma', 'roma', 'RM', (SELECT id FROM regioni WHERE slug='lazio')),
  ('Rovigo', 'rovigo', 'RO', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Salerno', 'salerno', 'SA', (SELECT id FROM regioni WHERE slug='campania')),
  ('Sassari', 'sassari', 'SS', (SELECT id FROM regioni WHERE slug='sardegna')),
  ('Savona', 'savona', 'SV', (SELECT id FROM regioni WHERE slug='liguria')),
  ('Siena', 'siena', 'SI', (SELECT id FROM regioni WHERE slug='toscana')),
  ('Siracusa', 'siracusa', 'SR', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Sondrio', 'sondrio', 'SO', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Sud Sardegna', 'sud-sardegna', 'SU', (SELECT id FROM regioni WHERE slug='sardegna')),
  ('Taranto', 'taranto', 'TA', (SELECT id FROM regioni WHERE slug='puglia')),
  ('Teramo', 'teramo', 'TE', (SELECT id FROM regioni WHERE slug='abruzzo')),
  ('Terni', 'terni', 'TR', (SELECT id FROM regioni WHERE slug='umbria')),
  ('Torino', 'torino', 'TO', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Trapani', 'trapani', 'TP', (SELECT id FROM regioni WHERE slug='sicilia')),
  ('Trento', 'trento', 'TN', (SELECT id FROM regioni WHERE slug='trentino-alto-adige')),
  ('Treviso', 'treviso', 'TV', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Trieste', 'trieste', 'TS', (SELECT id FROM regioni WHERE slug='friuli-venezia-giulia')),
  ('Udine', 'udine', 'UD', (SELECT id FROM regioni WHERE slug='friuli-venezia-giulia')),
  ('Varese', 'varese', 'VA', (SELECT id FROM regioni WHERE slug='lombardia')),
  ('Venezia', 'venezia', 'VE', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Verbano-Cusio-Ossola', 'verbano-cusio-ossola', 'VB', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Vercelli', 'vercelli', 'VC', (SELECT id FROM regioni WHERE slug='piemonte')),
  ('Verona', 'verona', 'VR', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Vibo Valentia', 'vibo-valentia', 'VV', (SELECT id FROM regioni WHERE slug='calabria')),
  ('Vicenza', 'vicenza', 'VI', (SELECT id FROM regioni WHERE slug='veneto')),
  ('Viterbo', 'viterbo', 'VT', (SELECT id FROM regioni WHERE slug='lazio'))
ON CONFLICT (slug) DO NOTHING;

-- METODOLOGIE EDUCATIVE
INSERT INTO metodologie (nome, slug, descrizione) VALUES
  ('Cognitivo-Relazionale', 'cognitivo-relazionale', 'Approccio basato sulla relazione uomo-cane come fondamento dell''apprendimento, con focus sulle capacità cognitive del cane'),
  ('Gentile', 'gentile', 'Metodo basato sul rinforzo positivo, senza coercizione, nel rispetto del benessere emotivo del cane'),
  ('Tradizionale/Utilitaristico', 'tradizionale', 'Approccio classico focalizzato su obbedienza e comandi, tipicamente con correzioni fisiche o strumentali'),
  ('Non Specificato', 'non-specificato', 'Metodologia non dichiarata o non classificabile')
ON CONFLICT (slug) DO NOTHING;

-- DISCIPLINE
INSERT INTO discipline (nome, slug, descrizione) VALUES
  ('Agility Dog', 'agility-dog', 'Sport cinofilo basato su percorso a ostacoli da completare nel minor tempo'),
  ('Rally-O', 'rally-o', 'Rally Obedience: disciplina che combina elementi di obbedienza con un percorso segnalato'),
  ('Hoopers', 'hoopers', 'Disciplina con ostacoli (hoop, barili) a basso impatto articolare, ideale per cani di ogni età'),
  ('Nosework / Ricerca Olfattiva', 'nosework', 'Attività basata sulla ricerca di odori target, stimola le capacità olfattive naturali'),
  ('Propriocezione / Mobilità', 'propriocezione', 'Esercizi per consapevolezza corporea, equilibrio e mobilità articolare'),
  ('Classi di Socializzazione', 'socializzazione', 'Incontri strutturati per lo sviluppo delle competenze sociali intra e interspecifiche'),
  ('Recupero Comportamentale', 'recupero-comportamentale', 'Percorso di riabilitazione per cani con problemi comportamentali (aggressività, paure, ansie)'),
  ('Educazione Base Cuccioli', 'educazione-base', 'Corsi di educazione di base: seduto, terra, resta, richiamo, passeggiata al guinzaglio')
ON CONFLICT (slug) DO NOTHING;

-- INFRASTRUTTURE
INSERT INTO infrastrutture (nome, slug, icona) VALUES
  ('Campo Coperto (Indoor)', 'campo-coperto', 'warehouse'),
  ('Campo Recintato in Sicurezza', 'campo-recintato', 'fence'),
  ('Piscina Cinofila', 'piscina', 'pool'),
  ('Area Asilo Diurno', 'asilo-diurno', 'dog')
ON CONFLICT (slug) DO NOTHING;

-- AFFILIAZIONI
INSERT INTO affiliazioni (nome, slug, ente_ufficiale) VALUES
  ('ENCI', 'enci', 'Ente Nazionale Cinofilia Italiana'),
  ('OPES Cinofilia', 'opes-cinofilia', 'OPES - Settore Cinofilia'),
  ('FICSS', 'ficss', 'Federazione Italiana Cinofilia Sport e Soccorso'),
  ('CSEN', 'csen', 'Centro Sportivo Educativo Nazionale'),
  ('FISC', 'fisc', 'Federazione Italiana Sport Cinofili'),
  ('ASC', 'asc', 'Attività Sportive Confederate'),
  ('Altro', 'altro', 'Altra affiliazione non elencata')
ON CONFLICT (slug) DO NOTHING;

COMMIT;