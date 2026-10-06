import sys
import types
import unittest
from unittest.mock import Mock, patch
from importlib.resources import files

from pipeline_comercial.bigquery import DestinoBigQuery
from pipeline_comercial.modelo import TABELAS


class Conflict(Exception):
    pass


class Transitorio(Exception):
    pass


class BigQueryTest(unittest.TestCase):
    def setUp(self):
        self.db = object.__new__(DestinoBigQuery)
        self.db.projeto, self.db.localizacao = "portfolio-teste", "US"
        self.db.cliente = Mock()
        self.db.bq = Mock()
        self.db.bq.LoadJobConfig = lambda **kwargs: kwargs
        excecoes = types.ModuleType("google.api_core.exceptions")
        excecoes.Conflict = Conflict
        excecoes.ServiceUnavailable = Transitorio
        excecoes.InternalServerError = Transitorio
        excecoes.TooManyRequests = Transitorio
        self.contexto = patch.dict(sys.modules, {"google.api_core.exceptions": excecoes})
        self.contexto.start()
        self.addCleanup(self.contexto.stop)

    def test_carga_repetida_recupera_job_existente(self):
        self.db._carregar("raw.registros", [{"a": 1}], [])
        id1 = self.db.cliente.load_table_from_json.call_args.kwargs["job_id"]
        self.db.cliente.load_table_from_json.side_effect = Conflict()
        self.db._carregar("raw.registros", [{"a": 1}], [])
        id2 = self.db.cliente.load_table_from_json.call_args.kwargs["job_id"]
        self.assertEqual(id1, id2)
        self.db.cliente.get_job.assert_called_once_with(id1, location="US")
        self.db.cliente.get_job.return_value.result.assert_called_once()

    def test_job_falho_transitorio_usa_outro_id(self):
        falho, sucesso = Mock(), Mock()
        falho.result.side_effect = Transitorio()
        self.db.cliente.load_table_from_json.side_effect = [falho, sucesso]
        self.db._carregar("raw.registros", [{"a": 1}], [])
        ids = [c.kwargs["job_id"] for c in self.db.cliente.load_table_from_json.call_args_list]
        self.assertNotEqual(ids[0], ids[1])
        sucesso.result.assert_called_once()

    def test_job_nao_transitorio_nao_e_mascarado(self):
        self.db.cliente.load_table_from_json.return_value.result.side_effect = ValueError("schema")
        with self.assertRaises(ValueError):
            self.db._carregar("raw.registros", [{"a": 1}], [])
        self.assertEqual(self.db.cliente.load_table_from_json.call_count, 1)

    def test_query_parametriza_id_e_informa_regiao(self):
        self.db.cliente.query.return_value.result.return_value = []
        self.db._query("SELECT @id FROM `__PROJETO__.operacao.execucoes`", id="run';DROP")
        args = self.db.cliente.query.call_args
        self.assertNotIn("DROP", args.args[0])
        self.assertIn("portfolio-teste.operacao", args.args[0])
        self.assertEqual(args.kwargs["location"], "US")

    def test_publicacao_transacional_inclui_todas_as_tabelas_e_watermarks(self):
        sql = files("pipeline_comercial").joinpath("sql/publicar.sql").read_text()
        self.assertLess(sql.index("BEGIN TRANSACTION"), sql.index("\n  MERGE"))
        self.assertGreater(sql.index("COMMIT TRANSACTION"), sql.index("operacao.watermarks"))
        for tabela, chave, _ in TABELAS.values():
            self.assertIn(f"MERGE `__PROJETO__.{tabela}`", sql)
            self.assertIn(f"t.{chave}=s.{chave}", sql)
        self.assertIn("GREATEST(t.valor,s.valor)", sql)
        self.assertIn("status = 'aprovada'", sql)

    def test_projeto_invalido_e_rejeitado_antes_de_criar_cliente(self):
        with self.assertRaises(ValueError):
            DestinoBigQuery("projeto`;DROP")
