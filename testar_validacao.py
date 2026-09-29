"""Confirma que o verificador detecta corrupção sem modificar a exportação."""
import unittest
from copy import deepcopy
from decimal import Decimal
from reproduzir_offline import load_snapshot, build_facts, reconcile

class ValidacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load_snapshot()

    def test_snapshot_valido(self):
        self.assertEqual(len(reconcile(self.original, build_facts(self.original))), 18)

    def test_preco_negativo(self):
        data = deepcopy(self.original)
        data['raw.orders'][0]['unit_price'] = Decimal('-1')
        with self.assertRaisesRegex(ValueError, 'Quantidade/preço inválido'):
            build_facts(data)

    def test_cliente_ausente(self):
        data = deepcopy(self.original)
        data['raw.orders'][0]['customer_id'] = -1
        with self.assertRaisesRegex(ValueError, 'Cliente ausente'):
            build_facts(data)

    def test_valor_fato_adulterado(self):
        data = deepcopy(self.original)
        data['comercial.fato_lancamento_vendas'][0]['valor_faturamento'] += 1
        with self.assertRaisesRegex(ValueError, 'Divergência em valor_faturamento'):
            reconcile(data, build_facts(data))

    def test_agregado_adulterado(self):
        data = deepcopy(self.original)
        data['comercial.vw_indicadores_executivos'][0]['faturamento'] = Decimal(data['comercial.vw_indicadores_executivos'][0]['faturamento']) + 1
        with self.assertRaisesRegex(ValueError, 'Indicador divergente'):
            reconcile(data, build_facts(data))

if __name__ == '__main__':
    unittest.main(verbosity=2)
