"""Origem sintética com IDs e versões estáveis; nenhuma chamada ao Projeto 2."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def evento(entidade, chave, versao=1, **campos):
    return dict(id_evento=f'{entidade}-{chave}-v{versao}', entidade=entidade,
                id_registro=str(chave), versao=str(versao),
                atualizado_em=f'2026-09-{(26 if entidade=="devolucao" else 20)+versao:02}T12:00:00Z', **{k:str(v) for k,v in campos.items()})

def pedido(i, versao=1, status='aberto'):
    return evento('pedido',i,versao, id_cliente=(i-1)%12+1, id_vendedor=(i-1)%4+1,
                  id_produto=(i-1)%8+1, quantidade=10+i%5, preco_unitario=f'{20+i%8*5}.00',
                  data_documento=f'2026-09-{1+i%9:02}', data_prevista='2026-09-20', status=status)

def fatura(i,p,qty,versao=1,status='faturado'):
    return evento('faturamento',i,versao,id_referencia=p,quantidade=qty,
                  data_documento='2026-09-15',status=status)

def devolucao(i,f,qty,versao=1):
    return evento('devolucao',i,versao,id_referencia=f,quantidade=qty,
                  data_documento='2026-09-25',status='confirmada')

def lotes():
    a=[pedido(i) for i in range(1,31)]
    a += [fatura(i,i,4) for i in range(1,21)]
    b=[pedido(i) for i in range(31,41)] + [pedido(2,2,'cancelado')]
    b += [fatura(100+i,i,3) for i in range(1,11)]
    b += [devolucao(i,i,1) for i in range(1,6)]
    b += [fatura(410,41,2), devolucao(800,480,1)]  # Documentos-pai chegam no lote 3.
    b += [fatura(999,1,-2)]  # Evento inválido; fica fora da Silver.
    b += [a[0],a[30]]  # Duplicatas exatas, inclusive de lote anterior.
    c=[pedido(i) for i in range(41,49)]
    c += [pedido(2)]  # Versão antiga chega após o cancelamento; não deve revertê-lo.
    c += [fatura(480,48,3), fatura(1,1,5,versao=2)]
    c += [fatura(999,1,2,versao=2)]  # Correção válida da quantidade negativa.
    return {'01_inicial':a,'02_movimento':b,'03_atrasos_e_correcao':c}

def gerar():
    pasta=ROOT/'dados/lotes';pasta.mkdir(parents=True,exist_ok=True)
    for nome,rows in lotes().items():
        (pasta/f'{nome}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
    cadastros={'clientes':[{'id_cliente':i,'nome':f'Mercado {i:02}'} for i in range(1,13)],
               'vendedores':[{'id_vendedor':i,'nome':n} for i,n in enumerate(['Ana Martins','Bruno Lopes','Carla Nunes','Diego Souza'],1)],
               'produtos':[{'id_produto':i,'nome':f'Produto {i:02}','categoria':'Limpeza' if i<=4 else 'Alimentos'} for i in range(1,9)]}
    for nome,rows in cadastros.items():
        (ROOT/'dados'/f'{nome}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
    print('Três lotes e cadastros gravados.')
if __name__=='__main__':gerar()
