-- Migração aditiva: preserva fontes e histórico já existentes.
BEGIN;
ALTER TABLE erp.vendedores ADD COLUMN IF NOT EXISTS equipe text NOT NULL DEFAULT 'Não informado';
ALTER TABLE erp.vendedores ADD COLUMN IF NOT EXISTS regiao text NOT NULL DEFAULT 'Não informado';
ALTER TABLE erp.clientes ADD COLUMN IF NOT EXISTS cidade text NOT NULL DEFAULT 'Não informado';
ALTER TABLE erp.clientes ADD COLUMN IF NOT EXISTS segmento text NOT NULL DEFAULT 'Não informado';
ALTER TABLE erp.produtos ADD COLUMN IF NOT EXISTS categoria text NOT NULL DEFAULT 'Não informado';
CREATE TABLE IF NOT EXISTS erp.devolucoes (
 id_devolucao bigint PRIMARY KEY,
 id_lancamento bigint NOT NULL REFERENCES erp.vendas(id_lancamento),
 data_devolucao date NOT NULL, quantidade integer NOT NULL,
 valor_devolvido numeric(18,2) NOT NULL, motivo text NOT NULL,
 atualizado_em timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS devolucoes_incremental ON erp.devolucoes(atualizado_em,id_devolucao);
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='erp.devolucoes'::regclass AND tgname='atualizacao') THEN
  CREATE TRIGGER atualizacao BEFORE UPDATE ON erp.devolucoes FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();
 END IF;
END $$;
GRANT SELECT ON erp.devolucoes TO leitor_erp;
COMMIT;
