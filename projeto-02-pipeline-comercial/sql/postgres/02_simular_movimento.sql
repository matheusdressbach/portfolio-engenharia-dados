-- Executar após a primeira carga; atualizado_em é preenchido pelo trigger.
BEGIN;
UPDATE erp.vendas SET valor_desconto=30.00 WHERE id_lancamento=1001;
UPDATE erp.vendas SET cancelado=true WHERE id_lancamento=1002;
INSERT INTO erp.vendas VALUES
 (1003,1,10,100,CURRENT_DATE,2,60.00,0.00,false,clock_timestamp())
ON CONFLICT (id_lancamento) DO NOTHING;
UPDATE planejamento.metas SET valor_meta=1200.00 WHERE id_meta=1;
COMMIT;
