"""Conferência de quantidades e valores em Python, independente do Spark SQL."""
from decimal import Decimal

def consolidar(eventos):
    vistos={};atuais={}
    for e in eventos:
        conteudo={k:v for k,v in e.items() if k!='id_evento'}
        if e['id_evento'] in vistos and vistos[e['id_evento']]!=conteudo:
            raise ValueError('id_evento reutilizado com conteúdo diferente')
        vistos[e['id_evento']]=conteudo
        if int(e['quantidade'])<=0:continue
        key=(e['entidade'],e['id_registro'])
        anterior=atuais.get(key)
        if anterior and int(anterior['versao'])==int(e['versao']) and {k:v for k,v in anterior.items() if k!='id_evento'}!=conteudo:
            raise ValueError('versão ambígua')
        if anterior is None or int(e['versao'])>int(anterior['versao']):atuais[key]=e
    pedidos={k[1]:e for k,e in atuais.items() if k[0]=='pedido'}
    faturas={k[1]:e for k,e in atuais.items() if k[0]=='faturamento' and e['id_referencia'] in pedidos}
    devs=[e for k,e in atuais.items() if k[0]=='devolucao' and e['id_referencia'] in faturas]
    saida=[]
    for idp,p in pedidos.items():
        fs={k:f for k,f in faturas.items() if f['id_referencia']==idp and f['status']=='faturado'}
        faturada=sum(int(f['quantidade']) for f in fs.values())
        devolvida=sum(int(d['quantidade']) for d in devs if d['id_referencia'] in fs)
        for idf,f in fs.items():
            if sum(int(d['quantidade']) for d in devs if d['id_referencia']==idf)>int(f['quantidade']):raise ValueError('devolução excedente')
        solicitada=int(p['quantidade']);preco=Decimal(p['preco_unitario'])
        if faturada>solicitada:raise ValueError('faturamento excedente')
        aberta=0 if p['status']=='cancelado' else solicitada-faturada
        cancelada=solicitada-faturada if p['status']=='cancelado' else 0
        saida.append({'id_pedido':int(idp),'quantidade_pedida':solicitada,'quantidade_faturada':faturada,
            'quantidade_devolvida':devolvida,'quantidade_aberta':aberta,'quantidade_cancelada':cancelada,
            'valor_aberto':str(aberta*preco),'valor_faturado':str(faturada*preco),
            'valor_devolvido':str(devolvida*preco),'receita_apos_devolucao':str((faturada-devolvida)*preco)})
    return sorted(saida,key=lambda r:r['id_pedido'])
