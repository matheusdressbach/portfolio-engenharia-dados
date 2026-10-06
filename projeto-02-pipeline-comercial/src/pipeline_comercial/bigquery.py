import hashlib
import json
import re
from datetime import timedelta
from importlib.resources import files

from .local import EPOCA
from .modelo import TABELAS, instante, timestamp


class DestinoBigQuery:
    def __init__(self, projeto, localizacao="US", cliente=None):
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", projeto):
            raise ValueError("ID de projeto Google Cloud inválido")
        from google.cloud import bigquery
        self.bq = bigquery
        self.cliente = cliente or bigquery.Client(project=projeto, location=localizacao)
        self.projeto, self.localizacao = projeto, localizacao

    def _query(self, sql, **parametros):
        config = self.bq.QueryJobConfig(query_parameters=[
            self.bq.ScalarQueryParameter(k, "STRING", v) for k, v in parametros.items()])
        return list(self.cliente.query(sql.replace("__PROJETO__", self.projeto),
                                      job_config=config, location=self.localizacao).result())

    def bootstrap(self):
        for dataset in ("raw", "staging", "dm", "comercial", "operacao"):
            objeto = self.bq.Dataset(f"{self.projeto}.{dataset}")
            objeto.location = self.localizacao
            self.cliente.create_dataset(objeto, exists_ok=True)
        self._query(files("pipeline_comercial").joinpath("sql/estrutura.sql").read_text())

    def iniciar(self, execucao, fim):
        existente = self._query("SELECT fim,limites,status FROM `__PROJETO__.operacao.execucoes` WHERE id=@id", id=execucao)
        if existente:
            contexto = self.contexto(execucao)
            if timestamp(fim) != contexto["fim"]:
                raise ValueError("Execução já existe com outro limite superior")
            return contexto
        marcas = {r.entidade: timestamp(r.valor) for r in self._query(
            "SELECT entidade,valor FROM `__PROJETO__.operacao.watermarks`")}
        if any(instante(fim) < instante(m) for m in marcas.values()):
            raise ValueError("Fim anterior ao watermark")
        limites = {e: timestamp(instante(marcas.get(e, EPOCA)) - timedelta(minutes=5)) for e in TABELAS}
        self._query("""INSERT INTO `__PROJETO__.operacao.execucoes`
            (id,fim,limites,status,atualizado_em)
            SELECT @id, TIMESTAMP(@fim), @limites, 'iniciada', CURRENT_TIMESTAMP()
            WHERE NOT EXISTS (SELECT 1 FROM `__PROJETO__.operacao.execucoes` WHERE id=@id)""",
            id=execucao, fim=timestamp(fim), limites=json.dumps(limites))
        return self.contexto(execucao)

    def contexto(self, execucao):
        linhas = self._query("SELECT fim,limites,status FROM `__PROJETO__.operacao.execucoes` WHERE id=@id", id=execucao)
        if len(linhas) != 1:
            raise ValueError("Execução inexistente ou duplicada; mantenha somente um escritor")
        r = linhas[0]
        return {"fim": timestamp(r.fim), "limites": json.loads(r.limites), "status": r.status}

    def _carregar(self, tabela, linhas, schema):
        if not linhas:
            return
        from google.api_core.exceptions import Conflict, ServiceUnavailable, InternalServerError, TooManyRequests
        conteudo = json.dumps(linhas, sort_keys=True, default=str).encode()
        job_id = "carga_" + hashlib.sha256(tabela.encode() + conteudo).hexdigest()
        config = self.bq.LoadJobConfig(schema=schema, write_disposition="WRITE_APPEND")
        # Um job que falhou não pode ser reutilizado: cada tentativa tem um ID estável.
        for tentativa in range(3):
            identificador = f"{job_id}_{tentativa}"
            try:
                try:
                    job = self.cliente.load_table_from_json(linhas, f"{self.projeto}.{tabela}",
                               job_id=identificador, job_config=config, location=self.localizacao)
                except Conflict:
                    job = self.cliente.get_job(identificador, location=self.localizacao)
                job.result()
                return
            except (ServiceUnavailable, InternalServerError, TooManyRequests):
                if tentativa == 2:
                    raise

    def gravar_raw(self, execucao, entidade, registros):
        chave = TABELAS[entidade][1]
        linhas = [{"execucao": execucao, "entidade": entidade, "chave": str(r[chave]),
                   "versao": timestamp(r["atualizado_em"]),
                   "payload": json.dumps(r, sort_keys=True, default=str)} for r in registros]
        self._carregar("raw.registros", linhas, [self.bq.SchemaField(c, t) for c, t in
            (("execucao", "STRING"), ("entidade", "STRING"), ("chave", "STRING"),
             ("versao", "TIMESTAMP"), ("payload", "STRING"))])

    def ler_raw(self, execucao, entidade):
        return [json.loads(r.payload) for r in self._query(
            "SELECT DISTINCT payload FROM `__PROJETO__.raw.registros` WHERE execucao=@id AND entidade=@entidade",
            id=execucao, entidade=entidade)]

    def gravar_staging(self, execucao, lotes):
        for entidade, linhas in lotes.items():
            schema = [self.bq.SchemaField("execucao", "STRING")] + [
                self.bq.SchemaField(c, t) for c, t in TABELAS[entidade][2].items()]
            self._carregar(f"staging.{entidade}", [{"execucao": execucao, **r} for r in linhas], schema)
        self._status(execucao, "preparada")

    def ler_staging(self, execucao):
        from .modelo import deduplicar
        return {e: deduplicar(e, [dict(r) for r in self._query(
            f"SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.{e}` WHERE execucao=@id", id=execucao)])
            for e in TABELAS}

    def publicados(self):
        from .modelo import normalizar
        return {e: [normalizar(e, dict(r)) for r in self._query(f"SELECT * FROM `__PROJETO__.{tabela}`")]
                for e, (tabela, _, _) in TABELAS.items()}

    def _status(self, execucao, status, erro=None):
        self._query("""UPDATE `__PROJETO__.operacao.execucoes`
            SET status=@status, erro=@erro, atualizado_em=CURRENT_TIMESTAMP()
            WHERE id=@id AND status!='sucesso'""", id=execucao, status=status, erro=erro)

    def aprovar(self, execucao):
        self._status(execucao, "aprovada")

    def publicar(self, execucao):
        self._query(files("pipeline_comercial").joinpath("sql/publicar.sql").read_text(), id=execucao)

    def falha(self, execucao, erro):
        self._status(execucao, "falha", str(erro)[:2000])

    def close(self):
        self.cliente.close()
