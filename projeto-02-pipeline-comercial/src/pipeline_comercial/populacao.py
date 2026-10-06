"""Cenário sintético reproduzível de distribuição de alimentos, outubro/2025 a setembro/2026."""
import argparse
import calendar
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .modelo import normalizar

SEMENTE = 42
ATUALIZADO = '2026-10-01T00:00:00Z'  # Apenas fixtures; a carga SQL carimba o instante da carga.
CIDADES = [('São Paulo','SP','Sudeste'), ('Campinas','SP','Sudeste'), ('Rio de Janeiro','RJ','Sudeste'),
           ('Belo Horizonte','MG','Sudeste'), ('Curitiba','PR','Sul'), ('Porto Alegre','RS','Sul'),
           ('Florianópolis','SC','Sul'), ('Salvador','BA','Nordeste'), ('Recife','PE','Nordeste'),
           ('Fortaleza','CE','Nordeste'), ('Goiânia','GO','Centro-Oeste'), ('Brasília','DF','Centro-Oeste')]
NOMES = ['Ana Martins','Bruno Lopes','Carla Souza','Diego Alves','Elisa Rocha','Felipe Costa',
         'Gabriela Lima','Henrique Dias','Isabela Nunes','João Ribeiro','Larissa Melo','Marcos Silva']
CATEGORIAS = [('Cafés','Café',Decimal('30')), ('Biscoitos','Biscoito',Decimal('12')),
              ('Bebidas','Suco',Decimal('9')), ('Mercearia','Arroz',Decimal('24'))]


def gerar():
    rng = random.Random(SEMENTE)
    dados = {e: [] for e in ['vendedores','clientes','produtos','vendas','devolucoes','metas']}
    for i, nome in enumerate(NOMES):
        regiao = CIDADES[i][2]
        dados['vendedores'].append(dict(id_vendedor=i+1,nome=nome,ativo=True,equipe='Equipe '+regiao,
                                       regiao=regiao,atualizado_em=ATUALIZADO))
    for i in range(200):
        cidade,uf,_ = CIDADES[i % len(CIDADES)]
        segmento = ['Mercado de bairro','Supermercado','Atacado','Restaurante'][i % 4]
        dados['clientes'].append(dict(id_cliente=10+i,nome='Mercado Horizonte' if i==0 else f'{segmento} {i+1:03d}',
                                     uf=uf,cidade=cidade,segmento=segmento,atualizado_em=ATUALIZADO))
    precos = {}
    for i in range(40):
        categoria,produto,preco = CATEGORIAS[i//10]
        precos[100+i] = preco + Decimal(i % 10) * Decimal('1.50')
        dados['produtos'].append(dict(id_produto=100+i,descricao='Café torrado 500g' if i==0 else f'{produto} variante {i%10+1}',
                                     categoria=categoria,atualizado_em=ATUALIZADO))
    meses = [(2025,m) for m in range(10,13)] + [(2026,m) for m in range(1,10)]
    pesos = [11,14,17,7,7,9,9,10,10,10,10,12]
    for i in range(4997):
        ano,mes = rng.choices(meses,weights=pesos)[0]
        dia = date(ano,mes,rng.randint(1,calendar.monthrange(ano,mes)[1]))
        # Clientes recorrentes têm probabilidade maior. Vendedor acompanha a praça do cliente.
        cliente = rng.choices(dados['clientes'], weights=[5 if j<40 else 1 for j in range(200)])[0]
        vendedor = (cliente['id_cliente']-10) % 12 + 1
        produto = rng.choices(list(precos), weights=[3 if j<10 else 1 for j in range(40)])[0]
        quantidade = rng.randint(2,32) if cliente['segmento']!='Atacado' else rng.randint(30,100)
        bruto = precos[produto] * quantidade
        desconto = (bruto * rng.choice([Decimal('0'),Decimal('0.03'),Decimal('0.05'),Decimal('0.10')])).quantize(Decimal('0.01'))
        dados['vendas'].append(dict(id_lancamento=10000+i,id_vendedor=vendedor,id_cliente=cliente['id_cliente'],
            id_produto=produto,data_venda=dia.isoformat(),quantidade=quantidade,valor_bruto=str(bruto),
            valor_desconto=str(desconto),cancelado=rng.random()<0.025,atualizado_em=ATUALIZADO))
    elegiveis = [r for r in dados['vendas'] if not r['cancelado']]
    for i,venda in enumerate(rng.sample(elegiveis,180)):
        quantidade = rng.randint(1,venda['quantidade'])
        liquido = Decimal(venda['valor_bruto'])-Decimal(venda['valor_desconto'])
        valor = (liquido*quantidade/venda['quantidade']).quantize(Decimal('0.01'))
        dia = min(date(2026,9,30),date.fromisoformat(venda['data_venda'])+timedelta(days=rng.randint(1,21)))
        dados['devolucoes'].append(dict(id_devolucao=20000+i,id_lancamento=venda['id_lancamento'],
            data_devolucao=dia.isoformat(),quantidade=quantidade,valor_devolvido=str(valor),
            motivo=rng.choice(['Avaria no transporte','Divergência no pedido','Qualidade do produto']),atualizado_em=ATUALIZADO))
    for j,(ano,mes) in enumerate(meses):
        for vendedor in range(1,13):
            if (ano,mes)==(2026,9) and vendedor in (1,2):
                continue  # Preserva as duas metas do caso inicial e sua correção já validada.
            meta = Decimal(18000 + vendedor*1200) * Decimal(str(pesos[j])) / Decimal(10)
            dados['metas'].append(dict(id_meta=10000+j*12+vendedor,id_vendedor=vendedor,
                competencia=date(ano,mes,1).isoformat(),valor_meta=str(meta.quantize(Decimal('0.01'))),atualizado_em=ATUALIZADO))
    return {e:[normalizar(e,r) for r in linhas] for e,linhas in dados.items()}


def literal(valor):
    if isinstance(valor,bool):
        return 'true' if valor else 'false'
    if isinstance(valor,int):
        return str(valor)
    return "'"+str(valor).replace("'","''")+"'"


def sql(dados):
    linhas = ['-- Gerado com semente 42. Não altera os três lançamentos do teste inicial.','BEGIN;']
    for entidade, registros in dados.items():
        schema = 'planejamento' if entidade=='metas' else 'erp'
        for r in registros:
            campos = [c for c in r if c!='valor_liquido']
            valores = ['CURRENT_TIMESTAMP' if c=='atualizado_em' else literal(r[c]) for c in campos]
            chave=campos[0]
            # Vendas, devoluções e metas não são regravadas ao reaplicar a mesma massa.
            acao = 'DO NOTHING'
            if entidade in ('vendedores','clientes','produtos'):
                acao = 'DO UPDATE SET '+', '.join(c+'=EXCLUDED.'+c for c in campos if c!=chave)
            linhas.append(f"INSERT INTO {schema}.{entidade} ({','.join(campos)}) VALUES ({','.join(valores)}) ON CONFLICT ({chave}) {acao};")
    linhas.append('COMMIT;')
    return '\n'.join(linhas)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,default=Path('sql/postgres/06_popular_comercial.sql'))
    args=parser.parse_args()
    dados=gerar()
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(sql(dados))
    print(json.dumps({'arquivo':str(args.saida),'semente':SEMENTE,'registros_gerados':{e:len(r) for e,r in dados.items()}},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
