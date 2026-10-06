-- Dados inteiramente sintéticos. Bancos Airflow e ERP usam o mesmo servidor local.
CREATE USER airflow WITH PASSWORD 'airflow_local';
CREATE DATABASE airflow OWNER airflow;
CREATE SCHEMA erp;
CREATE SCHEMA planejamento;

CREATE TABLE erp.vendedores (
 id_vendedor bigint PRIMARY KEY, nome text NOT NULL, ativo boolean NOT NULL,
 atualizado_em timestamptz NOT NULL);
CREATE TABLE erp.clientes (
 id_cliente bigint PRIMARY KEY, nome text NOT NULL, uf char(2) NOT NULL,
 atualizado_em timestamptz NOT NULL);
CREATE TABLE erp.produtos (
 id_produto bigint PRIMARY KEY, descricao text NOT NULL, atualizado_em timestamptz NOT NULL);
CREATE TABLE erp.vendas (
 id_lancamento bigint PRIMARY KEY, id_vendedor bigint REFERENCES erp.vendedores,
 id_cliente bigint REFERENCES erp.clientes, id_produto bigint REFERENCES erp.produtos,
 data_venda date NOT NULL, quantidade integer NOT NULL,
 valor_bruto numeric(18,2) NOT NULL, valor_desconto numeric(18,2) NOT NULL,
 cancelado boolean NOT NULL DEFAULT false, atualizado_em timestamptz NOT NULL);
CREATE TABLE planejamento.metas (
 id_meta bigint PRIMARY KEY, id_vendedor bigint NOT NULL, competencia date NOT NULL,
 valor_meta numeric(18,2) NOT NULL, atualizado_em timestamptz NOT NULL,
 UNIQUE (id_vendedor,competencia));

CREATE INDEX ON erp.vendedores(atualizado_em,id_vendedor);
CREATE INDEX ON erp.clientes(atualizado_em,id_cliente);
CREATE INDEX ON erp.produtos(atualizado_em,id_produto);
CREATE INDEX ON erp.vendas(atualizado_em,id_lancamento);
CREATE INDEX ON planejamento.metas(atualizado_em,id_meta);

-- Toda alteração recebe tempo do banco; não usamos a data comercial como watermark.
CREATE FUNCTION carimbar_atualizacao() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.atualizado_em = clock_timestamp(); RETURN NEW; END $$;
CREATE TRIGGER atualizacao BEFORE UPDATE ON erp.vendedores FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();
CREATE TRIGGER atualizacao BEFORE UPDATE ON erp.clientes FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();
CREATE TRIGGER atualizacao BEFORE UPDATE ON erp.produtos FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();
CREATE TRIGGER atualizacao BEFORE UPDATE ON erp.vendas FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();
CREATE TRIGGER atualizacao BEFORE UPDATE ON planejamento.metas FOR EACH ROW EXECUTE FUNCTION carimbar_atualizacao();

INSERT INTO erp.vendedores VALUES
 (1,'Ana Martins',true,'2026-09-01 08:00+00'),(2,'Bruno Lopes',true,'2026-09-01 08:00+00');
INSERT INTO erp.clientes VALUES (10,'Mercado Horizonte','SP','2026-09-01 08:00+00');
INSERT INTO erp.produtos VALUES (100,'Café torrado 500g','2026-09-01 08:00+00');
INSERT INTO erp.vendas VALUES
 (1001,1,10,100,'2026-09-01',10,300.00,20.00,false,'2026-09-01 10:00+00'),
 (1002,2,10,100,'2026-09-01',5,150.00,0.00,false,'2026-09-01 10:00+00');
INSERT INTO planejamento.metas VALUES
 (1,1,'2026-09-01',1000.00,'2026-09-01 08:00+00'),
 (2,2,'2026-09-01',800.00,'2026-09-01 08:00+00');

CREATE USER leitor_erp WITH PASSWORD 'leitor_local';
GRANT USAGE ON SCHEMA erp TO leitor_erp;
GRANT SELECT ON ALL TABLES IN SCHEMA erp TO leitor_erp;
CREATE USER leitor_metas WITH PASSWORD 'metas_local';
GRANT USAGE ON SCHEMA planejamento TO leitor_metas;
GRANT SELECT ON ALL TABLES IN SCHEMA planejamento TO leitor_metas;

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
