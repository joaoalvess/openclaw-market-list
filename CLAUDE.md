# CLAUDE.md — lista-mercado

## Visão Geral

`lista-mercado` é uma skill simples para gerenciar lista de compras com persistência local em JSON.

Objetivo da v1:
- adicionar itens com quantidade opcional (`add`)
- listar itens atuais (`list`)
- sugerir itens relacionados no `add`

---

## Estrutura do Projeto

```text
lista-mercado/
├── SKILL.md
├── README.md
├── CLAUDE.md
├── scripts/
│   └── market.py
├── references/
│   └── pairs.md
└── data/
    └── shopping-list.json
```

---

## Comandos Principais

Executar a partir da raiz do projeto:

```bash
python3 scripts/market.py add arroz
python3 scripts/market.py add arroz 5kg
python3 scripts/market.py add cafe
python3 scripts/market.py list
```

### Regras do `add`
- Entrada: `add <item> [quantidade]`
- Se `name + unit` já existir, soma quantidade
- Se não existir, cria novo item
- Retorna confirmação + 3 a 5 sugestões

### Regras do `list`
- Mostra lista numerada
- Exibe total de itens
- Se vazia, retorna mensagem amigável

---

## Formato JSON

Arquivo: `data/shopping-list.json`

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

Campos:
- `version`: versão do schema
- `updatedAt`: última atualização da lista
- `items[]`:
  - `name` (string normalizada)
  - `qty` (number, default 1)
  - `unit` (string: kg, g, un, l, ml...)
  - `addedAt` (ISO datetime)

---

## Decisões de Arquitetura (v1)

- Script único em Python (`scripts/market.py`) para simplicidade e portabilidade
- Persistência em JSON local para evitar dependências externas
- Escrita atômica (`tmp + rename`) para reduzir risco de corrupção
- Sugestões por base curada (`references/pairs.md`) + fallback por categoria

---

## Roadmap

Próximas evoluções sugeridas:
- `remove <item>`
- `done <item>`
- múltiplas listas (`casa`, `churrasco`, etc.)
- exportar lista para WhatsApp
- estimativa de preço por item

---

## Convenções de Contribuição

- Mensagens e documentação em português
- Commits com Conventional Commits
- Evitar dependências externas na v1
- Testar casos básicos e de borda antes de subir

Exemplos de commit:
- `feat: adicionar comando remove`
- `fix: corrigir parse de quantidade com vírgula`
- `docs: atualizar exemplos do README`
