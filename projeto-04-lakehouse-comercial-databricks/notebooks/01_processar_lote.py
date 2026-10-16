# Databricks notebook source
# MAGIC %md
# MAGIC # Posição comercial por lote
# MAGIC Execute em um workspace **Free Edition**. Este notebook usa o Spark da plataforma.
# MAGIC Os dados devem estar em um Volume; o motor não instala Spark nem cria um cluster.

# COMMAND ----------
# MAGIC %run ./00_motor

# COMMAND ----------
dbutils.widgets.text('catalogo',spark.sql('SELECT current_catalog()').first()[0])
dbutils.widgets.text('pasta_entrada','')
dbutils.widgets.dropdown('lote','01_inicial',['01_inicial','02_movimento','03_atrasos_e_correcao'])
dbutils.widgets.text('data_corte','2026-09-30')

# COMMAND ----------
catalogo=dbutils.widgets.get('catalogo')
pasta=dbutils.widgets.get('pasta_entrada').rstrip('/')
if not pasta.startswith(f'/Volumes/{catalogo}/p4_bronze/entrada/') and pasta!=f'/Volumes/{catalogo}/p4_bronze/entrada':
    raise ValueError('Informe o Volume dedicado: /Volumes/<catalogo>/p4_bronze/entrada')
lote=dbutils.widgets.get('lote')
if lote not in ['01_inicial','02_movimento','03_atrasos_e_correcao']:raise ValueError('Lote inválido')
motor=LakehouseComercial(spark,catalogo)
motor.cadastros(pasta)
resumo=motor.processar(f'{pasta}/lotes/{lote}.jsonl',dbutils.widgets.get('data_corte'))
print(resumo)
display(spark.table(motor.t('controle','quarentena_eventos')))
