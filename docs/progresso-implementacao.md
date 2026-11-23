# Progresso da implementação

Atualizado em 23/11/2026. Projeto acadêmico sem evento real.

## Estado inicial verificado

- Branch `feat/infra-terraform-ansible-actions`, criada sobre `4814004`.
- `main` preservada e tracking ajustado para `origin/main`; upstream mantido.
- Projeto GCP `triodelicia-mensal4-2026` ACTIVE, sem organização; faturamento inicialmente desabilitado.
- Auditoria anterior comprovou build e CRUD HTTP local e persistência no mesmo container. Não comprovou recriação/backup/HTTPS.
- Base tem credenciais demonstrativas administrativas, localhost fixo, porta Mongo pública no Compose, sem persistência explícita, saúde ou pipelines.
- Baseline npm anterior: backend 6 vulnerabilidades e frontend 64; frontend usa teste CRA desatualizado, backend teste placeholder.

## Etapas

| Etapa | Estado | Evidência / pendência |
| --- | --- | --- |
| Diagnóstico | Concluído localmente | Baseline ambos testes originais falharam; docs/evidencias/baseline.json |
| Aplicação | Validada localmente | CRUD, readiness, recriação do banco, reinício e atualização preservam dados |
| Terraform | Schema validado | Provider 7.46.2 aceitou scheduling.max_run_duration 21600 + STOP; bootstrap plan executado |
| Ansible | Lint validado | 0 falhas/avisos no perfil production; execução remota/idempotência pendentes |
| Actions/GHCR | CI e publicação verificadas | Execuções completas passaram; imagens frontend/backend no GHCR por SHA. Dispatch Terraform validate passou sem GCP |
| Backup/restore/rollback | Validados localmente | Hash restaurado confere; produção não sobrescrita; duas imagens reais, rollback e recuperação de imagem defeituosa passaram |
| HTTPS/GCP | Bloqueado por aprovação de segurança | Faturamento vinculado; bootstrap restrito aguarda resposta explícita após rejeição automática |
| Desligamento final | Local concluído; nenhuma VM criada | Contêineres locais Exited(0), volumes/backups preservados; Compute e Storage APIs permanecem desabilitadas |

Não há execução de nuvem declarada concluída. Resultados serão registrados após testes.

## Correções comprovadas durante os testes

- Migração CRA/Jest/Axios para Vite/Vitest/fetch reduziu o grafo de dependências; testes e build passaram, npm audit sem avisos conhecidos.
- Integração real identificou a exigência `updatePipeline: true` no Mongoose 9; adicionada e CRUD revalidado.
- Nginx usa resolução Docker dinâmica para sobreviver à recriação do backend.
- Backup bloqueia gravações brevemente, valida a restauração em rede/volume separados e reinicia o banco principal por trap. Execução local confirmou hash igual sem sobrescrever dados principais.
- Argumentos Terraform e encoding UTF-8 tratados no wrapper Python para execução Windows reprodutível.
- Reexecução do teste de release no Windows precisava liberar o atributo somente leitura do arquivo de secret antes de copiá-lo novamente; corrigido.
- Reativação agora sobe os contêineres explicitamente, banco antes da aplicação: o desligamento gracioso deixa containers parados e `unless-stopped` sozinho não os reinicia após boot.
- Terraform fmt/validate em ambos módulos, actionlint, ShellCheck e Ansible lint passaram. Testes HTTP/provider exigem execução fora do sandbox para abrir seus canais locais; isso não é falha da aplicação.

## Bloqueio de nuvem

O faturamento foi autorizado e vinculado somente ao projeto novo. APIs de controle Cloud Billing, Service Usage e Cloud Resource Manager foram habilitadas. Nenhum apply Terraform foi executado e nenhuma VM foi criada.

A aprovação automática rejeitou o bootstrap por alterar IAM, OIDC, contas de serviço, buckets, APIs e orçamento de forma persistente. A implementação foi reduzida a papel customizado de Compute, IAP condicional e prefixo de estado isolado; nova análise ainda exigiu aprovação direta do usuário desse escopo exato. A pergunta permanece pendente. Não houve tentativa de contornar a rejeição.

Branch publicada no fork. CI completa e GHCR passaram, incluindo testes Node/React, auditorias, Terraform/Ansible, integração com Mongo real, persistência, rollback de imagem e backup/restore isolado. Dispatch manual `Infrastructure → validate` passou na branch de implementação; autenticação GCP e apply foram pulados. Variáveis e secrets do fork cadastrados, sem imprimir valores nem criar identidades GCP. Contêineres locais parados e evidência final salva.

Após autorização do bootstrap: replanejar/aplicar, conferir outputs com as variáveis já cadastradas, validar plano principal, provisionar/configurar, medir e2-micro, testar HTTPS/isolamento/idempotência/backup/persistência e confirmar ambas VMs TERMINATED. Não executar destroy automaticamente. A aprovação ainda está pendente; não haverá execução após o fim desta sessão.
