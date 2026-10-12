{% snapshot clientes_carteira %}
{{ config(unique_key='id_cliente', strategy='timestamp', updated_at='atualizado_em') }}
select id_cliente, nome, id_vendedor, regiao, ativo, atualizado_em
from {{ source('erp', 'clientes') }}
{% endsnapshot %}
