import unittest
from decimal import Decimal
from unittest.mock import patch

from pipeline_comercial.exemplo import dados_exemplo, segundo_dia
from pipeline_comercial.fontes import FonteMemoria
from pipeline_comercial.local import DestinoLocal
from pipeline_comercial.modelo import deduplicar, normalizar, timestamp
from pipeline_comercial.pipeline import executar, extrair, preparar, conferir
from pipeline_comercial.qualidade import FalhaQualidade, validar

FIM1 = "2026-09-02T00:00:00Z"
FIM2 = "2026-09-03T00:00:00Z"


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.db = DestinoLocal(":memory:")
        self.dados = dados_exemplo()
        self.fonte = FonteMemoria(self.dados)
        self.addCleanup(self.db.close)

    def rodar(self, id="primeira", fim=FIM1):
        executar(self.db, self.fonte, self.fonte, id, fim)

    def marcas(self):
        return dict(self.db.db.execute("SELECT entidade,valor FROM watermarks"))

    def test_carga_inicial_e_reconciliacao(self):
        self.rodar()
        vendas = self.db.publicados()["vendas"]
        self.assertEqual(len(vendas), 2)
        self.assertEqual(sum(Decimal(v["valor_liquido"]) for v in vendas), Decimal("430.00"))
        self.assertEqual(set(self.marcas().values()), {timestamp(FIM1)})

    def test_reexecucao_mesmo_id_nao_duplica_raw_ou_fato(self):
        self.rodar()
        contagem = self.db.db.execute("SELECT COUNT(*) FROM raw").fetchone()[0]
        self.rodar()
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM raw").fetchone()[0], contagem)
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_novo_id_com_mesma_janela_nao_duplica_fato(self):
        self.rodar()
        self.rodar("repeticao", FIM1)
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_correcao_cancelamento_nova_venda(self):
        self.rodar()
        segundo_dia(self.dados)
        self.rodar("segunda", FIM2)
        vendas = {r["id_lancamento"]: r for r in self.db.publicados()["vendas"]}
        self.assertEqual(len(vendas), 3)
        self.assertEqual(vendas[1001]["valor_liquido"], "270.00")
        self.assertTrue(vendas[1002]["cancelado"])
        self.assertEqual(sum(Decimal(r["valor_liquido"]) for r in vendas.values() if not r["cancelado"]), Decimal("330.00"))

    def test_dimensao_publicada_valida_incremental_sem_dimensoes_no_lote(self):
        self.rodar()
        segundo_dia(self.dados)
        self.rodar("segunda", FIM2)
        self.assertEqual(self.db.ler_staging("segunda")["vendedores"], [])
        self.assertEqual(self.db.contexto("segunda")["status"], "sucesso")

    def test_falha_qualidade_preserva_publicados_e_watermark(self):
        self.rodar()
        antes, marcas = self.db.publicados(), self.marcas()
        self.dados["vendas"][0].update(id_vendedor=999, atualizado_em="2026-09-02T10:00:00Z")
        with self.assertRaises(FalhaQualidade):
            self.rodar("segunda", FIM2)
        self.assertEqual(self.db.publicados(), antes)
        self.assertEqual(self.marcas(), marcas)
        self.assertEqual(self.db.contexto("segunda")["status"], "falha")

    def test_recuperacao_mesmo_id_preserva_janela_e_corrige_raw(self):
        self.rodar()
        self.dados["vendas"][0].update(id_vendedor=999, atualizado_em="2026-09-02T10:00:00Z")
        with self.assertRaises(FalhaQualidade):
            self.rodar("segunda", FIM2)
        limites = self.db.contexto("segunda")["limites"]
        self.dados["vendas"][0].update(id_vendedor=1, atualizado_em="2026-09-02T11:00:00Z")
        self.rodar("segunda", FIM2)
        self.assertEqual(self.db.contexto("segunda")["limites"], limites)
        self.assertEqual(self.db.contexto("segunda")["status"], "sucesso")

    def test_falha_api_nao_publica_erp_parcial(self):
        class ForaDoAr:
            def extrair(self, *args):
                raise ConnectionError("API indisponível")
        with self.assertRaises(ConnectionError):
            executar(self.db, self.fonte, ForaDoAr(), "primeira", FIM1)
        self.assertEqual(self.db.publicados()["vendas"], [])
        self.assertEqual(self.marcas(), {})
        self.assertGreater(len(self.db.ler_raw("primeira", "vendas")), 0)
        self.rodar()
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_rollback_durante_publicacao_reverte_dimensoes_e_marcas(self):
        self.db.iniciar("primeira", FIM1)
        extrair(self.db, "primeira", self.fonte, list(self.dados))
        preparar(self.db, "primeira")
        conferir(self.db, "primeira")
        with self.assertRaises(RuntimeError):
            self.db.publicar("primeira", falhar_apos=1)
        self.assertTrue(all(not registros for registros in self.db.publicados().values()))
        self.assertEqual(self.marcas(), {})
        self.db.publicar("primeira")
        self.assertEqual(self.db.contexto("primeira")["status"], "sucesso")

    def test_publicacao_sem_qualidade_e_barrada(self):
        self.db.iniciar("primeira", FIM1)
        with self.assertRaises(ValueError):
            self.db.publicar("primeira")

    def test_intervalo_exclusivo_e_empate_timestamp(self):
        self.dados["vendas"][0]["atualizado_em"] = FIM1
        self.rodar()
        self.assertEqual(len(self.db.publicados()["vendas"]), 1)
        self.rodar("segunda", FIM2)
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_lookback_captura_atraso_curto(self):
        self.rodar()
        self.dados["vendas"][0].update(valor_desconto="25.00", atualizado_em="2026-09-01T23:58:00Z")
        self.rodar("segunda", FIM2)
        venda = next(r for r in self.db.publicados()["vendas"] if r["id_lancamento"] == 1001)
        self.assertEqual(venda["valor_liquido"], "275.00")

    def test_lote_vazio_avanca_watermark(self):
        self.rodar()
        self.rodar("segunda", FIM2)
        self.assertTrue(all(not r for r in self.db.ler_staging("segunda").values()))
        self.assertEqual(set(self.marcas().values()), {timestamp(FIM2)})

    def test_reexecucao_antiga_nao_regride_watermark_ou_dado(self):
        self.rodar()
        segundo_dia(self.dados)
        self.rodar("segunda", FIM2)
        self.rodar()
        self.assertEqual(set(self.marcas().values()), {timestamp(FIM2)})
        self.assertEqual(len(self.db.publicados()["vendas"]), 3)

    def test_nova_execucao_antiga_rejeitada(self):
        self.rodar()
        with self.assertRaises(ValueError):
            self.rodar("antiga", "2026-09-01T00:00:00Z")

    def test_mesmo_id_outro_fim_rejeitado_sem_alterar_sucesso(self):
        self.rodar()
        with self.assertRaises(ValueError):
            self.rodar("primeira", FIM2)
        self.assertEqual(self.db.contexto("primeira")["status"], "sucesso")

    def test_deduplicacao_mais_recente_e_conflito(self):
        antigo = self.dados["vendas"][0]
        novo = {**antigo, "valor_desconto": "30.00", "atualizado_em": "2026-09-02T10:00:00Z"}
        self.assertEqual(deduplicar("vendas", [novo, antigo, novo])[0]["valor_liquido"], "270.00")
        with self.assertRaises(ValueError):
            deduplicar("vendas", [antigo, {**antigo, "valor_desconto": "21.00"}])

    def test_dinheiro_decimal_e_booleano_estrito(self):
        venda = {**self.dados["vendas"][0], "valor_bruto": "0.30", "valor_desconto": "0.10"}
        self.assertEqual(normalizar("vendas", venda)["valor_liquido"], "0.20")
        for campo, valor in (("cancelado", "false"), ("valor_bruto", "1.001"), ("id_lancamento", True)):
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                normalizar("vendas", {**venda, campo: valor})

    def test_timestamp_sem_fuso_e_rejeitado(self):
        with self.assertRaises(ValueError):
            timestamp("2026-09-01T10:00:00")

    def test_valor_negativo_desconto_excessivo_quantidade_zero(self):
        for campo, valor in (("valor_bruto", "-1.00"), ("valor_desconto", "999.00"), ("quantidade", 0)):
            with self.subTest(campo=campo):
                dados = dados_exemplo()
                dados["vendas"][0][campo] = valor
                lotes = {e: deduplicar(e, l) for e, l in dados.items()}
                with self.assertRaises(FalhaQualidade):
                    validar(lotes, {e: [] for e in dados})

    def test_meta_duplicada_por_vendedor_competencia(self):
        self.dados["metas"].append({**self.dados["metas"][0], "id_meta": 3})
        with self.assertRaises(FalhaQualidade):
            self.rodar()

    def test_meta_negativa_ou_competencia_invalida(self):
        for campo, valor in (("valor_meta", "-1.00"), ("competencia", "2026-09-02")):
            dados = dados_exemplo()
            dados["metas"][0][campo] = valor
            with self.subTest(campo=campo), self.assertRaises(FalhaQualidade):
                validar({e: deduplicar(e, l) for e, l in dados.items()}, {e: [] for e in dados})

    def test_falha_normalizacao_preserva_watermark(self):
        self.dados["vendas"][0]["valor_bruto"] = "invalido"
        with self.assertRaises(Exception):
            self.rodar()
        self.assertEqual(self.marcas(), {})

    def test_mudanca_sem_timestamp_nao_sobrescreve_publicado(self):
        self.rodar()
        # Reentra pelo lookback, mas mantém a versão já publicada.
        venda = self.db.publicados()["vendas"][0]
        alterada = {**venda, "valor_desconto": "30.00", "valor_liquido": "270.00"}
        with self.assertRaises(FalhaQualidade):
            validar({e: [alterada] if e == "vendas" else [] for e in self.dados}, self.db.publicados())

    def test_retry_apos_resposta_perdida_do_commit(self):
        publicar = self.db.publicar

        def perder_resposta(execucao):
            publicar(execucao)
            raise TimeoutError("Resposta perdida depois do commit")

        with patch.object(self.db, "publicar", side_effect=perder_resposta):
            with self.assertRaises(TimeoutError):
                self.rodar()
        self.assertEqual(self.db.contexto("primeira")["status"], "sucesso")
        self.rodar()
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_retry_extracao_parcial_nao_duplica_raw(self):
        self.db.iniciar("primeira", FIM1)
        registros = [{**self.dados["vendedores"][0], "id_vendedor": i} for i in range(1, 502)]

        class Parcial:
            def extrair(self, *args):
                yield from registros[:500]
                raise ConnectionError("Origem desconectou após primeira página")

        with self.assertRaises(ConnectionError):
            extrair(self.db, "primeira", Parcial(), ["vendedores"])
        self.assertEqual(len(self.db.ler_raw("primeira", "vendedores")), 500)
        extrair(self.db, "primeira", FonteMemoria({"vendedores": registros}), ["vendedores"])
        self.assertEqual(len(self.db.ler_raw("primeira", "vendedores")), 501)

    def test_payload_invalido_corrigido_em_versao_mais_nova(self):
        self.dados["vendas"][0]["valor_bruto"] = "invalido"
        with self.assertRaises(Exception):
            self.rodar()
        self.dados["vendas"][0].update(valor_bruto="300.00", atualizado_em="2026-09-01T11:00:00Z")
        self.rodar()
        self.assertEqual(self.db.contexto("primeira")["status"], "sucesso")
        self.assertEqual(len(self.db.publicados()["vendas"]), 2)

    def test_falha_no_registro_operacional_preserva_erro_original(self):
        class ForaDoAr:
            def extrair(self, *args):
                raise ConnectionError("API indisponível")

        with patch.object(self.db, "falha", side_effect=RuntimeError("Warehouse indisponível")):
            with self.assertLogs("pipeline_comercial.pipeline", level="ERROR"):
                with self.assertRaisesRegex(ConnectionError, "API indisponível"):
                    executar(self.db, self.fonte, ForaDoAr(), "primeira", FIM1)


if __name__ == "__main__":
    unittest.main()
