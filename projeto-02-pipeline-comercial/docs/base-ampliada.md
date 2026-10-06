# Uma base comercial com histórico e devoluções

Distribuidora fictícia de alimentos com 12 vendedores atendendo 200 clientes em
12 cidades. O histórico cobre outubro de 2025 a setembro de 2026, com mais vendas
em novembro e dezembro, clientes recorrentes, descontos, cancelamentos e devoluções.
É uma simulação de comportamento comercial, não uma amostra de mercado real.

O gerador usa semente 42, Decimal e chaves reservadas. Não regrava os lançamentos
1001 a 1003 nem as metas 1 e 2. As dimensões iniciais recebem atributos de equipe,
região, cidade, segmento e categoria. Existem 4.997 novas vendas e 142 novas metas;
no ambiente já validado, o total será 5.000 vendas e 144 metas. Em um banco novo,
sem executar o movimento inicial, serão 4.999 vendas (a terceira não existe).

| Entidade | Total no ambiente já validado |
|---|---:|
| Vendedores | 12 |
| Clientes | 200 |
| Produtos | 40 |
| Lançamentos de vendas | 5.000 |
| Metas vendedor/mês | 144 |
| Devoluções | 180 |

O grão de `comercial.fato_devolucoes` é um evento de devolução de um lançamento.
Ela guarda quantidade, valor, data e motivo. O vendedor e o produto são obtidos
pela venda original. A regra de qualidade considera devoluções já publicadas e
novas: o acumulado não pode superar quantidade ou receita líquida da venda;
a venda precisa existir e não estar cancelada. Uma correção de venda que viole
essas condições também bloqueia a publicação.

## Atualizar o Docker existente

Pause a DAG e aguarde todas as execuções terminarem. Não use `down -v`.
Aplique primeiro a migração aditiva, depois a massa gerada, em transações separadas:

```sh
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U erp -d erp < sql/postgres/05_ampliar_modelo.sql
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U erp -d erp < sql/postgres/06_popular_comercial.sql
docker compose up -d --build
docker compose run --rm testes
```

A migração não altera o SQLite: a nova entidade ganha seu watermark na primeira
publicação. O SQL da massa carimba `atualizado_em` no instante da carga, mesmo que
a data comercial seja antiga. Assim o incremental captura o histórico importado.
Reaplicar o SQL não duplica vendas, metas ou devoluções. As dimensões são regravadas
com atributos determinísticos e timestamp novo. O arquivo não cria um quarto
movimento e não modifica lançamentos comerciais existentes nas chaves reservadas.

Dispare uma **nova execução manual**. Não reexecute uma janela antiga da versão
anterior que desconhecia devoluções. Aguarde sete tarefas verdes e pause novamente.
O Sandbox passa a publicar seis tabelas, ainda sem DML; o batch load substitui os
esquemas das dimensões pelos esquemas ampliados. Não há transação entre as cargas.

Execute `sql/bigquery/conferir_base_ampliada.sql`, substituindo `__PROJETO__` por
`pipeline-comercial-md`. Compare com `docs/evidencias/base-ampliada-esperado.json`.
Esse arquivo contém resultado calculado localmente, não evidência de carga na nuvem.
Depois repita uma execução sem mudanças para comprovar ausência de duplicações.

## Reproduzir a massa

```sh
PYTHONPATH=src python -m pipeline_comercial.populacao
```

O SQL é gerado sem conexão com banco ou Google Cloud. O conteúdo é determinístico;
os timestamps efetivos dependem do momento em que é aplicado.

## Análise comercial

`desempenho_comercial.sql` compara receita após devoluções com metas por mês e
vendedor. A devolução é atribuída ao mês da venda original: trata-se da análise
por safra de vendas, e não fluxo de caixa do mês da devolução. O SQL agrega os
eventos antes do join para evitar multiplicar vendas ou metas. A origem continua
separada: PostgreSQL fornece fatos e dimensões; REST API fornece metas.

A implementação alternativa com MERGE teve os SQLs regenerados para seis entidades.
Ela permanece não validada nesta conta. Para banco BigQuery já existente no modo
pago, o DDL CREATE IF NOT EXISTS não migra dimensões antigas: é necessário aplicar
migração explícita das colunas antes de usar esse modo. Nosso Sandbox usa batch load.
