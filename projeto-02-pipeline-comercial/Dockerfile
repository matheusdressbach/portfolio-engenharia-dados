FROM apache/airflow:2.11.2-python3.11
USER root
RUN mkdir -p /opt/airflow/dados && chown airflow:root /opt/airflow/dados
USER airflow
WORKDIR /opt/airflow
COPY --chown=airflow:root pyproject.toml ./
COPY --chown=airflow:root src ./src
# Reafirma a versão do Airflow para impedir que a instalação do projeto a altere.
RUN pip install --no-cache-dir "apache-airflow==2.11.2" ".[cloud,test]"
COPY --chown=airflow:root dags ./dags
COPY --chown=airflow:root tests ./tests
COPY --chown=airflow:root scripts ./scripts
