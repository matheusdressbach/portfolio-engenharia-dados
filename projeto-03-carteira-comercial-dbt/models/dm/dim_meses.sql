select
    mes::date as competencia,
    (mes + interval '1 month')::timestamptz as fim_exclusivo
from generate_series(
    '2025-01-01'::timestamptz, '2025-12-01'::timestamptz, interval '1 month'
) as meses(mes)
