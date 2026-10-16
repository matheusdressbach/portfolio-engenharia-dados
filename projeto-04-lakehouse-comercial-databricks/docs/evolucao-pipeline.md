# Da origem local ao lakehouse

O Projeto 2 já resolve extração e orquestração. Para exercitar Databricks, a primeira entrega usa o mesmo contexto comercial, mas uma origem sintética própria: cada linha é uma versão de documento. Não há uma ligação operacional entre os ambientes nesta entrega.

A conexão seguinte pode ser uma exportação Python de documentos da origem PostgreSQL/API para JSONL, preservando IDs e versões. Esses arquivos devem seguir o contrato demonstrado aqui. O mesmo lote pode ser enviado duas vezes; uma correção precisa ter versão maior. O watermark da extração não substitui a precedência das versões no destino.

Antes de integrar, é preciso definir onde os arquivos serão armazenados, como chegam ao Volume e quais credenciais permitem essa transferência. A Free Edition tem restrições de conectividade. Nesta fase, o upload manual preserva a prática na plataforma sem acrescentar conta de armazenamento externa ou serviço pago.

## Ordem de aprendizado

1. Importar os notebooks e executar o primeiro lote; comparar Bronze, Silver e posição da carteira.
2. Executar os dois lotes seguintes e explicar quais rejeições saíram da quarentena quando as referências chegaram.
3. Repetir o lote 2 e conferir que o cancelamento e os valores consolidados permaneceram.
4. Consultar `DESCRIBE HISTORY` para entender os commits Delta e configurar o Job com dependência entre processamento e conferência.
5. Registrar a execução no workspace e responder às consultas comerciais antes de evoluir a ingestão.

A próxima etapa de engenharia será reduzir a leitura completa da Bronze, identificando chaves afetadas e referências pendentes. Isso precisa preservar a reavaliação de documentos atrasados. Streaming e conexão com a origem vêm depois que esse contrato estiver bem entendido.
