-- Datasets são criados pelo comando bootstrap na região configurada.
CREATE TABLE IF NOT EXISTS `__PROJETO__.operacao.execucoes` (
 id STRING NOT NULL, fim TIMESTAMP NOT NULL, limites STRING NOT NULL,
 status STRING NOT NULL, erro STRING, atualizado_em TIMESTAMP
) CLUSTER BY id;
CREATE TABLE IF NOT EXISTS `__PROJETO__.operacao.watermarks` (
 entidade STRING NOT NULL, valor TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS `__PROJETO__.raw.registros` (
 execucao STRING NOT NULL, entidade STRING NOT NULL, chave STRING NOT NULL,
 versao TIMESTAMP NOT NULL, payload STRING NOT NULL
) PARTITION BY DATE(versao) CLUSTER BY execucao, entidade;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.vendedores` (
  execucao STRING NOT NULL,
  id_vendedor INT64 NOT NULL,
  nome STRING NOT NULL,
  ativo BOOL NOT NULL,
  equipe STRING NOT NULL,
  regiao STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.dm.dim_vendedores` (
  id_vendedor INT64 NOT NULL,
  nome STRING NOT NULL,
  ativo BOOL NOT NULL,
  equipe STRING NOT NULL,
  regiao STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY id_vendedor;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.clientes` (
  execucao STRING NOT NULL,
  id_cliente INT64 NOT NULL,
  nome STRING NOT NULL,
  uf STRING NOT NULL,
  cidade STRING NOT NULL,
  segmento STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.dm.dim_clientes` (
  id_cliente INT64 NOT NULL,
  nome STRING NOT NULL,
  uf STRING NOT NULL,
  cidade STRING NOT NULL,
  segmento STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY id_cliente;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.produtos` (
  execucao STRING NOT NULL,
  id_produto INT64 NOT NULL,
  descricao STRING NOT NULL,
  categoria STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.dm.dim_produtos` (
  id_produto INT64 NOT NULL,
  descricao STRING NOT NULL,
  categoria STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY id_produto;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.vendas` (
  execucao STRING NOT NULL,
  id_lancamento INT64 NOT NULL,
  id_vendedor INT64 NOT NULL,
  id_cliente INT64 NOT NULL,
  id_produto INT64 NOT NULL,
  data_venda DATE NOT NULL,
  quantidade INT64 NOT NULL,
  valor_bruto NUMERIC NOT NULL,
  valor_desconto NUMERIC NOT NULL,
  valor_liquido NUMERIC NOT NULL,
  cancelado BOOL NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.comercial.fato_lancamento_vendas` (
  id_lancamento INT64 NOT NULL,
  id_vendedor INT64 NOT NULL,
  id_cliente INT64 NOT NULL,
  id_produto INT64 NOT NULL,
  data_venda DATE NOT NULL,
  quantidade INT64 NOT NULL,
  valor_bruto NUMERIC NOT NULL,
  valor_desconto NUMERIC NOT NULL,
  valor_liquido NUMERIC NOT NULL,
  cancelado BOOL NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) PARTITION BY data_venda CLUSTER BY id_lancamento;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.devolucoes` (
  execucao STRING NOT NULL,
  id_devolucao INT64 NOT NULL,
  id_lancamento INT64 NOT NULL,
  data_devolucao DATE NOT NULL,
  quantidade INT64 NOT NULL,
  valor_devolvido NUMERIC NOT NULL,
  motivo STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.comercial.fato_devolucoes` (
  id_devolucao INT64 NOT NULL,
  id_lancamento INT64 NOT NULL,
  data_devolucao DATE NOT NULL,
  quantidade INT64 NOT NULL,
  valor_devolvido NUMERIC NOT NULL,
  motivo STRING NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY id_devolucao;

CREATE TABLE IF NOT EXISTS `__PROJETO__.staging.metas` (
  execucao STRING NOT NULL,
  id_meta INT64 NOT NULL,
  id_vendedor INT64 NOT NULL,
  competencia DATE NOT NULL,
  valor_meta NUMERIC NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY execucao;
CREATE TABLE IF NOT EXISTS `__PROJETO__.comercial.fato_metas_vendedores` (
  id_meta INT64 NOT NULL,
  id_vendedor INT64 NOT NULL,
  competencia DATE NOT NULL,
  valor_meta NUMERIC NOT NULL,
  atualizado_em TIMESTAMP NOT NULL
) CLUSTER BY id_meta;
