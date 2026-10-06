import json
import os
import subprocess

subprocess.run(["airflow", "db", "migrate"], check=True)
usuarios = json.loads(subprocess.check_output(["airflow", "users", "list", "--output", "json"], text=True))
if not any(u["username"] == "admin" for u in usuarios):
    subprocess.run(["airflow", "users", "create", "--username", "admin", "--firstname", "Dados",
                    "--lastname", "Comercial", "--role", "Admin", "--email", "admin@example.invalid",
                    "--password", os.environ["ADMIN_PASSWORD"]], check=True)
