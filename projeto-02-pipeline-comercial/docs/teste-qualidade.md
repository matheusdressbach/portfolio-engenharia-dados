# Rejeição de qualidade e recuperação

Use apenas o ERP sintético deste Docker. Pause a DAG e aguarde todas as execuções
terminarem. Não dispare outras cargas durante a comparação.

## Antes de alterar a origem

```sh
docker compose exec -T airflow-scheduler python - antes < scripts/conferir_bloqueio_qualidade.py
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U erp -d erp < sql/postgres/03_simular_falha_qualidade.sql
```

Despause a DAG, crie uma nova execução e aguarde a rejeição de `validar_qualidade`.
O log esperado contém `metas/2: id_vendedor sem dimensão`. Após os retries,
`publicar_comercial` e `sincronizar_sandbox` ficam `upstream_failed`.
Pause novamente. A falha é intencional e bloqueia a divulgação de uma meta inválida.

```sh
docker compose exec -T airflow-scheduler python - depois < scripts/conferir_bloqueio_qualidade.py
```

A verificação compara o conteúdo publicado e todos os watermarks com o estado
anterior. Ambos devem permanecer iguais. No BigQuery, repita a consulta das metas:
Bruno continua com id 2 e meta 800; não deve existir vendedor 999.

## Recuperação

```sh
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U erp -d erp < sql/postgres/04_corrigir_falha_qualidade.sql
```

Crie uma nova execução manual da DAG (não apenas Clear na validação, pois a origem
precisa ser extraída novamente). Aguarde sete tarefas verdes, pause e confira
metas e vendas. Esperado: Ana 1200, Bruno 800; vendas 3 / 1 / 330.
A versão inválida fica preservada na raw como evidência da falha.
Se interromper o teste, aplique a correção antes de retomar cargas normais.
