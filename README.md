# Web-Design-Facens

Repositório destinado aos projetos da disciplina de Desenvolvimento Web II.

## Padrão de branches do projeto

Este repositório foi padronizado para trabalhar com **três branches principais**:

- `features`: branch de entrada para conteúdo novo.
- `develop`: branch de homologação e consolidação.
- `main`: branch de produção/estável.

### Regras de trabalho

1. Todo conteúdo novo deve entrar primeiro em `features`.
2. Após validação, as mudanças devem ser promovidas de `features` para `develop`.
3. A `main` deve receber somente integrações validadas de `develop` (por PR/merge).
4. Nunca commitar diretamente na `main`.

### Fluxo recomendado

1. Criar alterações em `features`.
2. Validar as mudanças e abrir PR de `features` para `develop`.
3. Quando `develop` estiver estável, abrir PR de `develop` para `main`.
4. Após aprovação, fazer merge na `main`.


## Documentação por branch

- [`FEATURES.md`](FEATURES.md): entrada de conteúdo novo.
- [`DEVELOP.md`](DEVELOP.md): validação e consolidação.
- [`MAIN.md`](MAIN.md): versão estável de produção.

Regra oficial de promoção: `features` -> `develop` -> `main`.
