# Contribuição e fluxo de versionamento

## Branches oficiais

O projeto adota um fluxo enxuto com duas branches:

- `main` (estável)
- `develop` (desenvolvimento)

## Política obrigatória

- Commits de novas funcionalidades, correções e refactors devem ser feitos em `develop`.
- A `main` deve receber código somente via merge/PR aprovado de `develop`.
- O histórico de evolução do projeto deve permanecer em `develop`.

## Processo de entrega

1. Atualize `develop`.
2. Implemente e commite em `develop`.
3. Abra PR `develop` -> `main` com descrição técnica e testes.
4. Faça merge em `main` apenas após revisão/aprovação.


## Verificação de conformidade

Antes de abrir PR, execute:

```bash
./scripts/verify_branch_policy.sh
```

O script valida:
- existência de `main` e `develop`;
- se `main` está contida em `develop` (histórico centralizado em desenvolvimento).
