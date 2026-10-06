.PHONY: demo teste subir bootstrap parar movimento
demo:
	docker compose run --rm --no-deps demo
teste:
	docker compose run --rm --no-deps testes
subir:
	mkdir -p secrets
	docker compose up -d --build postgres api-metas airflow-init airflow-webserver airflow-scheduler
bootstrap:
	docker compose run --rm airflow-cli python -m pipeline_comercial.cli bootstrap
parar:
	docker compose down
movimento:
	docker compose exec -T postgres psql -U erp -d erp < sql/postgres/02_simular_movimento.sql
