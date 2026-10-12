# Regras comerciais

## Receita e responsabilidade pela venda

Um pedido pode ter vários itens. O preço é unitário e o desconto é total por item:
`valor_liquido = quantidade × preco_unitario − valor_desconto`. A fato soma os itens
antes de relacionar o pedido com o histórico do cliente. Isso evita multiplicar
receita quando o cadastro tem várias versões.

Pedidos cancelados permanecem na fato, com receita zero. Os cálculos monetários
usam `numeric` no PostgreSQL e `Decimal` na conferência em Python.

A receita pertence ao vendedor e à região vigentes na emissão do pedido, inclusive
quando o pedido chega depois de uma mudança de carteira. A origem deste exemplo
não guarda um vendedor no pedido. Se um ERP real registrar o responsável da venda,
essa informação precisaria ser considerada antes de usar a carteira como regra.

## Carteira no fechamento

A foto mensal usa o estado imediatamente anterior ao início do mês seguinte.
Uma mudança exatamente em 1º de julho pertence a julho, sem alterar a carteira
no fechamento de junho. O cliente continua aparecendo após a inativação, com
`ativo=false`; inativação de cadastro e ausência de compra são informações diferentes.

A carteira mensal não guarda receita por vendedor. Esse valor é calculado a partir
da fato de pedidos, com responsabilidade histórica. A tabela de desempenho agrega
as duas fatos separadamente e só então relaciona os resultados por vendedor/mês.

## Compra, recompra e retenção

Somente pedidos faturados contam como compra. Cada cliente/mês recebe uma situação:

| Situação | Regra |
|---|---|
| novo | Comprou no mês de sua primeira compra observada |
| recorrente | Comprou neste mês e no mês imediatamente anterior |
| reativado | Comprou neste mês, já havia comprado antes, mas não no mês anterior |
| sem_compra | Não possui pedido faturado neste mês |

`retido` significa compra em dois meses consecutivos. A retenção do vendedor é a
quantidade de clientes retidos dividida pelos clientes com compra no mês anterior,
considerando a carteira atribuída a esse vendedor no fechamento do mês atual.
Se não houver clientes no denominador, a taxa é nula.

Isso mede continuidade de compra na carteira atual, não uma coorte fixa do vendedor
anterior. Ao transferir um cliente, sua continuidade passa a compor a carteira do
novo vendedor; a receita antiga permanece com quem era responsável pela venda.
Janeiro não possui mês anterior na base, portanto não mede retenção.

“Primeira compra” é a primeira observada em 2025. A base não permite afirmar que um
cliente nunca comprou antes desse período. Os indicadores não representam resultados
de uma empresa real.
