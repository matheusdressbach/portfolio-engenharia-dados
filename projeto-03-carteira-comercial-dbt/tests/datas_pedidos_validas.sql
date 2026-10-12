select id_pedido from {{ ref('stg_pedidos') }}
where emitido_em is null or emitido_em < '2025-01-01'::timestamptz
    or emitido_em >= '2026-01-01'::timestamptz
