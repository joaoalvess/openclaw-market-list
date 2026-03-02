# lista-mercado

Skill para gerenciar lista de compras de forma rápida, com persistência local em JSON e sugestões inteligentes de itens relacionados.

## O que este projeto faz

A `lista-mercado` foi criada para manter uma lista de compras simples e prática, com dois comandos principais:

- `add <item> [quantidade]` → adiciona itens na lista
- `list` → mostra a lista atual formatada

Além disso, ao adicionar um item, a skill sugere produtos que normalmente são comprados juntos.

---

## Estrutura do projeto

```text
lista-mercado/
├── SKILL.md
├── README.md
├── scripts/
│   └── market.py
├── references/
│   └── pairs.md
└── data/
    └── shopping-list.json
```

- **SKILL.md**: descrição e instruções de uso da skill
- **scripts/market.py**: lógica principal (`add` e `list`)
- **references/pairs.md**: base curada de sugestões por co-compra
- **data/shopping-list.json**: persistência da lista (criado/atualizado em runtime)

---

## Como usar

No diretório do projeto:

```bash
python3 scripts/market.py add arroz
python3 scripts/market.py add arroz 5kg
python3 scripts/market.py add cafe
python3 scripts/market.py list
```

---

## Comportamento inteligente

### Normalização de itens

O script aplica regras para manter consistência:

- lowercase
- remoção de espaços extras
- matching sem acento (interno)
- alguns sinônimos curados (ex.: `café em pó` → `cafe`)
- plural simples em casos comuns (ex.: `ovos` → `ovo`)

### Regras do `add`

- Se já existir item com mesmo `name + unit`, soma quantidade
- Caso contrário, cria novo item
- Salva com escrita atômica (arquivo temporário + rename)
- Retorna confirmação curta + sugestões (3 a 5)

### Sugestões (cross-sell)

1. Usa pares curados em `references/pairs.md`
2. Se faltar sugestão, aplica fallback por categoria
3. Remove duplicados e itens já existentes na lista

---

## Formato de dados (JSON)

Exemplo simplificado:

```json
{
  "version": 1,
  "updatedAt": "2026-03-02T18:00:00Z",
  "items": [
    {
      "name": "arroz",
      "qty": 5,
      "unit": "kg",
      "addedAt": "2026-03-02T18:00:00Z"
    }
  ]
}
```

---

## Tratamento de erros

- Item vazio → `Informe um item para adicionar.`
- Quantidade inválida → `Quantidade inválida. Exemplo: add arroz 5kg`
- JSON corrompido → backup automático + reset controlado

---

## Status atual (v1)

Implementado:

- [x] Comando `add`
- [x] Comando `list`
- [x] Persistência em JSON
- [x] Sugestões de itens relacionados
- [x] Escrita atômica
- [x] Mensagens em português

---

## Próximos passos (v2+)

- `remove <item>`
- `done <item>`
- múltiplas listas (ex.: casa, churrasco)
- exportação para WhatsApp
- estimativa de preço
- recomendações por perfil

---

Feito com foco em simplicidade, velocidade e utilidade no dia a dia.
