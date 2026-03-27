# Web-Design-Facens

Repositório destinado aos projetos da disciplina de Desenvolvimento Web II.

## Padrão de branches do projeto

Este repositório foi padronizado para trabalhar com **apenas duas branches**:

- `main`: branch de produção/estável.
- `develop`: branch alternativa de desenvolvimento.

### Regras de trabalho

1. Todo desenvolvimento deve acontecer em `develop`.
2. O histórico completo de commits fica concentrado em `develop`.
3. A `main` deve receber somente integrações validadas de `develop` (por PR/merge).
4. Nunca commitar diretamente na `main`.

### Fluxo recomendado

1. Criar alterações em `develop`.
2. Abrir PR de `develop` para `main` quando a entrega estiver estável.
3. Após aprovação, fazer merge na `main`.


### Verificação automática da política

Para validar localmente se a política está sendo respeitada:

```bash
./scripts/verify_branch_policy.sh
```

Também há uma workflow de CI em `.github/workflows/branch-policy.yml` que roda essa verificação em push/PR.
