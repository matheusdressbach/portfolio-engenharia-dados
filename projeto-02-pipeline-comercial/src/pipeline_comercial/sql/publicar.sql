-- O cliente envia @id como parâmetro STRING.
-- DDL fora da transação; somente MERGE/UPDATE entram na publicação.
BEGIN TRANSACTION;
ASSERT (SELECT COUNT(*) = 1 FROM `__PROJETO__.operacao.execucoes` WHERE id=@id)
  AS 'Execução inexistente ou duplicada';
IF (SELECT status FROM `__PROJETO__.operacao.execucoes` WHERE id=@id) != 'sucesso' THEN
  ASSERT (SELECT status = 'aprovada' FROM `__PROJETO__.operacao.execucoes` WHERE id=@id)
    AS 'Qualidade ainda não aprovada';

  MERGE `__PROJETO__.dm.dim_vendedores` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.vendedores`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_vendedor ORDER BY atualizado_em DESC)=1
  ) s ON t.id_vendedor=s.id_vendedor
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    nome=s.nome,
    ativo=s.ativo,
    equipe=s.equipe,
    regiao=s.regiao,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_vendedor, nome, ativo, equipe, regiao, atualizado_em)
    VALUES (s.id_vendedor, s.nome, s.ativo, s.equipe, s.regiao, s.atualizado_em);

  MERGE `__PROJETO__.dm.dim_clientes` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.clientes`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_cliente ORDER BY atualizado_em DESC)=1
  ) s ON t.id_cliente=s.id_cliente
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    nome=s.nome,
    uf=s.uf,
    cidade=s.cidade,
    segmento=s.segmento,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_cliente, nome, uf, cidade, segmento, atualizado_em)
    VALUES (s.id_cliente, s.nome, s.uf, s.cidade, s.segmento, s.atualizado_em);

  MERGE `__PROJETO__.dm.dim_produtos` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.produtos`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_produto ORDER BY atualizado_em DESC)=1
  ) s ON t.id_produto=s.id_produto
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    descricao=s.descricao,
    categoria=s.categoria,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_produto, descricao, categoria, atualizado_em)
    VALUES (s.id_produto, s.descricao, s.categoria, s.atualizado_em);

  MERGE `__PROJETO__.comercial.fato_lancamento_vendas` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.vendas`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_lancamento ORDER BY atualizado_em DESC)=1
  ) s ON t.id_lancamento=s.id_lancamento
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    id_vendedor=s.id_vendedor,
    id_cliente=s.id_cliente,
    id_produto=s.id_produto,
    data_venda=s.data_venda,
    quantidade=s.quantidade,
    valor_bruto=s.valor_bruto,
    valor_desconto=s.valor_desconto,
    valor_liquido=s.valor_liquido,
    cancelado=s.cancelado,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_lancamento, id_vendedor, id_cliente, id_produto, data_venda, quantidade, valor_bruto, valor_desconto, valor_liquido, cancelado, atualizado_em)
    VALUES (s.id_lancamento, s.id_vendedor, s.id_cliente, s.id_produto, s.data_venda, s.quantidade, s.valor_bruto, s.valor_desconto, s.valor_liquido, s.cancelado, s.atualizado_em);

  MERGE `__PROJETO__.comercial.fato_devolucoes` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.devolucoes`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_devolucao ORDER BY atualizado_em DESC)=1
  ) s ON t.id_devolucao=s.id_devolucao
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    id_lancamento=s.id_lancamento,
    data_devolucao=s.data_devolucao,
    quantidade=s.quantidade,
    valor_devolvido=s.valor_devolvido,
    motivo=s.motivo,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_devolucao, id_lancamento, data_devolucao, quantidade, valor_devolvido, motivo, atualizado_em)
    VALUES (s.id_devolucao, s.id_lancamento, s.data_devolucao, s.quantidade, s.valor_devolvido, s.motivo, s.atualizado_em);

  MERGE `__PROJETO__.comercial.fato_metas_vendedores` t
  USING (
    SELECT * EXCEPT(execucao) FROM `__PROJETO__.staging.metas`
    WHERE execucao=@id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_meta ORDER BY atualizado_em DESC)=1
  ) s ON t.id_meta=s.id_meta
  WHEN MATCHED AND s.atualizado_em >= t.atualizado_em THEN UPDATE SET
    id_vendedor=s.id_vendedor,
    competencia=s.competencia,
    valor_meta=s.valor_meta,
    atualizado_em=s.atualizado_em
  WHEN NOT MATCHED THEN INSERT (id_meta, id_vendedor, competencia, valor_meta, atualizado_em)
    VALUES (s.id_meta, s.id_vendedor, s.competencia, s.valor_meta, s.atualizado_em);

  MERGE `__PROJETO__.operacao.watermarks` t
  USING (
    SELECT entidade, fim AS valor
    FROM `__PROJETO__.operacao.execucoes`,
      UNNEST(['vendedores','clientes','produtos','vendas','devolucoes','metas']) entidade
    WHERE id=@id
  ) s ON t.entidade=s.entidade
  WHEN MATCHED THEN UPDATE SET valor=GREATEST(t.valor,s.valor)
  WHEN NOT MATCHED THEN INSERT (entidade,valor) VALUES (s.entidade,s.valor);
  UPDATE `__PROJETO__.operacao.execucoes`
    SET status='sucesso', erro=NULL, atualizado_em=CURRENT_TIMESTAMP() WHERE id=@id;
END IF;
COMMIT TRANSACTION;
