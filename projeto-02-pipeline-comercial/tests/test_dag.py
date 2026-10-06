import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("airflow"), "Airflow é validado na imagem Docker/CI")
class DagTest(unittest.TestCase):
    def test_dag_importa_e_define_dependencias(self):
        from airflow.models import DagBag
        pasta = Path(__file__).resolve().parents[1] / "dags"
        bag = DagBag(dag_folder=str(pasta), include_examples=False)
        self.assertEqual(bag.import_errors, {})
        # Inspeciona a DAG importada sem consultar o banco de metadados.
        self.assertIn("vendas_metas_diarias", bag.dags)
        dag = bag.dags["vendas_metas_diarias"]
        self.assertEqual(dag.max_active_runs, 1)
        self.assertFalse(dag.catchup)
        self.assertEqual(len(dag.tasks), 7)
        self.assertEqual(dag.get_task("transformar_staging").upstream_task_ids,
                         {"extrair_postgresql", "extrair_api"})
        self.assertEqual(dag.get_task("publicar_comercial").upstream_task_ids, {"validar_qualidade"})
        self.assertEqual(dag.get_task("sincronizar_sandbox").upstream_task_ids, {"publicar_comercial"})
        self.assertEqual(dag.get_task("extrair_api").retries, 2)


if __name__ == "__main__":
    unittest.main()
