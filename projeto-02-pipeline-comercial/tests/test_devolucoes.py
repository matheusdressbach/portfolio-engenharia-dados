import unittest
from copy import deepcopy
from decimal import Decimal

from pipeline_comercial.exemplo import dados_exemplo, segundo_dia
from pipeline_comercial.fontes import FonteMemoria
from pipeline_comercial.local import DestinoLocal
from pipeline_comercial.modelo import TABELAS, deduplicar
from pipeline_comercial.pipeline import executar
from pipeline_comercial.populacao import gerar, sql
from pipeline_comercial.qualidade import FalhaQualidade, validar


class DevolucoesTest(unittest.TestCase):
    def lotes(self):
        dados=dados_exemplo()
        dados['devolucoes']=[dict(id_devolucao=1,id_lancamento=1001,data_devolucao='2026-09-02',
            quantidade=2,valor_devolvido='56.00',motivo='Avaria',atualizado_em='2026-09-02T10:00:00Z')]
        return {e:deduplicar(e,linhas) for e,linhas in dados.items()}

    def test_devolucao_parcial_valida(self):
        validar(self.lotes(),{e:[] for e in TABELAS})

    def test_rejeita_venda_ausente_cancelada_data_e_valores(self):
        for campo,valor in [('id_lancamento',999),('data_devolucao','2026-08-01'),('quantidade',0),
                            ('quantidade',11),('valor_devolvido','281.00'),('valor_devolvido','-1.00')]:
            lotes=self.lotes(); lotes['devolucoes'][0][campo]=valor
            with self.subTest(campo=campo,valor=valor),self.assertRaises(FalhaQualidade):
                validar(lotes,{e:[] for e in TABELAS})
        lotes=self.lotes(); lotes['vendas'][0]['cancelado']=True
        with self.assertRaises(FalhaQualidade):
            validar(lotes,{e:[] for e in TABELAS})

    def test_acumula_devolucoes_publicadas_e_novas(self):
        publicados=self.lotes()
        publicados['devolucoes'][0].update(quantidade=8,valor_devolvido='224.00')
        lote={e:[] for e in TABELAS}
        lote['devolucoes']=[{**publicados['devolucoes'][0],'id_devolucao':2,'quantidade':3,'valor_devolvido':'84.00'}]
        with self.assertRaises(FalhaQualidade):
            validar(lote,publicados)

    def test_massa_reproduzivel_e_relacoes_validas(self):
        a,b=gerar(),gerar()
        self.assertEqual(a,b)
        self.assertEqual({e:len(r) for e,r in a.items()},dict(vendedores=12,clientes=200,produtos=40,vendas=4997,devolucoes=180,metas=142))
        validar(a,{e:[] for e in TABELAS})
        self.assertEqual(len({r['data_venda'][:7] for r in a['vendas']}),12)
        self.assertIn('CURRENT_TIMESTAMP',sql(a))
        self.assertNotIn('DELETE',sql(a))
        self.assertTrue(all(r['id_lancamento']>=10000 for r in a['vendas']))

    def test_pipeline_com_massa_ampliada_idempotencia_e_rollback(self):
        dados=dados_exemplo(); segundo_dia(dados)
        massa=gerar()
        for e in TABELAS:
            dados[e].extend(massa[e])
        fonte=FonteMemoria(dados)
        db=DestinoLocal(':memory:')
        self.addCleanup(db.close)
        executar(db,fonte,fonte,'ampliada','2026-10-02T00:00:00Z')
        antes=deepcopy(db.publicados())
        self.assertEqual({e:len(r) for e,r in antes.items()},dict(vendedores=12,clientes=200,produtos=40,vendas=5000,devolucoes=180,metas=144))
        executar(db,fonte,fonte,'repetida','2026-10-03T00:00:00Z')
        self.assertEqual(db.publicados(),antes)
        marcas=list(db.db.execute('SELECT entidade,valor FROM watermarks ORDER BY entidade'))
        dados['devolucoes'].append({**massa['devolucoes'][0],'id_devolucao':99999,'quantidade':9999,'atualizado_em':'2026-10-03T10:00:00Z'})
        with self.assertRaises(FalhaQualidade):
            executar(db,fonte,fonte,'invalida','2026-10-04T00:00:00Z')
        self.assertEqual(db.publicados(),antes)
        self.assertEqual(list(db.db.execute('SELECT entidade,valor FROM watermarks ORDER BY entidade')),marcas)
