import os
from pathlib import Path


def destino():
    modo = os.getenv("PIPELINE_DESTINO", "local")
    if modo in {"local", "sandbox"}:
        from .local import DestinoLocal
        caminho = os.getenv("LOCAL_DB_PATH", "/opt/airflow/dados/comercial.sqlite")
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        return DestinoLocal(caminho)
    if modo == "bigquery":
        from .bigquery import DestinoBigQuery
        return DestinoBigQuery(os.environ["GCP_PROJECT_ID"], os.getenv("BQ_LOCATION", "US"))
    raise ValueError("PIPELINE_DESTINO deve ser local, sandbox ou bigquery")


def publicar_sandbox(db, execucao):
    if os.getenv("PIPELINE_DESTINO", "local") != "sandbox":
        return
    if db.contexto(execucao)["status"] != "sucesso":
        raise ValueError("Sandbox recebe somente uma publicação local concluída")
    from .sandbox import PublicadorSandbox
    PublicadorSandbox(os.environ["GCP_PROJECT_ID"], os.getenv("BQ_LOCATION", "US")).publicar(db.publicados())


def fontes():
    from .fontes import PostgreSQL, API
    return PostgreSQL(os.environ["ERP_DSN"]), API(os.environ["METAS_API_URL"])
