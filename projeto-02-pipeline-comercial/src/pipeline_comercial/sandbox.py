"""Publica tabelas consolidadas por batch load; não executa DML no Sandbox."""
import io
import json
import logging

from .modelo import TABELAS

log = logging.getLogger(__name__)


def exigir_sem_faturamento(projeto):
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credenciais, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    with AuthorizedSession(credenciais) as sessao:
        resposta = sessao.get(
            f"https://cloudbilling.googleapis.com/v1/projects/{projeto}/billingInfo", timeout=30)
        resposta.raise_for_status()
        info = resposta.json()
    validar_faturamento(info)


def validar_faturamento(info):
    # Falha fechada: ausência da informação não autoriza a publicação.
    if info.get("billingEnabled") is not False or info.get("billingAccountName"):
        raise ValueError("Modo Sandbox exige projeto sem conta de faturamento vinculada")


class PublicadorSandbox:
    def __init__(self, projeto, localizacao="US", cliente=None, verificar=exigir_sem_faturamento):
        from google.cloud import bigquery
        if not projeto or projeto == "data-engineering-portfolio-md":
            raise ValueError("Informe o ID real do projeto exclusivo do Sandbox")
        self.bq = bigquery
        self.projeto = projeto
        self.localizacao = localizacao
        self.cliente = cliente or bigquery.Client(project=projeto, location=localizacao)
        self.verificar = verificar

    def publicar(self, lotes):
        self.verificar(self.projeto)
        for dataset in ("dm", "comercial"):
            recurso = self.bq.Dataset(f"{self.projeto}.{dataset}")
            recurso.location = self.localizacao
            recurso.default_table_expiration_ms = 60 * 24 * 60 * 60 * 1000
            self.cliente.create_dataset(recurso, exists_ok=True)
        for entidade, (tabela, _, campos) in TABELAS.items():
            configuracao = self.bq.LoadJobConfig(
                schema=[self.bq.SchemaField(campo, tipo, mode="REQUIRED") for campo, tipo in campos.items()],
                source_format=self.bq.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=self.bq.WriteDisposition.WRITE_TRUNCATE)
            conteudo = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lotes[entidade])
            job = self.cliente.load_table_from_file(
                io.BytesIO(conteudo.encode("utf-8")), f"{self.projeto}.{tabela}",
                job_config=configuracao, location=self.localizacao)
            job.result(timeout=600)
            log.info(json.dumps({"etapa": "sandbox", "tabela": tabela,
                                 "registros": len(lotes[entidade]), "job_id": job.job_id}))
