import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pipeline_comercial.config import destino, publicar_sandbox
from pipeline_comercial.exemplo import dados_exemplo
from pipeline_comercial.modelo import TABELAS, deduplicar
from pipeline_comercial.sandbox import PublicadorSandbox, validar_faturamento


class SandboxTest(unittest.TestCase):
    def test_faturamento_vinculado_ou_indefinido_bloqueia(self):
        for info in ({}, {"billingEnabled": True},
                     {"billingEnabled": False, "billingAccountName": "billingAccounts/123"}):
            with self.subTest(info=info), self.assertRaises(ValueError):
                validar_faturamento(info)
        validar_faturamento({"billingEnabled": False})

    def publicador(self):
        publicador = object.__new__(PublicadorSandbox)
        publicador.projeto = "projeto-sandbox"
        publicador.localizacao = "US"
        publicador.verificar = Mock()
        publicador.cliente = Mock()
        publicador.cliente.load_table_from_file.return_value.job_id = "job-teste"
        publicador.bq = Mock()
        publicador.bq.LoadJobConfig = lambda **kw: kw
        return publicador

    def test_bloqueio_ocorre_antes_de_criar_ou_carregar(self):
        publicador = self.publicador()
        publicador.verificar.side_effect = ValueError("faturamento ativo")
        with self.assertRaises(ValueError):
            publicador.publicar({})
        publicador.cliente.create_dataset.assert_not_called()
        publicador.cliente.load_table_from_file.assert_not_called()

    def test_republicacao_substitui_seis_tabelas_sem_dml(self):
        publicador = self.publicador()
        dados = dados_exemplo()
        lotes = {e: deduplicar(e, dados[e]) for e in TABELAS}
        publicador.publicar(lotes)
        publicador.publicar(lotes)
        cargas = publicador.cliente.load_table_from_file.call_args_list
        self.assertEqual(len(cargas), 12)
        for i, entidade in enumerate(TABELAS):
            primeira, repetida = cargas[i], cargas[i + 6]
            self.assertEqual(primeira.args[1], "projeto-sandbox." + TABELAS[entidade][0])
            self.assertEqual(primeira.args[0].getvalue(), repetida.args[0].getvalue())
            linhas = primeira.args[0].getvalue().decode().splitlines()
            self.assertEqual([json.loads(l) for l in linhas], lotes[entidade])
            self.assertEqual(primeira.kwargs["job_config"]["write_disposition"],
                             publicador.bq.WriteDisposition.WRITE_TRUNCATE)
        publicador.cliente.query.assert_not_called()

    def test_falha_de_carga_e_propagada_para_retry(self):
        publicador = self.publicador()
        publicador.cliente.load_table_from_file.return_value.result.side_effect = RuntimeError("rede")
        with self.assertRaises(RuntimeError):
            publicador.publicar({e: [] for e in TABELAS})
        self.assertEqual(publicador.cliente.load_table_from_file.call_count, 1)

    def test_destino_local_persiste_entre_tarefas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = str(Path(pasta) / "dados/comercial.sqlite")
            with patch.dict(os.environ, {"PIPELINE_DESTINO": "local", "LOCAL_DB_PATH": caminho}):
                db = destino()
                db.iniciar("execucao-1", "2026-10-03T00:00:00Z")
                db.close()
                db = destino()
                self.assertEqual(db.contexto("execucao-1")["status"], "iniciada")
                db.close()

    def test_sandbox_exige_publicacao_local_concluida(self):
        with patch.dict(os.environ, {"PIPELINE_DESTINO": "sandbox"}):
            db = Mock()
            db.contexto.return_value = {"status": "falha"}
            with self.assertRaises(ValueError):
                publicar_sandbox(db, "execucao-1")

    def test_modo_local_nao_acessa_nuvem(self):
        with patch.dict(os.environ, {"PIPELINE_DESTINO": "local"}):
            db = Mock()
            publicar_sandbox(db, "execucao-1")
            db.contexto.assert_not_called()
