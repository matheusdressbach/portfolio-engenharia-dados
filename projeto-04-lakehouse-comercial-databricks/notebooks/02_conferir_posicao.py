# Databricks notebook source
# MAGIC %md
# MAGIC # Conferência do lote
# MAGIC Execute depois do processamento. Um Job deve falhar se a posição não fechar.

# COMMAND ----------
# MAGIC %run ./00_motor

# COMMAND ----------
dbutils.widgets.text('catalogo',spark.sql('SELECT current_catalog()').first()[0])
motor=LakehouseComercial(spark,dbutils.widgets.get('catalogo'))
fato=motor.t('comercial','fato_carteira_pedidos')
inconsistencias=spark.sql(f"""SELECT id_pedido FROM {fato}
    WHERE quantidade_pedida <> quantidade_faturada+quantidade_aberta+quantidade_cancelada
       OR quantidade_devolvida>quantidade_faturada
       OR receita_apos_devolucao<>valor_faturado-valor_devolvido
       OR quantidade_aberta<0
    UNION ALL SELECT id_pedido FROM {fato} GROUP BY id_pedido HAVING count(*)>1""")
if inconsistencias.limit(1).count():raise ValueError('Posição comercial inconsistente')
print('Quantidades, valores e unicidade conferidos.')
display(spark.table(motor.t('comercial','resumo_vendedores')).orderBy('id_vendedor'))
