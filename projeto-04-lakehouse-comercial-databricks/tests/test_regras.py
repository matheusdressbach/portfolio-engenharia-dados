import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gerar_lotes import lotes,fatura,devolucao,pedido
from referencia import consolidar

class RegrasComerciais(unittest.TestCase):
    def setUp(self):self.eventos=[e for ls in lotes().values() for e in ls]
    def test_48_pedidos(self):self.assertEqual(len(consolidar(self.eventos)),48)
    def test_repeticao(self):self.assertEqual(consolidar(self.eventos),consolidar(self.eventos+self.eventos))
    def test_antigo_nao_desfaz_cancelamento(self):
        p=consolidar(self.eventos)[1];self.assertEqual(p['quantidade_aberta'],0);self.assertGreater(p['quantidade_cancelada'],0)
    def test_faturamento_parcial(self):
        p=consolidar([pedido(1),fatura(1,1,4)])[0];self.assertEqual(p['quantidade_aberta'],7)
    def test_devolucao_nao_reabre_pedido(self):
        p=consolidar([pedido(1),fatura(1,1,4),devolucao(1,1,1)])[0];self.assertEqual(p['quantidade_aberta'],7);self.assertEqual(p['receita_apos_devolucao'],'75.00')
    def test_documento_pendente_resolvido(self):
        e=[fatura(410,41,2)];self.assertEqual(consolidar(e),[]);self.assertEqual(consolidar(e+[pedido(41)])[0]['quantidade_faturada'],2)
    def test_quantidade_negativa_nao_publicada(self):self.assertEqual(consolidar([pedido(1),fatura(1,1,-1)])[0]['quantidade_faturada'],0)
    def test_id_reutilizado(self):
        e=pedido(1);f=copy.deepcopy(e);f['quantidade']='99'
        with self.assertRaises(ValueError):consolidar([e,f])
    def test_excesso_faturamento(self):
        with self.assertRaises(ValueError):consolidar([pedido(1),fatura(1,1,99)])
    def test_excesso_devolucao(self):
        with self.assertRaises(ValueError):consolidar([pedido(1),fatura(1,1,4),devolucao(1,1,5)])
    def test_estorno_nao_conta_receita(self):self.assertEqual(consolidar([pedido(1),fatura(1,1,4,status='estornado')])[0]['valor_faturado'],'0.00')
    def test_versao_ambigua(self):
        e=pedido(1);f=copy.deepcopy(e);f.update(id_evento='outro',quantidade='99')
        with self.assertRaises(ValueError):consolidar([e,f])
if __name__=='__main__':unittest.main(verbosity=2)
