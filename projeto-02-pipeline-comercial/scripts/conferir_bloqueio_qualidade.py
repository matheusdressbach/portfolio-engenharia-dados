"""Confere que a falha preservou publicados e watermarks no banco real local."""
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

caminho = Path(os.environ["LOCAL_DB_PATH"])
registro = caminho.parent / "qualidade-antes.json"
with sqlite3.connect(caminho.as_uri() + "?mode=ro", uri=True) as db:
    publicados = list(db.execute("SELECT entidade,chave,payload FROM publicados ORDER BY entidade,chave"))
    estado = {"watermarks": list(db.execute("SELECT entidade,valor FROM watermarks ORDER BY entidade")),
              "publicados_sha256": hashlib.sha256(json.dumps(publicados).encode()).hexdigest()}
    if sys.argv[1] == "antes":
        registro.write_text(json.dumps(estado, indent=2))
        print("Estado anterior registrado. Mantenha a DAG pausada até aplicar a alteração.")
    elif sys.argv[1] == "depois":
        anterior = json.loads(registro.read_text())
        # JSON converte tuplas em listas.
        if json.loads(json.dumps(estado)) != anterior:
            raise SystemExit("FALHOU: publicados ou watermarks mudaram durante o teste")
        falhas = list(db.execute("SELECT id,erro FROM execucoes WHERE status='falha' AND erro LIKE '%metas/2:%sem dimensão%'"))
        if not falhas:
            raise SystemExit("Ainda não há rejeição registrada para a meta do teste")
        print(json.dumps({"publicados_preservados": True, "watermarks_preservados": True,
                          "rejeicoes": falhas}, indent=2, ensure_ascii=False))
    else:
        raise SystemExit("Use antes ou depois")
