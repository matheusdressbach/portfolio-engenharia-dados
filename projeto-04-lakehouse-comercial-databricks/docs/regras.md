# Regras da posição comercial

Cada pedido representa uma linha de produto. Um pedido pode ter vários documentos de faturamento; cada devolução aponta para um deles. Ainda não há pedidos com vários itens, impostos, frete ou custos. Não calculamos margem nem receita contábil reconhecida.

- A origem entrega `id_evento`, `entidade`, `id_registro`, `versao` e `atualizado_em`. A versão é crescente por registro e decide a precedência. O timestamp é informativo e validado; não substitui a sequência da origem.
- Uma versão repetida precisa ter o mesmo conteúdo, mesmo que receba outro ID de evento. Empates com conteúdo distinto falham antes de aceitar o lote na Bronze.
- Duplicatas exatas não geram novas linhas Bronze. Logo, essa tabela guarda eventos distintos, não um registro de todas as tentativas de entrega.
- Campos inválidos ficam na quarentena. Uma correção precisa trazer uma versão nova. O evento negativo anterior permanece como rejeição histórica, mesmo depois de corrigido.
- Documentos sem referência válida são reavaliados quando novos lotes chegam. Por isso a seleção atual lê toda a Bronze nesta massa pequena. Não há watermark de timestamp: ele poderia descartar documentos atrasados.
- Quantidade faturada não pode ultrapassar a pedida. A soma das devoluções não pode ultrapassar o documento faturado correspondente. Esses erros bloqueiam a atualização Silver até chegar uma correção, preservando a posição anterior.
- Um pedido cancelado mantém o faturamento que já ocorreu; o saldo restante vira quantidade cancelada. Estorno de faturamento zera sua contribuição. Uma devolução reduz o valor faturado líquido, mas não reabre automaticamente a carteira.

A posição deve fechar: `pedida = faturada + aberta + cancelada`. A receita após devolução é `valor_faturado - valor_devolvido`. Todos os documentos usam o preço do pedido; não há preços diferentes por nota nesta versão.

## Persistência e limite operacional

O MERGE é transacional por tabela Delta. O lote inteiro não é uma transação entre várias tabelas: Bronze e quarentena podem avançar mesmo se a consolidação falhar. Erros de quantidade são verificados antes dos MERGEs Silver; uma falha técnica entre os MERGEs exige reexecução. As views Gold leem o estado Silver disponível. Esta primeira versão deve rodar com um escritor e sem consultas concorrentes durante a atualização.

As dimensões mantêm o cadastro atual. Diferentemente do Projeto 3, este projeto não demonstra histórico de vendedores. A prioridade é o ciclo dos documentos comerciais e a aplicação de versões fora de ordem.

`p4_controle.execucoes` registra tentativas bem-sucedidas e falhas, duração, contagens e mensagem de erro. Reexecuções geram novos registros operacionais, mas não duplicam os documentos comerciais. A quarentena mostra rejeições de campos históricos e referências ainda pendentes; não substitui esse registro de tentativas.
