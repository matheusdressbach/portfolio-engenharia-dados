select * from {{ ref('dim_clientes') }}
where vigencia_inicio is null
   or (vigencia_fim is not null and vigencia_fim <= vigencia_inicio)
