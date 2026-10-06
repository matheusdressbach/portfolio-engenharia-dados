"""Payload fica no warehouse. XCom transporta somente contagens e identificadores."""
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from pipeline_comercial.config import destino, fontes, publicar_sandbox
from pipeline_comercial.pipeline import extrair, preparar, conferir, evento, limite_extracao


def registrar_falha(contexto):
    db = destino()
    try:
        db.falha(contexto["run_id"], contexto.get("exception", "Falha no Airflow"))
    finally:
        db.close()


@dag(
    dag_id="vendas_metas_diarias", schedule="0 9 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"), catchup=False,
    max_active_runs=1, dagrun_timeout=timedelta(hours=1),
    default_args={"owner": "dados", "retries": 2, "retry_delay": timedelta(minutes=1),
                  "retry_exponential_backoff": True, "max_retry_delay": timedelta(minutes=5),
                  "execution_timeout": timedelta(minutes=15), "on_failure_callback": registrar_falha},
    tags=["comercial", "incremental"],
    doc_md="Vendas do ERP e metas da API. Publicação e watermark na mesma transação.",
)
def vendas_metas_diarias():
    @task
    def iniciar_execucao():
        contexto = get_current_context()
        db = destino()
        try:
            # Limite exclusivo fixo em todos os retries deste DagRun.
            return db.iniciar(contexto["run_id"], limite_extracao(contexto))["fim"]
        finally:
            db.close()

    @task
    def extrair_postgresql():
        db = destino()
        try:
            return extrair(db, get_current_context()["run_id"], fontes()[0],
                           ["vendedores", "clientes", "produtos", "vendas", "devolucoes"])
        finally:
            db.close()

    @task
    def extrair_api():
        db = destino()
        try:
            return extrair(db, get_current_context()["run_id"], fontes()[1], ["metas"])
        finally:
            db.close()

    @task
    def transformar_staging():
        db = destino()
        try:
            preparar(db, get_current_context()["run_id"])
        finally:
            db.close()

    @task
    def validar_qualidade():
        db = destino()
        try:
            conferir(db, get_current_context()["run_id"])
        finally:
            db.close()

    @task
    def publicar_comercial():
        db = destino()
        try:
            execucao = get_current_context()["run_id"]
            db.publicar(execucao)
            evento(execucao, "publicacao", status="sucesso")
        finally:
            db.close()

    @task
    def sincronizar_sandbox():
        db = destino()
        try:
            publicar_sandbox(db, get_current_context()["run_id"])
        finally:
            db.close()

    inicio = iniciar_execucao()
    erp, api = extrair_postgresql(), extrair_api()
    staging = transformar_staging()
    inicio >> [erp, api]
    [erp, api] >> staging >> validar_qualidade() >> publicar_comercial() >> sincronizar_sandbox()


vendas_metas_diarias()
