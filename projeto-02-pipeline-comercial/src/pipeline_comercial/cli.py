import argparse
import json
import logging
from decimal import Decimal
from pathlib import Path

from .exemplo import dados_exemplo, segundo_dia
from .fontes import FonteMemoria
from .local import DestinoLocal
from .pipeline import executar


def demonstrar(caminho):
    if caminho != ":memory:":
        if Path(caminho).exists():
            raise ValueError("Use um caminho novo para a demonstração; ela preserva o arquivo existente")
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    db = DestinoLocal(caminho)
    try:
        dados = dados_exemplo()
        fonte = FonteMemoria(dados)
        executar(db, fonte, fonte, "dia-1", "2026-09-02T00:00:00Z")
        executar(db, fonte, fonte, "dia-1", "2026-09-02T00:00:00Z")
        segundo_dia(dados)
        executar(db, fonte, fonte, "dia-2", "2026-09-03T00:00:00Z")
        # Qualidade deve barrar um vendedor inexistente sem avançar watermark.
        dados["vendas"].append({**dados["vendas"][0], "id_lancamento": 1004,
                               "id_vendedor": 999, "atualizado_em": "2026-09-03T10:00:00Z"})
        from .qualidade import FalhaQualidade
        try:
            executar(db, fonte, fonte, "dia-3", "2026-09-04T00:00:00Z")
        except FalhaQualidade:
            pass
        else:
            raise AssertionError("A demonstração deveria rejeitar o vendedor inexistente")
        dados["vendas"][-1]["id_vendedor"] = 1
        dados["vendas"][-1]["atualizado_em"] = "2026-09-03T11:00:00Z"
        executar(db, fonte, fonte, "dia-3", "2026-09-04T00:00:00Z")
        vendas = db.publicados()["vendas"]
        total = sum((Decimal(r["valor_liquido"]) for r in vendas if not r["cancelado"]), Decimal(0))
        resultado = {"lancamentos": len(vendas), "cancelados": sum(r["cancelado"] for r in vendas),
                     "receita_liquida_ativa": str(total),
                     "watermarks": dict(db.db.execute("SELECT entidade,valor FROM watermarks")),
                     "execucoes": list(db.db.execute("SELECT id,status FROM execucoes ORDER BY id"))}
        assert len(vendas) == 4 and total == Decimal("600.00")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Pipeline comercial: demonstração local ou BigQuery")
    comandos = parser.add_subparsers(dest="comando", required=True)
    demo = comandos.add_parser("demo", help="Executa carga, repetição, correção, falha e recuperação")
    demo.add_argument("--banco", default=":memory:")
    comandos.add_parser("bootstrap", help="Cria datasets e tabelas no BigQuery")
    carga = comandos.add_parser("executar", help="Carga real PostgreSQL + API → BigQuery")
    carga.add_argument("--execucao", required=True)
    carga.add_argument("--fim", required=True, help="Timestamp com fuso; limite exclusivo")
    argumentos = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if argumentos.comando == "demo":
        demonstrar(argumentos.banco)
        return
    from .config import destino, fontes, publicar_sandbox
    db = destino()
    try:
        if argumentos.comando == "bootstrap":
            if hasattr(db, "bootstrap"):
                db.bootstrap()
        else:
            erp, api = fontes()
            executar(db, erp, api, argumentos.execucao, argumentos.fim)
            publicar_sandbox(db, argumentos.execucao)
    finally:
        db.close()


if __name__ == "__main__":
    main()
