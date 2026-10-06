from decimal import Decimal

from .modelo import TABELAS


class FalhaQualidade(ValueError):
    pass


def validar(lotes, publicados):
    """Valida o estado candidato completo, incluindo dimensões já publicadas."""
    candidato = {}
    erros = []
    for entidade, (_, chave, _) in TABELAS.items():
        registros = {r[chave]: r for r in publicados[entidade]}
        for r in lotes[entidade]:
            anterior = registros.get(r[chave])
            if anterior and r["atualizado_em"] == anterior["atualizado_em"] and r != anterior:
                erros.append(f"{entidade}/{r[chave]}: alteração sem atualizar timestamp")
            if not anterior or r["atualizado_em"] >= anterior["atualizado_em"]:
                registros[r[chave]] = r
        candidato[entidade] = registros
    for entidade, registros in candidato.items():
        for chave, r in registros.items():
            if chave <= 0:
                erros.append(f"{entidade}: chave não positiva {chave}")
            if entidade in ("vendas", "metas"):
                for dimensao, campo in (("vendedores", "id_vendedor"),
                                        ("clientes", "id_cliente"), ("produtos", "id_produto")):
                    if campo in r and r[campo] not in candidato[dimensao]:
                        erros.append(f"{entidade}/{chave}: {campo} sem dimensão")
            if entidade == "clientes" and (len(r["uf"]) != 2 or not r["uf"].isupper()):
                erros.append(f"cliente/{chave}: UF inválida")
            if entidade == "vendas":
                bruto, desconto, liquido = (Decimal(r[c]) for c in
                                           ("valor_bruto", "valor_desconto", "valor_liquido"))
                if r["quantidade"] <= 0 or bruto < 0 or desconto < 0 or desconto > bruto:
                    erros.append(f"venda/{chave}: quantidade ou valores inválidos")
                if liquido != bruto - desconto:
                    erros.append(f"venda/{chave}: líquido divergente")
            if entidade == "metas":
                if Decimal(r["valor_meta"]) < 0 or not r["competencia"].endswith("-01"):
                    erros.append(f"meta/{chave}: valor/competência inválido")
    devolvido = {}
    for chave, r in candidato["devolucoes"].items():
        venda = candidato["vendas"].get(r["id_lancamento"])
        if not venda:
            erros.append(f"devolucao/{chave}: lançamento sem venda")
            continue
        if venda["cancelado"]:
            erros.append(f"devolucao/{chave}: venda cancelada")
        if r["quantidade"] <= 0 or Decimal(r["valor_devolvido"]) <= 0:
            erros.append(f"devolucao/{chave}: quantidade ou valor inválido")
        if r["data_devolucao"] < venda["data_venda"] or not r["motivo"].strip():
            erros.append(f"devolucao/{chave}: data ou motivo inválido")
        quantidade, valor = devolvido.get(r["id_lancamento"], (0, Decimal(0)))
        devolvido[r["id_lancamento"]] = (quantidade + r["quantidade"], valor + Decimal(r["valor_devolvido"]))
    for chave, (quantidade, valor) in devolvido.items():
        venda = candidato["vendas"][chave]
        if quantidade > venda["quantidade"] or valor > Decimal(venda["valor_liquido"]):
            erros.append(f"devolucoes/{chave}: acumulado superior à venda")
    naturais = [(r["id_vendedor"], r["competencia"]) for r in candidato["metas"].values()]
    if len(naturais) != len(set(naturais)):
        erros.append("Mais de uma meta para vendedor e competência")
    if erros:
        raise FalhaQualidade("; ".join(erros[:20]))
    return {"regras": "aprovadas", "registros_candidatos": sum(map(len, candidato.values()))}
