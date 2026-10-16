"""Integração real com Spark e Delta; não acessa Databricks ou nuvem."""
import copy
import hashlib
import json
import runpy
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from gerar_lotes import lotes
from referencia import consolidar

ROOT=Path(__file__).resolve().parents[1]
RESULTADOS=ROOT/'resultados';RESULTADOS.mkdir(exist_ok=True)

def gravar(nome,eventos):
    p=RESULTADOS/f'{nome}.jsonl';p.write_text(''.join(json.dumps(e)+'\n' for e in eventos));return str(p)

def conteudo(spark,motor):
    estado={}
    for camada,tabela in [('bronze','eventos_comerciais'),('silver','pedidos'),('silver','faturamentos'),('silver','devolucoes')]:
        estado[f'{camada}.{tabela}']=sorted([json.dumps(x.asDict(),default=str,sort_keys=True) for x in spark.table(motor.t(camada,tabela)).collect()])
    estado['gold']=sorted([json.dumps(x.asDict(),default=str,sort_keys=True) for x in spark.table(motor.t('comercial','fato_carteira_pedidos')).collect()])
    return hashlib.sha256(json.dumps(estado,sort_keys=True).encode()).hexdigest()

with tempfile.TemporaryDirectory(prefix='p4-delta-') as tmp:
    builder=(SparkSession.builder.master('local[2]').appName('validacao-lakehouse-comercial')
        .config('spark.sql.extensions','io.delta.sql.DeltaSparkSessionExtension')
        .config('spark.sql.catalog.spark_catalog','org.apache.spark.sql.delta.catalog.DeltaCatalog')
        .config('spark.sql.warehouse.dir',tmp+'/warehouse')
        .config('spark.sql.shuffle.partitions','2')
        .config('spark.databricks.delta.snapshotPartitions','2')
        .config('spark.sql.session.timeZone','UTC')
        .config('spark.driver.memory','2g'))
    spark=configure_spark_with_delta_pip(builder).getOrCreate();spark.sparkContext.setLogLevel('ERROR')
    try:
        Motor=runpy.run_path(str(ROOT/'notebooks/00_motor.py'))['LakehouseComercial']
        motor=Motor(spark);motor.cadastros(str(ROOT/'dados'))
        acumulados=[];etapas=[]
        for nome,eventos in lotes().items():
            atual=motor.processar(str(ROOT/'dados/lotes'/f'{nome}.jsonl'))
            acumulados.extend(eventos);referencia=consolidar(acumulados)
            campos=list(referencia[0])
            observado=[x.asDict() for x in spark.table(motor.t('comercial','fato_carteira_pedidos')).select(*campos).orderBy('id_pedido').collect()]
            for o,e in zip(observado,referencia):
                for campo in campos:assert str(o[campo])==str(e[campo]),(nome,campo,o,e)
            assert len(observado)==len(referencia)
            atual.update(lote=nome,conciliado_com_python=True);etapas.append(atual)
            print(json.dumps(atual),flush=True)
        assert etapas[1]['quarentena']==3
        assert etapas[2]['quarentena']==1  # A rejeição histórica negativa continua registrada.
        assert spark.table(motor.t('silver','pedidos')).where('id_pedido=2').first()['status']=='cancelado'
        antes=conteudo(spark,motor)
        motor.processar(str(ROOT/'dados/lotes/02_movimento.jsonl'))
        assert conteudo(spark,motor)==antes,'Reexecução mudou o conteúdo publicado'
        rejeicoes=[]
        casos=[]
        conflito=copy.deepcopy(lotes()['01_inicial'][0]);conflito['quantidade']='99';casos.append(('evento_conflitante',[conflito],'id_evento'))
        empate=copy.deepcopy(conflito);empate['id_evento']='outro-id';casos.append(('versao_ambigua',[empate],'Versão ambígua'))
        from gerar_lotes import fatura,devolucao
        casos.append(('faturamento_excedente',[fatura(1,1,99,versao=3)],'excede'))
        # Testar este excesso antes do de faturamento, pois um evento impossível
        # já aceito na Bronze só deixa de bloquear após uma versão corretiva.
        casos[-1:]=[('devolucao_excedente',[devolucao(1,1,99,versao=2)],'excede'),casos[-1]]
        for nome,eventos,mensagem in casos:
            silver_antes=[json.dumps(x.asDict(),default=str,sort_keys=True) for x in spark.table(motor.t('comercial','fato_carteira_pedidos')).orderBy('id_pedido').collect()]
            try:motor.processar(gravar(nome,eventos))
            except ValueError as e:
                assert mensagem in str(e),(nome,str(e));rejeicoes.append(nome)
            else:raise AssertionError('Erro não detectado: '+nome)
            silver_depois=[json.dumps(x.asDict(),default=str,sort_keys=True) for x in spark.table(motor.t('comercial','fato_carteira_pedidos')).orderBy('id_pedido').collect()]
            assert silver_depois==silver_antes
            if nome=='devolucao_excedente':motor.processar(gravar('corrigir_devolucao',[devolucao(1,1,1,versao=3)]))
            if nome=='faturamento_excedente':motor.processar(gravar('corrigir_faturamento',[fatura(1,1,5,versao=4)]))
        # Versões corretivas mudam o histórico Bronze; quantidades e Gold devem voltar à posição anterior.
        observado=[x.asDict() for x in spark.table(motor.t('comercial','fato_carteira_pedidos')).select(*campos).orderBy('id_pedido').collect()]
        assert observado==[{k:Decimal(v) if k.startswith('valor_') or k=='receita_apos_devolucao' else v for k,v in e.items()} for e in referencia]
        totais={campo:str(sum(Decimal(str(x[campo])) for x in referencia)) for campo in campos if campo.startswith('valor_') or campo=='receita_apos_devolucao'}
        relatorio={'validado_em_utc':datetime.now(timezone.utc).isoformat(),'ambiente':'Docker local, Spark '+spark.version+' / Delta Lake 4.0.0',
                   'databricks_validado':False,'etapas':etapas,'reexecucao_preservou_conteudo':True,
                   'versao_antiga_nao_reverteu_cancelamento':True,'rejeicoes_controladas':rejeicoes,
                   'recuperacao_conferida':True,'pedidos':len(referencia),'totais':totais}
        (RESULTADOS/'validacao-spark.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2))
        print(json.dumps(relatorio,ensure_ascii=False,indent=2),flush=True)
    finally:spark.stop()
