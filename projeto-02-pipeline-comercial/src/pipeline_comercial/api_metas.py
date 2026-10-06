"""API REST local com contrato incremental; não é um serviço de produção."""
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .modelo import instante


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo):
        payload = json.dumps(corpo, default=str).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/health":
            self.responder(200, {"status": "ok"})
            return
        if url.path != "/metas":
            self.responder(404, {"erro": "Recurso inexistente"})
            return
        try:
            parametros = parse_qs(url.query)
            inicio, fim = parametros["inicio"][0], parametros["fim"][0]
            if instante(inicio) >= instante(fim):
                raise ValueError("Janela inválida")
            limite = int(parametros.get("limite", ["500"])[0])
            if not 1 <= limite <= 1000:
                raise ValueError("limite deve estar entre 1 e 1000")
            cursor_tempo, cursor_id = inicio, -1
            if "cursor" in parametros:
                cursor_tempo, cursor_id = json.loads(base64.urlsafe_b64decode(parametros["cursor"][0]))
                instante(cursor_tempo)
                cursor_id = int(cursor_id)
        except (KeyError, ValueError, TypeError) as erro:
            self.responder(400, {"erro": str(erro)})
            return
        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(os.environ["API_DSN"], row_factory=dict_row) as db:
                linhas = db.execute("""SELECT * FROM planejamento.metas
                    WHERE atualizado_em >= %s AND atualizado_em < %s
                    AND (atualizado_em,id_meta) > (%s::timestamptz,%s)
                    ORDER BY atualizado_em,id_meta LIMIT %s""",
                    (inicio, fim, cursor_tempo, cursor_id, limite + 1)).fetchall()
            itens = [{k: v.isoformat() if hasattr(v, "isoformat") else
                      str(v) if type(v).__name__ == "Decimal" else v for k, v in r.items()}
                     for r in linhas[:limite]]
            proximo = None
            if len(linhas) > limite:
                ultimo = itens[-1]
                proximo = base64.urlsafe_b64encode(json.dumps(
                    [ultimo["atualizado_em"], ultimo["id_meta"]]).encode()).decode()
            self.responder(200, {"itens": itens, "proximo_cursor": proximo})
        except Exception:
            import logging
            logging.exception("Falha ao consultar metas")
            self.responder(503, {"erro": "Origem temporariamente indisponível"})


def main():
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()


if __name__ == "__main__":
    main()
