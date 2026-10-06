-- Harmoniza as metas preservadas do teste inicial com a base ampliada.
-- Mesma regra do gerador: (18000 + id_vendedor * 1200) * 12 / 10.
-- Reaplicação não altera timestamps quando os valores já estão corretos.
BEGIN;
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM planejamento.metas
      WHERE (id_meta=1 AND id_vendedor=1 AND competencia=DATE '2026-09-01' AND valor_meta IN (1200,23040))
         OR (id_meta=2 AND id_vendedor=2 AND competencia=DATE '2026-09-01' AND valor_meta IN (800,24480))) <> 2 THEN
    RAISE EXCEPTION 'Metas fora do cenário esperado; harmonização não aplicada';
  END IF;
END $$;
UPDATE planejamento.metas SET valor_meta=23040
WHERE id_meta=1 AND valor_meta<>23040;
UPDATE planejamento.metas SET valor_meta=24480
WHERE id_meta=2 AND valor_meta<>24480;
COMMIT;
