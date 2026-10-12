# Modelo e captura do histórico

| Relação | Grão |
|---|---|
| `raw.clientes` | Cadastro atual de um cliente |
| `raw.pedidos` | Um pedido |
| `raw.itens_pedidos` | Um item identificado de pedido |
| `historico.clientes_carteira` | Uma versão observada de cliente pelo snapshot |
| `dm.dim_clientes` | Uma versão de cliente com chave e vigência |
| `dm.dim_vendedores` | Um vendedor atual |
| `dm.dim_produtos` | Um produto atual |
| `dm.dim_meses` | Um mês de 2025 |
| `comercial.fato_pedidos` | Um pedido com vendedor histórico |
| `comercial.fato_carteira_mensal` | Um cliente por mês |
| `comercial.desempenho_vendedores` | Um vendedor por mês |

O snapshot usa estratégia `timestamp`, chave `id_cliente` e campo `atualizado_em`.
A chave `dbt_scd_id` identifica a versão. `dbt_valid_from` e `dbt_valid_to` são
expostos como `vigencia_inicio` e `vigencia_fim`; fim nulo representa a versão atual.

Os timestamps são tratados em UTC. O cadastro inicial tem vigência desde dezembro
de 2024 para cobrir todos os pedidos do ano de análise. Os dois movimentos são
observados em sequência, com timestamps de julho e setembro de 2025. Esses instantes
são parte do cenário sintético, e não o horário real em que o teste foi executado.

O snapshot lê a tabela de origem diretamente. As views staging organizam as colunas;
a origem já tem tipos definidos. `ref()` e `source()` expressam as dependências,
sem nomes de banco fixos dentro dos modelos.

A macro de schema conserva a nomenclatura `dm` e `comercial`. Por isso, ambientes
de execução precisam usar bancos separados; mudar apenas o schema do perfil não
isola o projeto. O Compose já cria um banco exclusivo.

A massa e o cálculo de conferência estão em `scripts/dados.py`. O roteiro
`scripts/verificar_integracao.py` carrega a origem, chama o dbt e compara os resultados
com o cálculo em Python. Ele não executa o SQL dos modelos para gerar o esperado.

Referências usadas: [snapshots](https://docs.getdbt.com/docs/build/snapshots),
[estratégia timestamp](https://docs.getdbt.com/reference/resource-configs/strategy)
e [adaptador PostgreSQL](https://docs.getdbt.com/docs/local/connect-data-platform/postgres-setup).
