from copy import deepcopy

BASE = {
    "vendedores": [
        {"id_vendedor": 1, "nome": "Ana Martins", "ativo": True, "atualizado_em": "2026-09-01T08:00:00Z"},
        {"id_vendedor": 2, "nome": "Bruno Lopes", "ativo": True, "atualizado_em": "2026-09-01T08:00:00Z"}],
    "clientes": [{"id_cliente": 10, "nome": "Mercado Horizonte", "uf": "SP", "atualizado_em": "2026-09-01T08:00:00Z"}],
    "produtos": [{"id_produto": 100, "descricao": "Café torrado 500g", "atualizado_em": "2026-09-01T08:00:00Z"}],
    "vendas": [
        {"id_lancamento": 1001, "id_vendedor": 1, "id_cliente": 10, "id_produto": 100,
         "data_venda": "2026-09-01", "quantidade": 10, "valor_bruto": "300.00", "valor_desconto": "20.00",
         "cancelado": False, "atualizado_em": "2026-09-01T10:00:00Z"},
        {"id_lancamento": 1002, "id_vendedor": 2, "id_cliente": 10, "id_produto": 100,
         "data_venda": "2026-09-01", "quantidade": 5, "valor_bruto": "150.00", "valor_desconto": "0.00",
         "cancelado": False, "atualizado_em": "2026-09-01T10:00:00Z"}],
    "devolucoes": [],
    "metas": [
        {"id_meta": 1, "id_vendedor": 1, "competencia": "2026-09-01", "valor_meta": "1000.00",
         "atualizado_em": "2026-09-01T08:00:00Z"},
        {"id_meta": 2, "id_vendedor": 2, "competencia": "2026-09-01", "valor_meta": "800.00",
         "atualizado_em": "2026-09-01T08:00:00Z"}],
}


def dados_exemplo():
    return deepcopy(BASE)


def segundo_dia(dados):
    dados["vendas"][0].update(valor_desconto="30.00", atualizado_em="2026-09-02T08:00:00Z")
    dados["vendas"][1].update(cancelado=True, atualizado_em="2026-09-02T08:10:00Z")
    dados["vendas"].append({**dados["vendas"][0], "id_lancamento": 1003, "data_venda": "2026-09-02",
                           "quantidade": 2, "valor_bruto": "60.00", "valor_desconto": "0.00",
                           "atualizado_em": "2026-09-02T09:00:00Z"})
