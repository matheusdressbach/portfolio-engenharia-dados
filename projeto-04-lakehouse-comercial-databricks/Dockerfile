FROM apache/spark:4.0.0-python3@sha256:a89782d90529a623fc4471cdddb0f9c32d6eed10a81b256a80207b23c3b1df00
USER root
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /projeto
ENV PYTHONPATH=/projeto/notebooks:/projeto/scripts
ENTRYPOINT ["python3", "scripts/validar_spark.py"]
