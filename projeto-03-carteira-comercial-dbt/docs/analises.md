# O que investigar na carteira

A receita do mês sozinha não explica a saúde comercial. As novas tabelas colocam o fechamento mensal ao lado do histórico de cada cliente.

- `comercial.comportamento_clientes`: receita, ticket, recência mensal, receita acumulada e comparação com a média dos três meses anteriores. Uma queda superior a 50% gera um sinal de atenção; dois meses sem compra geram ausência prolongada. Cadastro inativo tem uma classificação própria. Os três primeiros meses não geram alerta de queda por falta de base.
- `comercial.retencao_coortes`: acompanha os clientes pela primeira compra observada. O denominador permanece a coorte inteira, inclusive clientes inativados. A taxa mede quem comprou em cada mês, não sobrevivência contínua. Como o histórico começa em 2025, “primeira compra” não significa aquisição real.
- `comercial.concentracao_receita`: mede a participação dos 20% maiores clientes e a soma dos quadrados das participações individuais. O grupo usa 20% de toda a carteira, arredondado para cima, com desempate por cliente. Receita zero resulta em indicador nulo. Maior concentração indica maior dependência de poucos compradores.
- `comercial.fato_itens_vendas`: permite comparar categorias e produtos sem duplicar a receita do pedido. Cancelamentos permanecem no detalhe, com receita zero.

As consultas `priorizar_contatos.sql` e `mix_categorias.sql` conectam os indicadores a perguntas concretas: quem merece contato primeiro e quais categorias sustentam a receita?

Os sinais são regras comerciais exploratórias, não previsão de churn. A base mensal inclui zeros e só usa meses passados na referência; não usa compras futuras para gerar um alerta. Receita acumulada também termina no mês analisado. A carteira segue o vendedor no fechamento, enquanto os itens mantêm o vendedor histórico da venda.

A massa inclui cinco perfis de volume: grandes contas, crescimento trimestral, queda no último trimestre, pico de fim de ano e volume estável. O perfil é definido por `id_cliente % 5`, para reprodução sem sorteio. A frequência de compra continua regular e há poucas coortes. Ela valida cálculos e mudanças de carteira, mas não sustenta conclusões sobre um mercado real. Uma próxima ampliação da origem deve incluir entradas de clientes ao longo do ano, sazonalidade e frequências de compra distintas. Não inventamos margem sem dados de custo.

## Leitura da execução ampliada

Na massa validada, a participação dos 20% maiores clientes sobe de 49,18% em setembro para 59,66% em dezembro. Isso sugere maior dependência das contas de maior receita; não prova perda de clientes.

Em dezembro há 34 sinais de queda de receita, dos quais 14 são clientes que ainda compraram. Uma lista baseada apenas em ausência deixaria essas 14 contas fora da análise. Há também um caso de ausência prolongada e um cadastro inativo, tratados separadamente.

Esses resultados descrevem a massa sintética. Os perfis foram construídos para testar situações comerciais, não estimar a frequência delas no mundo real.
