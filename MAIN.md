# Branch `main`

## Objetivo

A branch `main` representa a versão **estável/produção** do projeto.

## Responsabilidades

- Receber somente mudanças aprovadas de `develop`.
- Manter histórico de versões estáveis.
- Servir como referência oficial de release.

## Fluxo de trabalho

1. Aguardar aprovação e merge de PR vindo de `develop`.
2. Publicar versão estável após integração.
3. Evitar commits diretos que quebrem a rastreabilidade do fluxo.

## Regra do fluxo

`features` -> `develop` -> `main`
