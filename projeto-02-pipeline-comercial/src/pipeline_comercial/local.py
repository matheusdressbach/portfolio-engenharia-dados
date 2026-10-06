"""Destino SQLite para demonstração e testes; não emula o motor SQL do BigQuery."""
import json
import sqlite3
from datetime import timedelta

from .modelo import TABELAS, instante, timestamp

EPOCA = "1970-01-01T00:00:00.000000+00:00"


class DestinoLocal:
    def __init__(self, caminho):
        self.db = sqlite3.connect(caminho, timeout=60)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS execucoes (
          id TEXT PRIMARY KEY, fim TEXT, limites TEXT, status TEXT, erro TEXT);
        CREATE TABLE IF NOT EXISTS watermarks (entidade TEXT PRIMARY KEY, valor TEXT);
        CREATE TABLE IF NOT EXISTS raw (
          execucao TEXT, entidade TEXT, chave TEXT, versao TEXT, payload TEXT,
          PRIMARY KEY (execucao, entidade, chave, versao));
        CREATE TABLE IF NOT EXISTS staging (
          execucao TEXT, entidade TEXT, chave TEXT, payload TEXT,
          PRIMARY KEY (execucao, entidade, chave));
        CREATE TABLE IF NOT EXISTS publicados (
          entidade TEXT, chave TEXT, payload TEXT, PRIMARY KEY (entidade, chave));
        """)

    def iniciar(self, execucao, fim):
        existente = self.db.execute("SELECT fim,limites,status FROM execucoes WHERE id=?", (execucao,)).fetchone()
        if existente:
            if timestamp(fim) != existente[0]:
                raise ValueError("Execução já existe com outro limite superior")
            return {"fim": existente[0], "limites": json.loads(existente[1]), "status": existente[2]}
        limites = {}
        for entidade in TABELAS:
            linha = self.db.execute("SELECT valor FROM watermarks WHERE entidade=?", (entidade,)).fetchone()
            watermark = linha[0] if linha else EPOCA
            if instante(fim) < instante(watermark):
                raise ValueError("Fim anterior ao watermark; use uma nova execução corrente")
            limites[entidade] = timestamp(instante(watermark) - timedelta(minutes=5))
        with self.db:
            self.db.execute("INSERT INTO execucoes VALUES (?,?,?,?,NULL)",
                            (execucao, timestamp(fim), json.dumps(limites), "iniciada"))
        return {"fim": timestamp(fim), "limites": limites, "status": "iniciada"}

    def contexto(self, execucao):
        linha = self.db.execute("SELECT fim,limites,status FROM execucoes WHERE id=?", (execucao,)).fetchone()
        if not linha:
            raise ValueError("Execução não iniciada")
        return {"fim": linha[0], "limites": json.loads(linha[1]), "status": linha[2]}

    def gravar_raw(self, execucao, entidade, registros):
        chave = TABELAS[entidade][1]
        with self.db:
            for r in registros:
                versao = timestamp(r["atualizado_em"])
                existente = self.db.execute(
                    "SELECT payload FROM raw WHERE execucao=? AND entidade=? AND chave=? AND versao=?",
                    (execucao, entidade, str(r[chave]), versao)).fetchone()
                payload = json.dumps(r, sort_keys=True, default=str)
                if existente and existente[0] != payload:
                    raise ValueError("Fonte alterou uma versão já extraída; atualizado_em deve mudar")
                self.db.execute("INSERT OR IGNORE INTO raw VALUES (?,?,?,?,?)",
                                (execucao, entidade, str(r[chave]), versao, payload))

    def ler_raw(self, execucao, entidade):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT payload FROM raw WHERE execucao=? AND entidade=?", (execucao, entidade))]

    def gravar_staging(self, execucao, lotes):
        with self.db:
            self.db.execute("DELETE FROM staging WHERE execucao=?", (execucao,))
            for entidade, registros in lotes.items():
                chave = TABELAS[entidade][1]
                self.db.executemany("INSERT INTO staging VALUES (?,?,?,?)", [
                    (execucao, entidade, str(r[chave]), json.dumps(r)) for r in registros])
            self.db.execute("UPDATE execucoes SET status='preparada',erro=NULL WHERE id=?", (execucao,))

    def ler_staging(self, execucao):
        return {e: [json.loads(r[0]) for r in self.db.execute(
            "SELECT payload FROM staging WHERE execucao=? AND entidade=?", (execucao, e))] for e in TABELAS}

    def publicados(self):
        return {e: [json.loads(r[0]) for r in self.db.execute(
            "SELECT payload FROM publicados WHERE entidade=?", (e,))] for e in TABELAS}

    def aprovar(self, execucao):
        with self.db:
            self.db.execute("UPDATE execucoes SET status='aprovada',erro=NULL WHERE id=?", (execucao,))

    def publicar(self, execucao, falhar_apos=None):
        contexto = self.contexto(execucao)
        if contexto["status"] == "sucesso":
            return
        if contexto["status"] != "aprovada":
            raise ValueError("Publicação exige qualidade aprovada")
        with self.db:
            for i, (entidade, registros) in enumerate(self.ler_staging(execucao).items()):
                chave = TABELAS[entidade][1]
                for r in registros:
                    anterior = self.db.execute("SELECT payload FROM publicados WHERE entidade=? AND chave=?",
                                               (entidade, str(r[chave]))).fetchone()
                    if not anterior or r["atualizado_em"] >= json.loads(anterior[0])["atualizado_em"]:
                        self.db.execute("INSERT OR REPLACE INTO publicados VALUES (?,?,?)",
                                        (entidade, str(r[chave]), json.dumps(r)))
                if i == falhar_apos:
                    raise RuntimeError("Falha simulada durante publicação")
                anterior = self.db.execute("SELECT valor FROM watermarks WHERE entidade=?", (entidade,)).fetchone()
                valor = max(contexto["fim"], anterior[0] if anterior else EPOCA)
                self.db.execute("INSERT OR REPLACE INTO watermarks VALUES (?,?)", (entidade, valor))
            self.db.execute("UPDATE execucoes SET status='sucesso',erro=NULL WHERE id=?", (execucao,))

    def falha(self, execucao, erro):
        with self.db:
            self.db.execute("UPDATE execucoes SET status='falha',erro=? WHERE id=? AND status!='sucesso'",
                            (str(erro)[:2000], execucao))

    def close(self):
        self.db.close()
