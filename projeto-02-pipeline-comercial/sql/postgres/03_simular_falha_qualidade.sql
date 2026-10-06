-- Caso sintético: API aceita a meta; Data Quality deve rejeitar a referência.
BEGIN;
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM planejamento.metas WHERE id_meta=2 AND id_vendedor=2)
    OR EXISTS (SELECT 1 FROM erp.vendedores WHERE id_vendedor=999) THEN
  RAISE EXCEPTION 'Origem fora do estado esperado; teste não aplicado';
 END IF;
END $$;
UPDATE planejamento.metas SET id_vendedor=999 WHERE id_meta=2;
COMMIT;
