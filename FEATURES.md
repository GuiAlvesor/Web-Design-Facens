# Branch `features`

## Objetivo

A branch `features` é a origem de todo **conteúdo novo** (funcionalidades, melhorias e correções em desenvolvimento).

## Responsabilidades

- Receber commits de desenvolvimento ativo.
- Centralizar testes e validações iniciais.
- Servir de base para promoção de mudanças para `develop`.

## Fluxo de trabalho

1. Implementar conteúdo novo em `features`.
2. Validar localmente (testes, revisão e qualidade).
3. Abrir PR de `features` para `develop`.
4. Após aprovação/merge em `develop`, seguir com PR de `develop` para `main`.

## Boas práticas

- Evitar commits diretos em `main`.
- Evitar promover mudanças para `develop` sem validação prévia em `features`.
- Manter PRs pequenos e descritivos para facilitar revisão.

## Regra do fluxo

`features` -> `develop` -> `main`
