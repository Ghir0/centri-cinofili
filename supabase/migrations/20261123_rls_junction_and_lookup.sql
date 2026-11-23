-- Migration: Abilita Row Level Security e revoca scritture pubbliche sulle junction
-- e allinea le metodologie aggiungendo quelle mancanti dai seed storici

-- 1. Allinea metodologie (se non gia' presenti nel database)
INSERT INTO public.metodologie (id, nome, slug, descrizione) VALUES
  (5, 'Etologico', 'etologico', 'Approccio basato sullo studio del comportamento naturale della specie canina, rispettando le motivazioni innate e i bisogni etologici specifici.'),
  (6, 'Misto', 'misto', 'Integrazione pragmatica di piu approcci educativi adattata alle esigenze specifiche del singolo binomio.')
ON CONFLICT (id) DO UPDATE SET
  nome = EXCLUDED.nome,
  slug = EXCLUDED.slug,
  descrizione = EXCLUDED.descrizione;

SELECT setval('metodologie_id_seq', (SELECT MAX(id) FROM metodologie));

-- 2. Row Level Security su junction
ALTER TABLE public.centri_metodologie    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.centri_discipline     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.centri_infrastrutture ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.centri_affiliazioni   ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS select_pubblico ON public.centri_metodologie;
DROP POLICY IF EXISTS select_pubblico ON public.centri_discipline;
DROP POLICY IF EXISTS select_pubblico ON public.centri_infrastrutture;
DROP POLICY IF EXISTS select_pubblico ON public.centri_affiliazioni;

CREATE POLICY select_pubblico ON public.centri_metodologie    FOR SELECT USING (true);
CREATE POLICY select_pubblico ON public.centri_discipline     FOR SELECT USING (true);
CREATE POLICY select_pubblico ON public.centri_infrastrutture FOR SELECT USING (true);
CREATE POLICY select_pubblico ON public.centri_affiliazioni   FOR SELECT USING (true);

-- 3. Revoca scritture per ruoli pubblici
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
  ON public.centri_metodologie, public.centri_discipline,
     public.centri_infrastrutture, public.centri_affiliazioni
  FROM anon, authenticated;
