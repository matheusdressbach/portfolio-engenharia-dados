# Databricks notebook source
"""Motor de lotes: mesmo código usado no notebook e na integração local."""
import re
import time
from uuid import uuid4
from datetime import datetime, timezone
from pyspark.sql import functions as F

CAMPOS = ['id_evento','entidade','id_registro','versao','atualizado_em','id_cliente',
          'id_vendedor','id_produto','id_referencia','quantidade','preco_unitario',
          'data_documento','data_prevista','status']
SCHEMA_EVENTOS = ', '.join(f'{c} string' for c in CAMPOS)

class LakehouseComercial:
    def __init__(self,spark,catalogo=None,prefixo='p4_'):
        self.spark=spark
        if catalogo and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',catalogo):raise ValueError('Catálogo inválido')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',prefixo):raise ValueError('Prefixo obrigatório para isolar o projeto')
        self.catalogo=catalogo;self.prefixo=prefixo
        self.sq=lambda query:spark.sql(query)
        for camada in ['bronze','silver','dm','comercial','controle']:
            self.sq(f'CREATE SCHEMA IF NOT EXISTS {self.schema(camada)}')
        campos=', '.join(f'{c} STRING' for c in CAMPOS)
        self.sq(f'CREATE TABLE IF NOT EXISTS {self.t("bronze","eventos_comerciais")} ({campos}, hash_conteudo STRING) USING DELTA')
    def schema(self,camada):
        return (f'{self.catalogo}.' if self.catalogo else '')+self.prefixo+camada
    def t(self,camada,nome):return self.schema(camada)+'.'+nome
    def cadastros(self,pasta):
        schemas={'clientes':'id_cliente long, nome string','vendedores':'id_vendedor long, nome string',
                 'produtos':'id_produto long, nome string, categoria string'}
        for nome,schema in schemas.items():
            df=self.spark.read.schema(schema).json(f'{pasta}/{nome}.jsonl')
            if df.filter(F.col(f'id_{nome[:-1] if nome != "vendedores" else "vendedor"}').isNull()).count():raise ValueError('Cadastro inválido')
            df.write.format('delta').mode('overwrite').saveAsTable(self.t('dm','dim_'+nome))
    def processar(self,arquivo,data_corte='2026-09-30'):
        inicio=time.monotonic(); resumo={}; erro=None; status='sucesso'
        try:
            resumo=self._processar(arquivo,data_corte)
            return resumo
        except Exception as exc:
            status='falha';erro=str(exc)[:2000]
            raise
        finally:
            linha=(str(uuid4()),str(arquivo),data_corte,status,
                   datetime.now(timezone.utc),time.monotonic()-inicio,
                   resumo.get('eventos_bronze'),resumo.get('quarentena'),erro)
            schema='id_execucao string, arquivo string, data_corte string, status string, registrado_em timestamp, duracao_segundos double, eventos_bronze long, quarentena long, erro string'
            self.spark.createDataFrame([linha],schema).write.format('delta').mode('append').saveAsTable(self.t('controle','execucoes'))
    def _processar(self,arquivo,data_corte='2026-09-30'):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',data_corte):raise ValueError('Data de corte inválida')
        df=self.spark.read.schema(SCHEMA_EVENTOS).option('mode','FAILFAST').json(arquivo)
        if df.filter(F.col('id_evento').isNull() | (F.trim('id_evento')=='')).count():raise ValueError('Evento sem identificador')
        df=df.withColumn('hash_conteudo',F.sha2(F.to_json(F.struct(*[F.col(c) for c in CAMPOS if c!='id_evento'])),256))
        df.createOrReplaceTempView('p4_lote')
        # Detectar ambiguidades antes de aceitar eventos. Não escolher arbitrariamente uma linha.
        conflitos=self.sq(f"""SELECT id_evento FROM (
            SELECT id_evento, hash_conteudo FROM p4_lote
            UNION ALL SELECT id_evento, hash_conteudo FROM {self.t('bronze','eventos_comerciais')}
        ) GROUP BY id_evento HAVING count(DISTINCT hash_conteudo)>1""")
        if conflitos.limit(1).count():raise ValueError('id_evento reutilizado com conteúdo diferente')
        revisoes=self.sq(f"""SELECT entidade,try_cast(id_registro AS BIGINT) AS chave,try_cast(versao AS BIGINT) AS revisao FROM (
            SELECT * FROM p4_lote UNION ALL SELECT * FROM {self.t('bronze','eventos_comerciais')}
        ) WHERE try_cast(id_registro AS BIGINT) IS NOT NULL AND try_cast(versao AS BIGINT) IS NOT NULL GROUP BY entidade,try_cast(id_registro AS BIGINT),try_cast(versao AS BIGINT) HAVING count(DISTINCT hash_conteudo)>1""")
        if revisoes.limit(1).count():raise ValueError('Versão ambígua para o mesmo registro')
        self.sq(f"""MERGE INTO {self.t('bronze','eventos_comerciais')} t
            USING (SELECT DISTINCT * FROM p4_lote) s ON t.id_evento=s.id_evento
            WHEN NOT MATCHED THEN INSERT *""")
        self.sq(f"""CREATE OR REPLACE TEMP VIEW p4_tipados AS SELECT *,
            try_cast(id_registro AS BIGINT) AS chave,
            try_cast(versao AS BIGINT) AS revisao,
            try_cast(quantidade AS BIGINT) AS qtd,
            try_cast(preco_unitario AS DECIMAL(18,2)) AS preco,
            try_cast(data_documento AS DATE) AS data_doc,
            try_cast(data_prevista AS DATE) AS previsao,
            try_cast(atualizado_em AS TIMESTAMP) AS atualizado
            FROM {self.t('bronze','eventos_comerciais')}""")
        self.sq(f"""CREATE OR REPLACE TEMP VIEW p4_avaliados AS SELECT *, CASE
            WHEN chave IS NULL OR chave<=0 OR revisao IS NULL OR revisao<=0 OR atualizado IS NULL OR data_doc IS NULL THEN 'identificador_versao_ou_data_invalida'
            WHEN qtd IS NULL OR qtd<=0 THEN 'quantidade_invalida'
            WHEN entidade='pedido' AND (preco IS NULL OR preco<=0 OR previsao IS NULL
                OR previsao<data_doc OR status NOT IN ('aberto','cancelado') OR status IS NULL
                OR try_cast(id_cliente AS BIGINT) NOT IN (SELECT id_cliente FROM {self.t('dm','dim_clientes')})
                OR try_cast(id_vendedor AS BIGINT) NOT IN (SELECT id_vendedor FROM {self.t('dm','dim_vendedores')})
                OR try_cast(id_produto AS BIGINT) NOT IN (SELECT id_produto FROM {self.t('dm','dim_produtos')})
                OR id_cliente IS NULL OR id_vendedor IS NULL OR id_produto IS NULL
                OR try_cast(id_cliente AS BIGINT) IS NULL OR try_cast(id_vendedor AS BIGINT) IS NULL OR try_cast(id_produto AS BIGINT) IS NULL) THEN 'pedido_invalido'
            WHEN entidade='faturamento' AND (status IS NULL OR status NOT IN ('faturado','estornado') OR try_cast(id_referencia AS BIGINT) IS NULL) THEN 'faturamento_invalido'
            WHEN entidade='devolucao' AND (status IS NULL OR status<>'confirmada' OR try_cast(id_referencia AS BIGINT) IS NULL) THEN 'devolucao_invalida'
            WHEN entidade IS NULL OR entidade NOT IN ('pedido','faturamento','devolucao') THEN 'entidade_invalida'
            ELSE NULL END AS motivo FROM p4_tipados""")
        self.sq("""CREATE OR REPLACE TEMP VIEW p4_atuais AS SELECT * EXCEPT (posicao) FROM (
            SELECT *,row_number() OVER (PARTITION BY entidade,chave ORDER BY revisao DESC,id_evento) AS posicao
            FROM p4_avaliados WHERE motivo IS NULL) WHERE posicao=1""")
        self.sq("CREATE OR REPLACE TEMP VIEW p4_pedidos AS SELECT * FROM p4_atuais WHERE entidade='pedido'")
        self.sq("""CREATE OR REPLACE TEMP VIEW p4_faturas AS SELECT f.* FROM p4_atuais f
            JOIN p4_pedidos p ON try_cast(f.id_referencia AS BIGINT)=p.chave
            WHERE f.entidade='faturamento' AND f.data_doc>=p.data_doc""")
        self.sq("""CREATE OR REPLACE TEMP VIEW p4_devolucoes AS SELECT d.* FROM p4_atuais d
            JOIN p4_faturas f ON try_cast(d.id_referencia AS BIGINT)=f.chave
            WHERE d.entidade='devolucao' AND f.status='faturado' AND d.data_doc>=f.data_doc""")
        self.sq(f"""CREATE OR REPLACE TABLE {self.t('controle','quarentena_eventos')} USING DELTA AS
            SELECT id_evento,entidade,chave,revisao,motivo FROM p4_avaliados WHERE motivo IS NOT NULL
            UNION ALL SELECT id_evento,entidade,chave,revisao,'referencia_ausente_ou_data_incompativel' FROM p4_atuais a
            WHERE (entidade='faturamento' AND NOT EXISTS(SELECT 1 FROM p4_faturas f WHERE f.id_evento=a.id_evento))
               OR (entidade='devolucao' AND NOT EXISTS(SELECT 1 FROM p4_devolucoes d WHERE d.id_evento=a.id_evento))""")
        # Bloquear totais impossíveis antes de alterar a posição consolidada.
        excesso=self.sq("""SELECT p.chave FROM p4_pedidos p JOIN p4_faturas f ON try_cast(f.id_referencia AS BIGINT)=p.chave
            WHERE f.status='faturado' GROUP BY p.chave,p.qtd HAVING sum(f.qtd)>p.qtd
            UNION ALL SELECT f.chave FROM p4_faturas f JOIN p4_devolucoes d ON try_cast(d.id_referencia AS BIGINT)=f.chave
            GROUP BY f.chave,f.qtd HAVING sum(d.qtd)>f.qtd""")
        if excesso.limit(1).count():raise ValueError('Quantidade consolidada excede documento de origem; Silver preservada')
        selecoes={
            'pedidos':"SELECT chave AS id_pedido,revisao AS versao,atualizado,try_cast(id_cliente AS BIGINT) AS id_cliente,try_cast(id_vendedor AS BIGINT) AS id_vendedor,try_cast(id_produto AS BIGINT) AS id_produto,qtd AS quantidade,preco AS preco_unitario,data_doc AS data_pedido,previsao AS data_prevista,status FROM p4_pedidos",
            'faturamentos':"SELECT chave AS id_faturamento,revisao AS versao,atualizado,try_cast(id_referencia AS BIGINT) AS id_pedido,qtd AS quantidade,data_doc AS data_faturamento,status FROM p4_faturas",
            'devolucoes':"SELECT chave AS id_devolucao,revisao AS versao,atualizado,try_cast(id_referencia AS BIGINT) AS id_faturamento,qtd AS quantidade,data_doc AS data_devolucao,status FROM p4_devolucoes"}
        for nome,query in selecoes.items():
            tabela=self.t('silver',nome); chave={'pedidos':'id_pedido','faturamentos':'id_faturamento','devolucoes':'id_devolucao'}[nome]
            self.sq(f'CREATE TABLE IF NOT EXISTS {tabela} USING DELTA AS {query} LIMIT 0')
            self.sq(f"""MERGE INTO {tabela} t USING ({query}) s ON t.{chave}=s.{chave}
                WHEN MATCHED AND s.versao>t.versao THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                WHEN NOT MATCHED BY SOURCE THEN DELETE""")
        self.gold(data_corte)
        return {'eventos_bronze':self.spark.table(self.t('bronze','eventos_comerciais')).count(),
                'quarentena':self.spark.table(self.t('controle','quarentena_eventos')).count(),
                'pedidos':self.spark.table(self.t('silver','pedidos')).count()}
    def gold(self,data_corte):
        p=self.t('silver','pedidos');f=self.t('silver','faturamentos');d=self.t('silver','devolucoes')
        self.sq(f"""CREATE OR REPLACE VIEW {self.t('comercial','fato_carteira_pedidos')} AS
            WITH fat AS (SELECT id_pedido,sum(quantidade) AS qtd FROM {f} WHERE status='faturado' GROUP BY id_pedido),
            dev AS (SELECT f.id_pedido,sum(d.quantidade) AS qtd FROM {d} d JOIN {f} f USING(id_faturamento) WHERE f.status='faturado' GROUP BY f.id_pedido),
            posicao AS (SELECT p.*,p.quantidade AS quantidade_pedida,coalesce(fat.qtd,0) AS quantidade_faturada,
                coalesce(dev.qtd,0) AS quantidade_devolvida,
                CASE WHEN p.status='cancelado' THEN 0 ELSE p.quantidade-coalesce(fat.qtd,0) END AS quantidade_aberta,
                CASE WHEN p.status='cancelado' THEN p.quantidade-coalesce(fat.qtd,0) ELSE 0 END AS quantidade_cancelada
                FROM {p} p LEFT JOIN fat USING(id_pedido) LEFT JOIN dev USING(id_pedido))
            SELECT *,quantidade_aberta*preco_unitario AS valor_aberto,
                quantidade_faturada*preco_unitario AS valor_faturado,
                quantidade_devolvida*preco_unitario AS valor_devolvido,
                (quantidade_faturada-quantidade_devolvida)*preco_unitario AS receita_apos_devolucao,
                CASE WHEN quantidade_aberta>0 THEN greatest(datediff(DATE '{data_corte}',data_prevista),0) ELSE 0 END AS dias_atraso
            FROM posicao""")
        self.sq(f"""CREATE OR REPLACE VIEW {self.t('comercial','fato_devolucoes')} AS
            SELECT d.id_devolucao,d.id_faturamento,f.id_pedido,p.id_cliente,p.id_vendedor,p.id_produto,
                d.data_devolucao,d.quantidade AS quantidade_devolvida,d.quantidade*p.preco_unitario AS valor_devolvido
            FROM {d} d JOIN {f} f USING(id_faturamento) JOIN {p} p USING(id_pedido) WHERE f.status='faturado'""")
        self.sq(f"""CREATE OR REPLACE VIEW {self.t('comercial','resumo_vendedores')} AS
            SELECT id_vendedor,count(*) AS pedidos,sum(valor_aberto) AS carteira_aberta,
                sum(valor_faturado) AS faturamento,sum(valor_devolvido) AS devolucoes,
                sum(receita_apos_devolucao) AS receita_apos_devolucao,
                sum(CASE WHEN dias_atraso>0 THEN valor_aberto ELSE 0 END) AS carteira_atrasada
            FROM {self.t('comercial','fato_carteira_pedidos')} GROUP BY id_vendedor""")
