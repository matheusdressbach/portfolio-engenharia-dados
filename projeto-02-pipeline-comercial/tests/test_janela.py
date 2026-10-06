import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from enum import Enum

from pipeline_comercial.pipeline import limite_extracao


class JanelaTest(unittest.TestCase):
    def contexto(self, tipo):
        return {"dag_run": SimpleNamespace(run_type=tipo),
                "logical_date": datetime(2026, 10, 4, 0, 15, tzinfo=timezone.utc),
                "data_interval_end": datetime(2026, 10, 3, 9, tzinfo=timezone.utc)}

    def test_manual_inclui_alteracoes_apos_intervalo_diario(self):
        contexto = self.contexto("manual")
        self.assertEqual(limite_extracao(contexto), "2026-10-04T00:15:00+00:00")
        self.assertEqual(limite_extracao(contexto), limite_extracao(contexto))

    def test_agendada_preserva_intervalo_diario(self):
        self.assertEqual(limite_extracao(self.contexto("scheduled")), "2026-10-03T09:00:00+00:00")

    def test_tipo_enum_do_airflow(self):
        class Tipo(Enum):
            MANUAL = "manual"
        self.assertEqual(limite_extracao(self.contexto(Tipo.MANUAL)), "2026-10-04T00:15:00+00:00")
