# Contribuição e fluxo de versionamento

## Branches oficiais

O projeto adota um fluxo em três etapas com as branches:

- `features` (entrada de conteúdo novo)
- `develop` (homologação/consolidação)
- `main` (estável/produção)

## Política obrigatória

- Commits de novas funcionalidades, correções e refactors devem ser feitos em `features`.
- A `develop` deve receber mudanças validadas via merge/PR aprovado de `features`.
- A `main` deve receber código somente via merge/PR aprovado de `develop`.

## Processo de entrega

1. Atualize `features`.
2. Implemente e commite em `features`.
3. Valide e abra PR `features` -> `develop` com descrição técnica e testes.
4. Após aprovação em `develop`, abra PR `develop` -> `main`.
5. Faça merge em `main` apenas após revisão/aprovação final.


## Documentação por branch

- `FEATURES.md`
- `DEVELOP.md`
- `MAIN.md`

Fluxo obrigatório: `features` -> `develop` -> `main`.
