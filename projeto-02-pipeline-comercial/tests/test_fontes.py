import io
import json
import sys
import types
import unittest
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from unittest.mock import Mock, patch

from pipeline_comercial.fontes import API, PostgreSQL

INICIO = "2026-09-01T00:00:00Z"
FIM = "2026-09-02T00:00:00Z"


def resposta(corpo):
    return io.BytesIO(json.dumps(corpo).encode())


class FontesTest(unittest.TestCase):
    def test_api_paginada_com_mesmo_timestamp(self):
        paginas = [{"itens": [{"id_meta": 1, "atualizado_em": INICIO}], "proximo_cursor": "cursor-1"},
                   {"itens": [{"id_meta": 2, "atualizado_em": INICIO}], "proximo_cursor": None}]
        with patch("pipeline_comercial.fontes.urlopen", side_effect=[resposta(p) for p in paginas]) as get:
            registros = list(API("http://api", tamanho_pagina=1).extrair("metas", INICIO, FIM))
            self.assertEqual([r["id_meta"] for r in registros], [1, 2])
            self.assertIn("cursor=cursor-1", get.call_args.args[0])
            self.assertEqual(get.call_args.kwargs["timeout"], 30)

    def test_api_429_respeita_retry_after(self):
        erro = HTTPError("http://api", 429, "limite", {"Retry-After": "3"}, None)
        dormir = Mock()
        with patch("pipeline_comercial.fontes.urlopen", side_effect=[erro, resposta({"itens": []})]):
            self.assertEqual(list(API("http://api", dormir=dormir).extrair("metas", INICIO, FIM)), [])
        dormir.assert_called_once_with(3)

    def test_api_erro_4xx_nao_e_repetido(self):
        with patch("pipeline_comercial.fontes.urlopen", side_effect=HTTPError("api", 401, "negado", {}, None)) as get:
            with self.assertRaises(HTTPError):
                list(API("http://api").extrair("metas", INICIO, FIM))
            self.assertEqual(get.call_count, 1)

    def test_api_esgota_tentativas_de_rede(self):
        dormir = Mock()
        with patch("pipeline_comercial.fontes.urlopen", side_effect=URLError("rede")) as get:
            with self.assertRaises(URLError):
                list(API("http://api", dormir=dormir).extrair("metas", INICIO, FIM))
        self.assertEqual(get.call_count, 3)
        self.assertEqual(dormir.call_count, 2)

    def test_api_cursor_repetido_e_rejeitado(self):
        pagina = {"itens": [{"atualizado_em": INICIO}], "proximo_cursor": "igual"}
        with patch("pipeline_comercial.fontes.urlopen", side_effect=[resposta(pagina), resposta(pagina)]):
            with self.assertRaises(ValueError):
                list(API("http://api").extrair("metas", INICIO, FIM))

    def test_api_registro_fora_da_janela_e_rejeitado(self):
        with patch("pipeline_comercial.fontes.urlopen", return_value=resposta({"itens": [{"atualizado_em": FIM}]})):
            with self.assertRaises(ValueError):
                list(API("http://api").extrair("metas", INICIO, FIM))

    def test_postgres_paginacao_keyset_e_snapshot(self):
        tempo = datetime(2026, 9, 1, tzinfo=timezone.utc)
        db = Mock()
        db.__enter__ = Mock(return_value=db)
        db.__exit__ = Mock(return_value=False)
        db.execute.side_effect = [None,
            Mock(fetchall=lambda: [{"id_vendedor": 1, "atualizado_em": tempo}]),
            Mock(fetchall=lambda: [{"id_vendedor": 2, "atualizado_em": tempo}]),
            Mock(fetchall=lambda: [])]
        modulo, rows = types.ModuleType("psycopg"), types.ModuleType("psycopg.rows")
        modulo.connect, rows.dict_row = Mock(return_value=db), object()
        with patch.dict(sys.modules, {"psycopg": modulo, "psycopg.rows": rows}):
            registros = list(PostgreSQL("dsn", tamanho_pagina=1).extrair("vendedores", INICIO, FIM))
        self.assertEqual([r["id_vendedor"] for r in registros], [1, 2])
        self.assertIn("REPEATABLE READ", db.execute.call_args_list[0].args[0])
        self.assertEqual(db.execute.call_args_list[2].args[1][2:4], (tempo, 1))
        self.assertEqual(db.execute.call_args_list[3].args[1][2:4], (tempo, 2))

    def test_entidade_nao_permitida_e_rejeitada(self):
        with self.assertRaises(ValueError):
            list(API("http://api").extrair("vendas", INICIO, FIM))
