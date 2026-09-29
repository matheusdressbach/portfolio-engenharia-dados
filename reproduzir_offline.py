"""Reconstitui vendas e indicadores a partir do snapshot raw, sem nuvem ou pacotes externos."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import json

ROOT = Path(__file__).resolve().parent
D = lambda v: Decimal(str(v))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load_snapshot():
    tables = defaultdict(list)
    raw = json.loads((ROOT / 'exportacao-bigquery.json').read_text())
    for item in raw:
        tables[item['objeto']].append(json.loads(item['registro'], parse_float=Decimal))
    return tables

def build_facts(tables):
    products = {int(r['product_id']): r for r in tables['raw.products']}
    customers = {int(r['customer_id']) for r in tables['raw.customers']}
    sellers = {int(r['salesperson_id']) for r in tables['raw.salespeople']}
    latest = {}
    for row in tables['raw.orders']:
        key = int(row['order_id'])
        if key not in latest or (row['updated_at'], row['ingerido_em']) > (latest[key]['updated_at'], latest[key]['ingerido_em']):
            latest[key] = row
    result = []
    for key, row in sorted(latest.items()):
        qty, price = int(row['quantity']), D(row['unit_price'])
        require(qty > 0 and price >= 0, f'Quantidade/preço inválido: {key}')
        require(int(row['customer_id']) in customers, f'Cliente ausente: {key}')
        require(int(row['salesperson_id']) in sellers, f'Vendedor ausente: {key}')
        require(int(row['product_id']) in products, f'Produto ausente: {key}')
        cost = D(products[int(row['product_id'])]['unit_cost'])
        result.append(dict(id_lancamento=key, data_venda=row['sale_date'],
                           id_cliente=int(row['customer_id']), status=row['status'],
                           valor_faturamento=qty*price, valor_custo=qty*cost,
                           valor_margem_bruta=qty*(price-cost)))
    return result

def reconcile(tables, facts):
    reference = {int(r['id_lancamento']): r for r in tables['comercial.fato_lancamento_vendas']}
    require(len(reference) == len(facts), 'Contagem diferente entre raw e fato exportada')
    for f in facts:
        r = reference[f['id_lancamento']]
        for key in ['valor_faturamento', 'valor_custo', 'valor_margem_bruta']:
            require(f[key] == D(r[key]), f'Divergência em {key}: {f["id_lancamento"]}')
        require(f['data_venda'] == r['data_venda'] and f['status'] == r['status'], 'Data/status divergente')
    groups = defaultdict(list)
    for f in facts:
        if f['status'] == 'invoiced':
            groups[f['data_venda'][:7]+'-01'].append(f)
    metrics = []
    refs = {r['mes_referencia']: r for r in tables['comercial.vw_indicadores_executivos']}
    for month, sales in sorted(groups.items()):
        rev = sum((f['valor_faturamento'] for f in sales), Decimal(0))
        margin = sum((f['valor_margem_bruta'] for f in sales), Decimal(0))
        active = len({f['id_cliente'] for f in sales})
        goal = sum((D(r['valor_meta']) for r in tables['raw.metas'] if r['mes_referencia'] == month), Decimal(0))
        row = dict(mes_referencia=month, faturamento=rev, margem_bruta=margin,
                   clientes_ativos=active, quantidade_lancamentos=len(sales), valor_meta=goal)
        ref = refs[month]
        for key in row:
            require(str(row[key]) == str(ref[key]) if key == 'mes_referencia' else D(row[key]) == D(ref[key]), f'Indicador divergente: {month}/{key}')
        for key, value in [('percentual_margem',margin/rev),('ticket_medio',rev/len(sales)),('percentual_atingimento_meta',rev/goal)]:
            require(abs(value-D(ref[key])) <= Decimal('0.000000001'), f'Razão divergente: {month}/{key}')
            row[key] = value.quantize(Decimal('0.000000001'), rounding=ROUND_HALF_UP)
        metrics.append(row)
    require(set(groups)==set(refs), 'Meses ausentes no snapshot')
    return metrics

def main():
    tables = load_snapshot()
    facts = build_facts(tables)
    months = reconcile(tables, facts)
    invoiced = [f for f in facts if f['status']=='invoiced']
    summary = dict(status='APROVADO', objetos=len(tables), registros_exportados=sum(map(len,tables.values())),
                   lancamentos=len(facts), lancamentos_faturados=len(invoiced), meses=len(months),
                   faturamento=sum((f['valor_faturamento'] for f in invoiced),Decimal(0)),
                   margem_bruta=sum((f['valor_margem_bruta'] for f in invoiced),Decimal(0)),
                   verificacoes=['Integridade referencial','Valores monetários por lançamento','Totais e indicadores de cada mês'],
                   escopo='Reprocessamento local do snapshot exportado; não é ingestão PostgreSQL/API nem execução Airflow.')
    folder=ROOT/'resultados'; folder.mkdir(exist_ok=True)
    for name, data in [('validacao.json',summary),('indicadores-recalculados.json',months)]:
        (folder/name).write_text(json.dumps(data,default=str,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,default=str,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
