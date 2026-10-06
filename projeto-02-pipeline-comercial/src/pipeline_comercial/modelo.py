from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

# Grão: uma linha por lançamento do ERP; dimensões tipo 1.
TABELAS = {
    "vendedores": ("dm.dim_vendedores", "id_vendedor", {
        "id_vendedor": "INT64", "nome": "STRING", "ativo": "BOOL", "equipe": "STRING", "regiao": "STRING"}),
    "clientes": ("dm.dim_clientes", "id_cliente", {
        "id_cliente": "INT64", "nome": "STRING", "uf": "STRING", "cidade": "STRING", "segmento": "STRING"}),
    "produtos": ("dm.dim_produtos", "id_produto", {
        "id_produto": "INT64", "descricao": "STRING", "categoria": "STRING"}),
    "vendas": ("comercial.fato_lancamento_vendas", "id_lancamento", {
        "id_lancamento": "INT64", "id_vendedor": "INT64", "id_cliente": "INT64",
        "id_produto": "INT64", "data_venda": "DATE", "quantidade": "INT64",
        "valor_bruto": "NUMERIC", "valor_desconto": "NUMERIC", "valor_liquido": "NUMERIC",
        "cancelado": "BOOL"}),
    "devolucoes": ("comercial.fato_devolucoes", "id_devolucao", {
        "id_devolucao": "INT64", "id_lancamento": "INT64", "data_devolucao": "DATE",
        "quantidade": "INT64", "valor_devolvido": "NUMERIC", "motivo": "STRING"}),
    "metas": ("comercial.fato_metas_vendedores", "id_meta", {
        "id_meta": "INT64", "id_vendedor": "INT64", "competencia": "DATE",
        "valor_meta": "NUMERIC"}),
}
for _, _, campos in TABELAS.values():
    campos["atualizado_em"] = "TIMESTAMP"


def instante(valor):
    data = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    if data.tzinfo is None:
        raise ValueError("Timestamp deve informar fuso horário")
    return data.astimezone(timezone.utc)


def timestamp(valor):
    return instante(valor).isoformat(timespec="microseconds")


def dinheiro(valor):
    try:
        numero = Decimal(str(valor))
    except InvalidOperation as erro:
        raise ValueError("Valor monetário inválido") from erro
    if not numero.is_finite() or numero != numero.quantize(Decimal("0.01")):
        raise ValueError("Valor monetário exige até duas casas decimais")
    if abs(numero) >= Decimal("100000000000000000000000000000"):
        raise ValueError("Valor monetário fora do limite NUMERIC")
    return format(numero, ".2f")


def normalizar(entidade, registro):
    registro = dict(registro)
    # Compatibilidade com as pequenas fixtures e publicações da versão inicial.
    padroes = {"vendedores": {"equipe": "Não informado", "regiao": "Não informado"},
               "clientes": {"cidade": "Não informado", "segmento": "Não informado"},
               "produtos": {"categoria": "Não informado"}}
    registro = {**padroes.get(entidade, {}), **registro}
    if entidade == "vendas":
        registro["valor_liquido"] = dinheiro(
            Decimal(str(registro["valor_bruto"])) - Decimal(str(registro["valor_desconto"])))
    saida = {}
    for campo, tipo in TABELAS[entidade][2].items():
        valor = registro.get(campo)
        if valor is None:
            raise ValueError(f"{entidade}.{campo}: obrigatório")
        if tipo == "INT64":
            if isinstance(valor, bool) or str(valor) != str(int(valor)):
                raise ValueError(f"{campo}: inteiro inválido")
            valor = int(valor)
            if not -(2 ** 63) <= valor < 2 ** 63:
                raise ValueError(f"{campo}: fora do limite INT64")
        elif tipo == "NUMERIC":
            valor = dinheiro(valor)
        elif tipo == "TIMESTAMP":
            valor = timestamp(valor)
        elif tipo == "DATE":
            from datetime import date
            valor = date.fromisoformat(str(valor)).isoformat()
        elif tipo == "BOOL":
            if not isinstance(valor, bool):
                raise ValueError(f"{campo}: booleano inválido")
        else:
            valor = str(valor).strip()
            if not valor:
                raise ValueError(f"{campo}: texto vazio")
        saida[campo] = valor
    return saida


def deduplicar(entidade, registros):
    chave = TABELAS[entidade][1]
    ultimos = {}
    for registro in registros:
        # Escolhe a versão antes de converter: uma correção pode substituir um
        # payload antigo inválido preservado na raw de uma execução falha.
        registro = dict(registro)
        registro["atualizado_em"] = timestamp(registro["atualizado_em"])
        anterior = ultimos.get(registro[chave])
        if anterior and anterior["atualizado_em"] == registro["atualizado_em"] and anterior != registro:
            raise ValueError(f"{entidade}: versões conflitantes para a mesma chave/timestamp")
        if not anterior or registro["atualizado_em"] > anterior["atualizado_em"]:
            ultimos[registro[chave]] = registro
    return [normalizar(entidade, r) for r in ultimos.values()]
