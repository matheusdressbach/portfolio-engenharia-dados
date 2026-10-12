from decimal import Decimal
"""Executa o cenário completo em carteira_demo e compara dbt com cálculo independente."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values
from dados import VENDEDORES, clientes, pedidos, pedidos_atrasado_e_limite, esperado

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = ROOT / 'resultados'
RESULTADOS.mkdir(exist_ok=True)
ETAPAS = []

def dbt(nome, *args, rejeitar=False):
    processo = subprocess.run(['dbt', '--no-use-colors', *args], cwd=ROOT,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (RESULTADOS / f'{nome}.log').write_text(processo.stdout)
    print(processo.stdout, flush=True)
    if rejeitar:
        if processo.returncode == 0:
            raise AssertionError(f'{nome}: o teste deveria rejeitar os dados')
    elif processo.returncode != 0:
        raise RuntimeError(f'{nome}: dbt terminou com código {processo.returncode}')
    artifact = ROOT / 'target/run_results.json'
    resultados = json.loads(artifact.read_text()) if artifact.exists() and args[0] != 'docs' else {}
    if rejeitar:
        falhas = [r['unique_id'] for r in resultados.get('results', []) if r['status'] == 'fail']
        if not falhas or any(r['status'] == 'error' for r in resultados['results']):
            raise AssertionError(f'{nome}: não foi uma rejeição de qualidade válida')
    else:
        falhas = []
    resumo = {'etapa': nome, 'codigo': processo.returncode,
              'testes': sum(r['unique_id'].startswith('test.') for r in resultados.get('results', [])),
              'rejeicoes': falhas}
    ETAPAS.append(resumo)
    (RESULTADOS / f'{nome}.json').write_text(json.dumps(resultados, indent=2))

def linhas(db, sql, args=None):
    with db.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall() if cur.description else []

def carregar(db, meses):
    cab, itens = pedidos(meses)
    inserir_pedidos(db, cab, itens)

def inserir_pedidos(db, cab, itens):
    with db.cursor() as cur:
        execute_values(cur, 'insert into raw.pedidos values %s', cab)
        execute_values(cur, 'insert into raw.itens_pedidos values %s', itens)

def assinatura(db):
    estado = {}
    for tabela, ordenacao in [('dm.dim_clientes','id_cliente, vigencia_inicio'),
                              ('comercial.fato_pedidos','id_pedido'),
                              ('comercial.fato_carteira_mensal','id_cliente, competencia'),
                              ('comercial.desempenho_vendedores','competencia, id_vendedor'),
                              ('comercial.fato_itens_vendas','id_item'),
                              ('comercial.comportamento_clientes','id_cliente, competencia'),
                              ('comercial.retencao_coortes','coorte, competencia'),
                              ('comercial.concentracao_receita','competencia')]:
        estado[tabela] = linhas(db, f'select * from {tabela} order by {ordenacao}')
    return hashlib.sha256(json.dumps(estado, default=str, sort_keys=True).encode()).hexdigest()

def teste_negativo(db, nome, alterar, restaurar, seletor):
    try:
        linhas(db, alterar)
        dbt(nome, 'test', '--select', seletor, rejeitar=True)
    finally:
        linhas(db, restaurar)

db = psycopg2.connect(host=os.environ.get('PGHOST','postgres'),
                      port=int(os.environ.get('PGPORT','5432')),
                      user=os.environ.get('PGUSER','carteira'),
                      password=os.environ.get('PGPASSWORD','carteira_local'),
                      dbname=os.environ.get('PGDATABASE','carteira_demo'))
try:
    db.autocommit = True
    if linhas(db, 'select current_database()')[0][0] != 'carteira_demo':
        raise RuntimeError('O roteiro só pode usar o banco sintético carteira_demo')
    # O roteiro reinicia apenas os schemas do banco isolado deste projeto.
    for schema in ('raw','historico','staging','intermediario','dm','comercial'):
        linhas(db, f'drop schema if exists {schema} cascade')
    linhas(db, '''create schema raw;
      create table raw.clientes (id_cliente integer primary key, nome text not null,
        id_vendedor integer not null, regiao text not null, ativo boolean not null,
        atualizado_em timestamptz not null);
      create table raw.vendedores (id_vendedor integer primary key, nome text not null);
      create table raw.produtos (id_produto integer primary key, nome text not null, categoria text not null);
      create table raw.pedidos (id_pedido integer primary key, id_cliente integer not null,
        emitido_em timestamptz not null, status text not null);
      create table raw.itens_pedidos (id_item integer primary key, id_pedido integer not null,
        id_produto integer not null, quantidade integer not null,
        preco_unitario numeric(12,2) not null, valor_desconto numeric(12,2) not null);''')
    with db.cursor() as cur:
        execute_values(cur, 'insert into raw.clientes values %s', clientes())
        execute_values(cur, 'insert into raw.vendedores values %s', VENDEDORES)
        execute_values(cur, 'insert into raw.produtos values %s',
                       [(i,f'Produto {i:02}', ['Mercearia','Bebidas','Limpeza'][(i-1)%3]) for i in range(1,19)])
    carregar(db, range(1,7))
    dbt('01_cadastro_inicial', 'build')
    junho = linhas(db, "select id_pedido, id_vendedor, receita from comercial.fato_pedidos where competencia = '2025-06-01' order by id_pedido")
    linhas(db, "update raw.clientes set id_vendedor = id_cliente + 1, regiao = 'Sudeste', atualizado_em = '2025-07-01T00:00:00Z' where id_cliente in (1,2)")
    carregar(db, range(7,9))
    dbt('02_troca_carteira', 'build')
    assert linhas(db, "select id_pedido, id_vendedor, receita from comercial.fato_pedidos where competencia = '2025-06-01' order by id_pedido") == junho
    inserir_pedidos(db, *pedidos_atrasado_e_limite())
    linhas(db, "update raw.clientes set ativo = false, atualizado_em = '2025-09-01T00:00:00Z' where id_cliente = 3")
    carregar(db, range(9,13))
    primeiro = pedidos([1])[0][0][0]
    linhas(db, 'update raw.pedidos set status = %s where id_pedido = %s', ('cancelado', primeiro))
    dbt('03_atraso_e_inativacao', 'build')
    exp = esperado()
    assert linhas(db,'select count(*) from comercial.fato_pedidos')[0][0] == exp['pedidos']
    assert linhas(db,'select count(*) from raw.itens_pedidos')[0][0] == exp['itens']
    assert linhas(db,'select count(*) from dm.dim_clientes')[0][0] == exp['versoes_clientes']
    assert linhas(db,'select count(distinct id_cliente) from dm.dim_clientes')[0][0] == exp['clientes']
    assert linhas(db,'select count(*) from dm.dim_vendedores')[0][0] == exp['vendedores']
    assert linhas(db,'select count(*) from dm.dim_produtos')[0][0] == exp['produtos']
    assert linhas(db,'select count(distinct (competencia, id_vendedor)) from comercial.desempenho_vendedores')[0][0] == 72
    assert linhas(db,'select count(*) from comercial.desempenho_vendedores')[0][0] == 72
    assert linhas(db,'select count(*) from comercial.fato_carteira_mensal')[0][0] == 1440
    assert str(linhas(db,'select sum(receita) from comercial.fato_pedidos')[0][0]) == exp['receita']
    por_vendedor = {str(k):str(v) for k,v in linhas(db,'select id_vendedor, sum(receita) from comercial.fato_pedidos group by id_vendedor')}
    assert por_vendedor == exp['receita_por_vendedor']
    assert dict(linhas(db,'select situacao_compra, count(*) from comercial.fato_carteira_mensal group by situacao_compra')) == exp['situacoes_compra']
    assert linhas(db,'select count(*) from comercial.fato_carteira_mensal where retido')[0][0] == exp['clientes_retidos_mes']
    assert linhas(db,"select count(*) from comercial.fato_pedidos where status='cancelado'")[0][0] == exp['cancelados']
    assert linhas(db,'select id_pedido, id_vendedor from comercial.fato_pedidos where id_pedido in (900001,900002) order by id_pedido') == [(900001,1),(900002,2)]
    assert linhas(db,"select ativo from comercial.fato_carteira_mensal where id_cliente=3 and competencia='2025-08-01'") == [(True,)]
    assert linhas(db,"select ativo from comercial.fato_carteira_mensal where id_cliente=3 and competencia='2025-09-01'") == [(False,)]
    antes = assinatura(db)
    dbt('04_repeticao', 'build')
    assert assinatura(db) == antes, 'Repetição alterou o estado publicado'
    teste_negativo(db,'05_vigencias_sobrepostas',
        "update dm.dim_clientes set vigencia_fim='2025-07-02' where id_cliente=1 and vigencia_fim is not null",
        "update dm.dim_clientes set vigencia_fim='2025-07-01' where id_cliente=1 and vigencia_fim is not null",
        'vigencias_sem_sobreposicao')
    teste_negativo(db,'06_desconto_invalido',
        'update raw.itens_pedidos set valor_desconto=999999 where id_item=9000011',
        'update raw.itens_pedidos set valor_desconto=0 where id_item=9000011',
        'itens_com_valores_validos')
    teste_negativo(db,'07_vendedor_inexistente',
        'update raw.clientes set id_vendedor=999 where id_cliente=1',
        'update raw.clientes set id_vendedor=2 where id_cliente=1',
        'source:erp.clientes')
    teste_negativo(db,'08_venda_no_vendedor_errado',
        'update comercial.fato_pedidos set id_vendedor=2 where id_pedido=900001',
        'update comercial.fato_pedidos set id_vendedor=1 where id_pedido=900001',
        'pedido_na_vigencia')
    dbt('09_recuperacao', 'test')
    # Referência independente para o alerta: consulta só os valores mensais,
    # calcula as janelas em Python e compara com o modelo analítico.
    series = {}
    for cliente, mes, valor, alerta, media, acumulada in linhas(db,
        'select id_cliente, competencia, receita_mes, sinal_atencao, receita_media_3m_anteriores, receita_acumulada from comercial.comportamento_clientes order by id_cliente, competencia'):
        anteriores = series.setdefault(cliente, [])
        base = anteriores[-3:]
        media_esperada = sum(base) / len(base) if base else None
        assert media is None if media_esperada is None else abs(media - media_esperada) < Decimal('0.000001')
        assert acumulada == sum(anteriores) + valor
        if cliente != 3:  # Cliente 3 tem inativação explícita e precedência de cadastro.
            if len(base) < 3:
                esperado_alerta = 'historico_insuficiente'
            elif not any(v > 0 for v in (anteriores[-1], valor)):
                esperado_alerta = 'ausencia_prolongada'
            elif media_esperada > 0 and valor < media_esperada * Decimal('0.5'):
                esperado_alerta = 'queda_receita'
            else:
                esperado_alerta = 'sem_alerta'
            assert alerta == esperado_alerta, (cliente, mes, alerta, esperado_alerta)
        anteriores.append(valor)
    assert linhas(db, "select count(*) from comercial.comportamento_clientes where pedidos_mes > 0 and sinal_atencao = 'queda_receita'")[0][0] > 0

    assert assinatura(db) == antes, 'Os testes negativos não restauraram o estado'
    dbt('10_documentacao', 'docs', 'generate')
    exemplos = linhas(db,"select id_pedido, emitido_em, id_vendedor, receita from comercial.fato_pedidos where id_pedido in (6001,900001,900002,7001) order by emitido_em")
    relatorio = {'validado_em_utc':datetime.now(timezone.utc).isoformat(),
                 'dbt_core':'1.10.13','dbt_postgres':'1.10.0',
                 'resultados_conciliados':exp, 'historico_junho_preservado':True,
                 'repeticao_preservou_estado':True,'negativos_restaurados':True,
                 'assinatura_estado':antes,'exemplos_cliente_1':exemplos, 'etapas':ETAPAS}
    (RESULTADOS/'validacao.json').write_text(json.dumps(relatorio, default=str, ensure_ascii=False,indent=2))
    print(json.dumps(relatorio,default=str,ensure_ascii=False,indent=2),flush=True)

finally:
    db.close()
