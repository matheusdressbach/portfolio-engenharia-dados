-- O trigger gera uma versão nova, permitindo recuperar o payload rejeitado.
BEGIN;
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM planejamento.metas WHERE id_meta=2 AND id_vendedor=999) THEN
  RAISE EXCEPTION 'Meta não está no estado do teste; correção não aplicada';
 END IF;
END $$;
UPDATE planejamento.metas SET id_vendedor=2 WHERE id_meta=2;
COMMIT;
