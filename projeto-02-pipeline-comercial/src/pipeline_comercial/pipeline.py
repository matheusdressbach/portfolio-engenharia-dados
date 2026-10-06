import json
import logging
import time

from .modelo import TABELAS, deduplicar
from .qualidade import validar

log = logging.getLogger(__name__)


def evento(execucao, etapa, **campos):
    log.info(json.dumps({"execucao": execucao, "etapa": etapa, **campos}, ensure_ascii=False))


def extrair(destino, execucao, fonte, entidades):
    contexto = destino.contexto(execucao)
    if contexto["status"] == "sucesso":
        return 0
    total = 0
    for entidade in entidades:
        inicio = time.monotonic()
        quantidade, buffer = 0, []
        for r in fonte.extrair(entidade, contexto["limites"][entidade], contexto["fim"]):
            buffer.append(r)
            quantidade += 1
            if len(buffer) == 500:
                destino.gravar_raw(execucao, entidade, buffer)
                buffer = []
        if buffer:
            destino.gravar_raw(execucao, entidade, buffer)
        evento(execucao, "extracao", entidade=entidade, registros=quantidade,
               segundos=round(time.monotonic() - inicio, 3))
        total += quantidade
    return total


def preparar(destino, execucao):
    if destino.contexto(execucao)["status"] == "sucesso":
        return
    lotes = {e: deduplicar(e, destino.ler_raw(execucao, e)) for e in TABELAS}
    destino.gravar_staging(execucao, lotes)
    evento(execucao, "staging", contagens={e: len(l) for e, l in lotes.items()})


def conferir(destino, execucao):
    if destino.contexto(execucao)["status"] == "sucesso":
        return
    resultado = validar(destino.ler_staging(execucao), destino.publicados())
    destino.aprovar(execucao)
    evento(execucao, "qualidade", **resultado)


def executar(destino, fonte_erp, fonte_api, execucao, fim):
    try:
        contexto = destino.iniciar(execucao, fim)
        if contexto["status"] == "sucesso":
            evento(execucao, "reexecucao", status="já publicada")
            return
        extrair(destino, execucao, fonte_erp, [e for e in TABELAS if e != "metas"])
        extrair(destino, execucao, fonte_api, ["metas"])
        preparar(destino, execucao)
        conferir(destino, execucao)
        destino.publicar(execucao)
        evento(execucao, "publicacao", status="sucesso", watermark=contexto["fim"])
    except Exception as erro:
        try:
            destino.falha(execucao, erro)
        except Exception:
            log.exception("Não foi possível registrar a falha no destino; preserve o log da tarefa")
        evento(execucao, "falha", tipo=type(erro).__name__, mensagem=str(erro))
        raise


def limite_extracao(contexto):
    """Manuais usam a data lógica do disparo; agendadas usam o intervalo diário."""
    run = contexto["dag_run"]
    tipo = getattr(run.run_type, "value", run.run_type)
    limite = contexto["logical_date"] if tipo == "manual" else contexto["data_interval_end"]
    return limite.isoformat()
