"""Massa de uma distribuidora fictícia; valores monetários calculados com Decimal."""
from datetime import datetime, timezone
from decimal import Decimal

VENDEDORES = [(1, 'Ana Martins'), (2, 'Bruno Lopes'), (3, 'Carla Nunes'),
              (4, 'Diego Souza'), (5, 'Elisa Costa'), (6, 'Felipe Rocha')]
REGIOES = ['Sul', 'Sudeste', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sul']

def clientes():
    return [(i, f'Mercado {i:03}', vendedor_inicial(i),
             REGIOES[vendedor_inicial(i)-1], True, '2024-12-01T00:00:00+00:00')
            for i in range(1, 121)]

def vendedor_inicial(cliente):
    return (cliente - 1) % 6 + 1

def vendedor_na_data(cliente, data):
    if data >= datetime(2025, 7, 1, tzinfo=timezone.utc) and cliente in (1, 2):
        return cliente + 1
    return vendedor_inicial(cliente)

def quantidade_compra(cliente, mes, posicao):
    """Perfis determinísticos: volumes distintos, sazonalidade, crescimento e queda."""
    base = (cliente + mes + posicao) % 5 + 1
    perfil = cliente % 5
    if perfil == 0:  # Contas grandes, concentradas na receita.
        return base * 8
    if perfil == 1:  # Aumenta o volume a cada trimestre.
        return base * (1 + (mes - 1) // 3)
    if perfil == 2:  # Reduz volume no último trimestre.
        return base * (5 if mes <= 9 else 1)
    if perfil == 3:  # Pico de compras no fim do ano.
        return base * (4 if mes >= 10 else 1)
    return base * 2

def pedidos(meses):
    cabecalhos, itens = [], []
    for mes in meses:
        for cliente in range(1, 121):
            if (cliente + mes) % 7 == 0 or (cliente == 3 and mes >= 9):
                continue
            chave = mes * 1000 + cliente
            status = 'cancelado' if (cliente + mes) % 31 == 0 else 'faturado'
            data = datetime(2025, mes, 15, 12, tzinfo=timezone.utc)
            cabecalhos.append((chave, cliente, data, status))
            for posicao in (1, 2):
                produto = (cliente * 3 + mes + posicao) % 18 + 1
                quantidade = quantidade_compra(cliente, mes, posicao)
                preco = Decimal('10.00') + Decimal(produto) * Decimal('2.35')
                desconto = Decimal('1.50') if cliente % 4 == 0 else Decimal('0.00')
                itens.append((chave * 10 + posicao, chave, produto, quantidade, preco, desconto))
    return cabecalhos, itens

def pedidos_atrasado_e_limite():
    return ([
        (900001, 1, datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc), 'faturado'),
        (900002, 1, datetime(2025, 7, 1, tzinfo=timezone.utc), 'faturado'),
    ], [(9000011, 900001, 1, 2, Decimal('25.00'), Decimal('0.00')),
        (9000021, 900002, 1, 3, Decimal('25.00'), Decimal('0.00'))])

def esperado():
    cab, itens = pedidos(range(1, 13))
    extras, extra_itens = pedidos_atrasado_e_limite()
    cab += extras; itens += extra_itens
    valores = {}
    for _, pedido, _, qtd, preco, desconto in itens:
        valores[pedido] = valores.get(pedido, Decimal('0.00')) + qtd * preco - desconto
    cancelado_corrigido = cab[0][0]
    compras = set()
    receita_vendedor = {i: Decimal('0.00') for i, _ in VENDEDORES}
    receita = Decimal('0.00'); cancelados = 0
    for chave, cliente, data, status in cab:
        if chave == cancelado_corrigido:
            status = 'cancelado'
        if status == 'cancelado':
            cancelados += 1
        else:
            receita += valores[chave]
            receita_vendedor[vendedor_na_data(cliente, data)] += valores[chave]
            compras.add((cliente, data.month))
    primeiras = {c: min(m for cc,m in compras if cc == c) for c in range(1,121)}
    situacoes = {'novo': 0, 'recorrente': 0, 'reativado': 0, 'sem_compra': 0}
    retidos = 0
    for c in range(1,121):
        for m in range(1,13):
            if (c,m) not in compras:
                estado = 'sem_compra'
            elif primeiras[c] == m:
                estado = 'novo'
            elif (c,m-1) in compras:
                estado = 'recorrente'; retidos += 1
            else:
                estado = 'reativado'
            situacoes[estado] += 1
    return {
        'clientes': 120, 'vendedores': 6, 'produtos': 18,
        'pedidos': len(cab), 'itens': len(itens), 'cancelados': cancelados,
        'versoes_clientes': 123, 'carteira_mensal': 1440,
        'receita': str(receita),
        'receita_por_vendedor': {str(k):str(v) for k,v in receita_vendedor.items()},
        'situacoes_compra': situacoes, 'clientes_retidos_mes': retidos,
        'pedido_atrasado_vendedor': 1, 'pedido_no_limite_vendedor': 2,
    }

if __name__ == '__main__':
    import json
    print(json.dumps(esperado(), ensure_ascii=False, indent=2))
