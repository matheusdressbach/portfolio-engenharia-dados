-- Troque workspace pelo catálogo existente no seu Free Edition.
SELECT id_pedido, quantidade_pedida, quantidade_faturada,
       quantidade_aberta, quantidade_cancelada, quantidade_devolvida,
       valor_faturado, valor_devolvido, receita_apos_devolucao
FROM workspace.p4_comercial.fato_carteira_pedidos
ORDER BY id_pedido;

SELECT * FROM workspace.p4_controle.quarentena_eventos;

-- Histórico de commits do Delta; versões dependem do número de execuções.
DESCRIBE HISTORY workspace.p4_silver.pedidos;

SELECT * FROM workspace.p4_controle.execucoes ORDER BY registrado_em DESC;
