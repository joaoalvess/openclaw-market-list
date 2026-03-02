---
name: lista-mercado
description: Gerencia lista de mercado com comandos add e list, persistência em JSON e sugestões de itens relacionados. Use quando o usuário quiser adicionar itens de compra rapidamente, consultar a lista atual ou receber recomendações do que comprar junto.
---

# lista-mercado

Use o script `scripts/market.py` para executar os comandos.

## Comandos
- `add <item> [quantidade]`
- `list`

## Formato de uso
- `python3 scripts/market.py add arroz`
- `python3 scripts/market.py add arroz 5kg`
- `python3 scripts/market.py add leite 6un`
- `python3 scripts/market.py list`

## Persistência
- Arquivo padrão: `lista-mercado/data/shopping-list.json`
- Escrita atômica: arquivo temporário + rename.

## Normalização
- lowercase
- trim de espaços extras
- remoção de acento para matching interno
- sinônimos curados (ex.: `café em pó` → `café`)
- plural simples em casos comuns (ex.: `ovos` → `ovo`)

## Sugestões
- Primeiro tenta pares curados de `references/pairs.md`.
- Se não encontrar, usa fallback por categoria.
- Remove itens já presentes na lista.
- Limita entre 3 e 5 sugestões.

## Mensagens de erro comuns
- Item vazio: `Informe um item para adicionar.`
- Quantidade inválida: `Quantidade inválida. Exemplo: add arroz 5kg`
- JSON corrompido: backup automático + reset controlado.
