{% docs __overview__ %}
# Carteira comercial: quem era responsável pela venda?

O cliente 1 passou de Ana para Bruno em julho de 2025. Este projeto mantém
as versões de sua carteira para que os pedidos anteriores continuem com Ana.

O teste inclui um pedido de junho que chegou depois da troca e um pedido emitido
exatamente no início de julho. Eles ficaram, respectivamente, com Ana e Bruno.

## Explorar os modelos

- **dim_clientes:** vendedor, região e situação de cadastro por intervalo de vigência.
- **fato_pedidos:** um pedido com valores dos itens e vendedor vigente na emissão.
- **fato_carteira_mensal:** cadastro no fechamento, primeira compra, recompra e retenção.
- **desempenho_vendedores:** receita histórica e indicadores da carteira mensal.

As dependências entre fontes, snapshot e modelos podem ser vistas no gráfico
no canto inferior direito. Cada modelo mostra o SQL, as colunas e os testes associados.

## Execução validada em 06/10/2026

| Conferência | Resultado |
|---|---:|
| Clientes | 120 |
| Versões de clientes | 123 |
| Pedidos | 1.234 |
| Cliente/mês | 1.440 |
| Receita sintética | R$ 849.439,80 |
| Testes dbt após recuperação | 50 aprovados |

A conferência em Python conciliou receita e comportamento de compra. A repetição
preservou o conteúdo das tabelas. Quatro erros controlados foram detectados e
restaurados: vigências sobrepostas, desconto inválido, vendedor inexistente e
atribuição de pedido ao vendedor errado.

Todos os dados são sintéticos. O histórico conserva estados observados pelo
snapshot; não recupera mudanças que a origem não disponibilizou. As fatos usam
reconstrução completa, em um PostgreSQL local isolado.
## Comportamento e concentração

A massa inclui grandes contas, crescimento trimestral, queda de volume e sazonalidade de fim de ano. Explore `comportamento_clientes` para sinais de atenção, `retencao_coortes` para compra ao longo do tempo, `concentracao_receita` para dependência das maiores contas e `fato_itens_vendas` para o mix de categorias.

Os alertas são regras comerciais explicáveis, não previsão de churn. A referência de receita usa somente os três meses anteriores; a primeira compra da coorte é a primeira observada neste histórico.

{% enddocs %}
