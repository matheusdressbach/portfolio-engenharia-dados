# Portfólio de Engenharia de Dados — Matheus Dressbach

Estou construindo este portfólio para demonstrar, na prática, como organizo dados comerciais, confiro resultados e trato a operação de um pipeline. Os três projetos seguem uma sequência: primeiro a análise, depois a ingestão e a orquestração, e por fim o histórico necessário para interpretar a carteira ao longo do tempo.

O contexto comercial conecta os trabalhos. As entregas usam dados sintéticos, regras documentadas e cenários reproduzíveis; cada projeto registra o que foi validado e os limites da solução.

## Evolução dos projetos

| Etapa | Projeto | Pergunta central | O que demonstro |
|---|---|---|---|
| 1 · Organizar e conferir | [Análise comercial](projeto-01-analise-comercial/README.md) | Os indicadores representam corretamente as vendas? | Modelagem em camadas, SQL no BigQuery e conciliação em Python. |
| 2 · Construir e operar | [Pipeline comercial orquestrado](projeto-02-pipeline-comercial/README.md) | Como atualizar os dados e recuperar a execução quando algo falha? | PostgreSQL, REST API, Python e Airflow; carga incremental, watermarks, idempotência e bloqueio por qualidade. |
| 3 · Preservar e interpretar | [Histórico e análise da carteira](projeto-03-carteira-comercial-dbt/README.md) | Como analisar vendas e comportamento sem perder o contexto histórico do cliente? | dbt, snapshots, atribuição histórica, retenção por coorte, concentração de receita e sinais de queda comercial. |

## Projeto 1 — Análise comercial

Comecei pela organização das vendas, metas e previsões em `raw`, `staging`, `dm` e `comercial`. As consultas produzem indicadores comerciais no BigQuery, e uma conferência independente em Python concilia os lançamentos e os totais mensais.

A entrega inclui 848 lançamentos de venda, 18 meses analisados, 19 tabelas, 11 visualizações e cinco testes locais aprovados. A execução no BigQuery Sandbox foi registrada em 29/09/2026; os arquivos exportados permitem reproduzir a conferência offline.

[Explorar o Projeto 1](projeto-01-analise-comercial/README.md) · [Ver as evidências](projeto-01-analise-comercial/evidencias-projeto-1.md)

## Projeto 2 — Pipeline comercial orquestrado

O passo seguinte foi tratar a atualização e as falhas. Integrei PostgreSQL e uma REST API de metas, com tarefas orquestradas no Airflow e validação de qualidade antes da publicação. O cenário inclui reexecução, dados inválidos e recuperação, com preservação dos dados publicados e dos watermarks quando a qualidade bloqueia a carga.

A base contém 5.000 vendas, 144 metas e 180 devoluções. A transformação e o controle incremental rodam localmente; as tabelas consolidadas são sincronizadas com o BigQuery Sandbox. O MERGE em BigQuery é uma alternativa documentada, não uma execução validada no Sandbox.

[Explorar o Projeto 2](projeto-02-pipeline-comercial/README.md) · [Ver as evidências](projeto-02-pipeline-comercial/docs/evidencias-visuais.md)

## Projeto 3 — Histórico e análise da carteira

Uma mudança de vendedor não deve reatribuir as vendas antigas. Trabalhei esse problema com snapshots de clientes no dbt, separando o responsável vigente na emissão do pedido e a carteira no fechamento mensal. Um pedido atrasado e uma venda na fronteira entre versões verificam essa regra.

A análise inclui clientes que ainda compram, mas reduziram sua receita, retenção por coorte, concentração nos maiores compradores e mix de categorias. A massa possui 120 clientes, 1.234 pedidos e 123 versões de cadastro. Os 50 testes e a conciliação em Python passaram localmente; a integração também foi [validada no GitHub Actions](https://github.com/matheusdressbach/portfolio-engenharia-dados/actions/runs/38323258198).

[Explorar o Projeto 3](projeto-03-carteira-comercial-dbt/README.md) · [Ler as análises](projeto-03-carteira-comercial-dbt/docs/analises.md) · [Ver a validação](projeto-03-carteira-comercial-dbt/docs/validacao.md)

## Como navegar e reproduzir

Cada pasta tem seu próprio README, instruções de execução e registros de validação. O Projeto 1 oferece reprodução offline com Python. Os projetos 2 e 3 usam Docker; o Projeto 3 executa inteiramente de forma local. Para trabalhar com BigQuery, consulte as condições do Sandbox documentadas nos projetos 1 e 2.

Este portfólio reúne as entregas técnicas que sustentam a apresentação dos projetos no meu LinkedIn: o problema de negócio, as escolhas de engenharia e a evidência do resultado. A sequência mostra competências complementares, sem tratar os três casos como um único ambiente de produção.
