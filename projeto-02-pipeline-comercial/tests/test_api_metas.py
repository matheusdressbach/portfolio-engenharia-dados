import base64
import json
import sys
import types
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from pipeline_comercial.api_metas import Handler


class APIMetasTest(unittest.TestCase):
    def handler(self, parametros):
        h = object.__new__(Handler)
        h.path = "/metas?" + urlencode(parametros)
        h.responder = Mock()
        return h

    def test_contrato_servidor_e_cursor_de_desempate(self):
        tempo = datetime(2026, 9, 1, tzinfo=timezone.utc)
        linhas = [{"id_meta": i, "id_vendedor": i, "competencia": date(2026, 9, 1),
                   "valor_meta": Decimal("1000.00"), "atualizado_em": tempo} for i in (1, 2)]
        db = Mock()
        db.__enter__, db.__exit__ = Mock(return_value=db), Mock(return_value=False)
        db.execute.return_value.fetchall.return_value = linhas
        pg, rows = types.ModuleType("psycopg"), types.ModuleType("psycopg.rows")
        pg.connect, rows.dict_row = Mock(return_value=db), object()
        h = self.handler({"inicio": "2026-09-01T00:00:00Z", "fim": "2026-09-02T00:00:00Z", "limite": 1})
        with patch.dict(sys.modules, {"psycopg": pg, "psycopg.rows": rows}), patch.dict("os.environ", {"API_DSN": "teste"}):
            h.do_GET()
        codigo, corpo = h.responder.call_args.args
        self.assertEqual(codigo, 200)
        self.assertEqual(corpo["itens"][0]["valor_meta"], "1000.00")
        self.assertEqual(corpo["itens"][0]["competencia"], "2026-09-01")
        self.assertEqual(json.loads(base64.urlsafe_b64decode(corpo["proximo_cursor"])), [tempo.isoformat(), 1])
        self.assertEqual(db.execute.call_args.args[1][-1], 2)

    def test_janela_invertida_e_limite_invalido_retornam_400(self):
        for parametros in (
            {"inicio": "2026-09-02T00:00:00Z", "fim": "2026-09-01T00:00:00Z"},
            {"inicio": "2026-09-01T00:00:00Z", "fim": "2026-09-02T00:00:00Z", "limite": 1001},
            {"inicio": "2026-09-01T00:00:00", "fim": "2026-09-02T00:00:00Z"},
        ):
            h = self.handler(parametros)
            h.do_GET()
            self.assertEqual(h.responder.call_args.args[0], 400)

    def test_health_e_rota_inexistente(self):
        h = object.__new__(Handler)
        h.responder = Mock()
        for rota, codigo in (("/health", 200), ("/vendas", 404)):
            h.path = rota
            h.do_GET()
            self.assertEqual(h.responder.call_args.args[0], codigo)
