# Contratos e grãos

| Entidade | Chave da origem | Tabela final | Grão |
|---|---|---|---|
| vendedores | id_vendedor | dm.dim_vendedores | um vendedor |
| clientes | id_cliente | dm.dim_clientes | um cliente |
| produtos | id_produto | dm.dim_produtos | um produto |
| vendas | id_lancamento | comercial.fato_lancamento_vendas | um lançamento/item do ERP |
| metas | id_meta | comercial.fato_metas_vendedores | um vendedor/competência |
| devolucoes | id_devolucao | comercial.fato_devolucoes | um evento de devolução de um lançamento |

As chaves naturais do ERP foram preservadas. Todas as tabelas recebem `atualizado_em`. Dimensões são tipo 1: mudança de nome substitui a versão anterior. O lançamento tem uma única chave; não é um pedido com múltiplos itens sem identificação individual.

`valor_bruto` e `valor_desconto` são valores totais do lançamento, não preços unitários. `valor_liquido = valor_bruto - valor_desconto`, sem arredondamento silencioso. O cancelamento preserva a linha; o consumo analítico filtra a flag. `quantidade` é positiva. Valores monetários são `NUMERIC` no BigQuery e strings decimais no contrato JSON, evitando conversão por ponto flutuante.

A API entrega `GET /metas?inicio=<timestamp>&fim=<timestamp>&limite=500&cursor=<opcional>`:

```json
{
  "itens": [{
    "id_meta": 1,
    "id_vendedor": 1,
    "competencia": "2026-09-01",
    "valor_meta": "1000.00",
    "atualizado_em": "2026-09-01T08:00:00+00:00"
  }],
  "proximo_cursor": null
}
```

Competência é o primeiro dia do mês. Há uma meta por vendedor/competência. `proximo_cursor=null` termina a extração. O cursor local codifica timestamp e chave; o cliente trata o valor como opaco. Timestamp deve informar fuso. O servidor aceita páginas de 1 a 1000 linhas.

Raw: `execucao`, `entidade`, `chave`, `versao`, `payload`. Staging: `execucao` e campos tipados de cada entidade. Operação: ID de execução, fim exclusivo, mapa JSON dos limites inferiores, status, erro e timestamp de alteração. Watermarks: entidade e fim da última publicação aprovada.

O PostgreSQL do Docker hospeda o ERP e uma tabela de planejamento que alimenta a API. ERP e planejamento têm interfaces separadas, mas compartilham um servidor para simplificar a execução local. O usuário do pipeline lê somente o schema ERP; somente o usuário da API lê planejamento.
