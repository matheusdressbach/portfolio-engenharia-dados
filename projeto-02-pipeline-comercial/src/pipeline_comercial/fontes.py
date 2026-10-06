import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .modelo import TABELAS, timestamp, instante


class PostgreSQL:
    def __init__(self, dsn, tamanho_pagina=500):
        self.dsn, self.tamanho_pagina = dsn, tamanho_pagina

    def extrair(self, entidade, inicio, fim):
        import psycopg
        from psycopg.rows import dict_row
        if entidade not in TABELAS or entidade == "metas":
            raise ValueError("Entidade não pertence ao ERP")
        chave = TABELAS[entidade][1]
        with psycopg.connect(self.dsn, row_factory=dict_row) as db:
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            cursor_tempo, cursor_id = inicio, -1
            while True:
                pagina = db.execute(f"""SELECT * FROM erp.{entidade}
                    WHERE atualizado_em >= %s AND atualizado_em < %s
                      AND (atualizado_em, {chave}) > (%s::timestamptz, %s)
                    ORDER BY atualizado_em, {chave} LIMIT %s""",
                    (inicio, fim, cursor_tempo, cursor_id, self.tamanho_pagina)).fetchall()
                if not pagina:
                    break
                for r in pagina:
                    yield {k: (v.isoformat() if hasattr(v, "isoformat") else
                               str(v) if type(v).__name__ == "Decimal" else v) for k, v in r.items()}
                cursor_tempo, cursor_id = pagina[-1]["atualizado_em"], pagina[-1][chave]


class API:
    def __init__(self, url, tamanho_pagina=500, tentativas=3, dormir=time.sleep):
        self.url, self.tamanho_pagina = url.rstrip("/"), tamanho_pagina
        self.tentativas, self.dormir = tentativas, dormir

    def _get(self, parametros):
        for tentativa in range(self.tentativas):
            try:
                with urlopen(f"{self.url}/metas?{urlencode(parametros)}", timeout=30) as resposta:
                    return json.load(resposta)
            except (HTTPError, URLError, TimeoutError) as erro:
                if isinstance(erro, HTTPError) and erro.code not in (429, 500, 502, 503, 504):
                    raise
                if tentativa == self.tentativas - 1:
                    raise
                atraso = 2 ** tentativa
                if isinstance(erro, HTTPError):
                    try:
                        atraso = min(60, max(atraso, int(erro.headers.get("Retry-After", "0"))))
                    except ValueError:
                        pass
                self.dormir(atraso)

    def extrair(self, entidade, inicio, fim):
        if entidade != "metas":
            raise ValueError("API fornece apenas metas")
        cursor = None
        vistos = set()
        while True:
            parametros = {"inicio": inicio, "fim": fim, "limite": self.tamanho_pagina}
            if cursor:
                parametros["cursor"] = cursor
            pagina = self._get(parametros)
            itens = pagina["itens"]
            if not isinstance(itens, list):
                raise ValueError("Contrato da API: itens deve ser lista")
            for r in itens:
                if not instante(inicio) <= instante(r["atualizado_em"]) < instante(fim):
                    raise ValueError("API devolveu registro fora da janela")
                yield r
            cursor = pagina.get("proximo_cursor")
            if not cursor:
                break
            if cursor in vistos or not itens:
                raise ValueError("API não avançou a paginação")
            vistos.add(cursor)


class FonteMemoria:
    def __init__(self, dados):
        self.dados = dados

    def extrair(self, entidade, inicio, fim):
        return [dict(r) for r in self.dados[entidade]
                if timestamp(inicio) <= timestamp(r["atualizado_em"]) < timestamp(fim)]
