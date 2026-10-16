# Databricks notebook source
# MAGIC %md
# MAGIC # Onde está o dinheiro da carteira?
# MAGIC As consultas separam saldo a faturar, faturamento bruto e devoluções.
# MAGIC A data de corte é a usada no último processamento, não a data atual do computador.

# COMMAND ----------
# MAGIC %run ./00_motor

# COMMAND ----------
dbutils.widgets.text('catalogo',spark.sql('SELECT current_catalog()').first()[0])
motor=LakehouseComercial(spark,dbutils.widgets.get('catalogo'))
fato=motor.t('comercial','fato_carteira_pedidos')
display(spark.sql(f"""SELECT p.id_pedido,c.nome AS cliente,v.nome AS vendedor,
    p.quantidade_aberta,p.valor_aberto,p.dias_atraso
    FROM {fato} p JOIN {motor.t('dm','dim_clientes')} c USING(id_cliente)
    JOIN {motor.t('dm','dim_vendedores')} v USING(id_vendedor)
    WHERE p.quantidade_aberta>0 ORDER BY p.valor_aberto DESC,p.id_pedido"""))

# COMMAND ----------
display(spark.sql(f"""SELECT d.categoria,sum(p.valor_faturado) AS faturamento,
    sum(p.valor_devolvido) AS devolucoes,sum(p.receita_apos_devolucao) AS receita_apos_devolucao,
    sum(p.valor_devolvido)/nullif(sum(p.valor_faturado),0) AS taxa_devolucao_valor
    FROM {fato} p JOIN {motor.t('dm','dim_produtos')} d USING(id_produto)
    GROUP BY d.categoria ORDER BY devolucoes DESC"""))

# COMMAND ----------
display(spark.sql(f"""SELECT id_vendedor,sum(valor_aberto) AS carteira,
    sum(CASE WHEN quantidade_faturada>0 AND quantidade_aberta>0 THEN valor_aberto ELSE 0 END) AS saldo_parcial,
    sum(quantidade_cancelada*preco_unitario) AS saldo_cancelado
    FROM {fato} GROUP BY id_vendedor ORDER BY carteira DESC"""))
