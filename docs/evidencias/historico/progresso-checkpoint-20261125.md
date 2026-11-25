# Progresso da implementação

Atualizado em 23/11/2026. Projeto acadêmico sem evento real.

## Retomada autorizada — 25/11/2026

- Usuário autorizou explicitamente o bootstrap restrito e continuidade da implantação, sem ampliar permissões e com parada final obrigatória.
- Número do projeto confirmado na API: `271680307280`; filtro do orçamento confere. Bootstrap aplicado: 27 criados, nenhum alterado/removido. Buckets privados, três contas sem chaves permanentes e WIF ACTIVE conferidos em `evidencias/bootstrap-validation.json`.
- Corrigida sintaxe HCL do arquivo gerado para backend; estado migrado para `todo/bootstrap`, prefixo principal `todo/main`.
- OIDC e plano pela automação passaram: run `45582818037`.
- Primeira criação de VMs falhou por `onHostMaintenance=TERMINATE` incompatível com E2 padrão. Corrigido para MIGRATE, preservando duração21600/STOP/automaticRestartfalse. Não houve ampliação de IAM.
- Provisionamento corrigido passou: run `45584126255`. API confirmou duas e2-micro em us-central1-a, Mongo sem IP público, limite nativo de21600segundos/STOP nas duas.
- Deploy e testes remotos em andamento: run `45584309429`, imagens `9a2747c` e `fa626de` para teste de troca/rollback. O workflow tenta parar ambas no final, inclusive em falha. Confirmar o estado real antes de encerrar a sessão.
- Esse primeiro deploy conseguiu SSH/scp pelo gcloud, mas o Ansible direto recusou a chave sem certificado. Ambas as VMs foram explicitamente paradas e confirmadas TERMINATED. Adaptado o transporte Ansible para gcloud por conexão, que renova certificados OS Login para identidade federada. Nenhuma nova permissão IAM foi adicionada. Retentativa: run `45585407780`, commit `51021a7`, com os mesmos dois SHAs de imagem.
- A retentativa confirmou o transporte (9 tarefas do host público passaram), mas perdeu autorização do IAP depois de expirar a credencial federada inicial. Ambas as VMs foram novamente paradas e confirmadas TERMINATED. Configurada emissão explícita de access token temporário3600s dentro do papel existente; não foram criadas chaves permanentes nem novos grants. Mongo passou a ser transferido comprimido. Nova retentativa: run `45588264540`, commit `b36ff36`; ainda em configuração no último checkpoint.
- Run45588264540 avançou até a inicialização Mongo privada, mas excedeu o prazo120s de saúde inicial. Parada das duas VMs confirmada. Diagnóstico automatizado45593069785 passou e também parou ambas: Mongo saudável após retomada, sem OOM/restarts registrados, VM953MiB e462MiB disponíveis na amostra. Não houve aumento de máquina.
- Corrigida a sonda para TCP no endereço do contêiner (o daemon temporário de init escuta só loopback); API mantém ping autenticado para readiness. Adicionados prazo300s de cold start, graça60s para parar Mongo e garantia idempotente do usuário da aplicação em volume parcialmente inicializado. Docker local e integração CI45594480653 passaram.
- Retentativa atual: run45594899799, commit0824404, mesmos SHAs de aplicação9a2747c/fa626de. Está configurando as VMs; confirmar testes e parada antes de encerrar. Checkpoint anterior de custo bruto/reservas: US$0,4173, não valor faturado, com quatro ciclos e ambas paradas naquele instante. Atualizar inventário/custos ao finalizar esta nova execução.
- Run45594899799 confirmou a sonda leve, mas o administrador Mongo não existia após a primeira inicialização interrompida. Diagnóstico registrou UserNotFound para administrator/admin, sem OOM/restarts, e as duas VMs terminaram TERMINATED. Implementada recuperação usando apenas localhost exception (válida somente quando não há usuários/roles), sem desligar auth, apagar volume ou redefinir usuário existente.
- Recuperação testada em Mongo real isolado: primeiro administrador e usuário readWrite criados, segunda execução idempotente, redefinição de administrador existente recusada e três documentos mantidos. Evidência `mongo-bootstrap-recovery.json`; teste adicionado à CI. Corrigido um erro de formatação YAML que o lint apontou; validação final passou sem avisos. Commits310b5e2 e719939b.
- Retentativa em andamento: **45599197611**, checkout310b5e2, imagens9a2747c/fa626de. Ainda falta comprovar HTTPS/CRUD/backup/rollback/idempotência remotos, testar o ciclo de reativação e confirmar a parada final. Não encerrar com VMs rodando.
- Testes adicionais implementados: persistência remota, isolamento de portas, troca real de imagem/rollback, backup via systemd, download GCS/restore isolado, renovação TLS dry-run e idempotência Ansible. Não considerar esses testes concluídos até a execução real passar.

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

## Histórico do bloqueio em 23/11/2026

O faturamento foi autorizado e vinculado somente ao projeto novo. APIs de controle Cloud Billing, Service Usage e Cloud Resource Manager foram habilitadas. Nenhum apply Terraform foi executado e nenhuma VM foi criada.

A aprovação automática rejeitou o bootstrap por alterar IAM, OIDC, contas de serviço, buckets, APIs e orçamento de forma persistente. A implementação foi reduzida a papel customizado de Compute, IAP condicional e prefixo de estado isolado; nova análise ainda exigiu aprovação direta do usuário desse escopo exato. A pergunta permanece pendente. Não houve tentativa de contornar a rejeição.

Branch publicada no fork. CI completa e GHCR passaram, incluindo testes Node/React, auditorias, Terraform/Ansible, integração com Mongo real, persistência, rollback de imagem e backup/restore isolado. Dispatch manual `Infrastructure → validate` passou na branch de implementação; autenticação GCP e apply foram pulados. Variáveis e secrets do fork cadastrados, sem imprimir valores nem criar identidades GCP. Contêineres locais parados e evidência final salva.

Após autorização do bootstrap: replanejar/aplicar, conferir outputs com as variáveis já cadastradas, validar plano principal, provisionar/configurar, medir e2-micro, testar HTTPS/isolamento/idempotência/backup/persistência e confirmar ambas VMs TERMINATED. Não executar destroy automaticamente. A aprovação ainda está pendente; não haverá execução após o fim desta sessão.


## Retomada autorizada em 25/11/2026

O usuário autorizou explicitamente o bootstrap restrito. Projeto confirmado na API: triodelicia-mensal4-2026, número 271680307280, também usado no filtro do orçamento. Plano bootstrap revisado: 27 criações, sem alteração ou exclusão. Aplicação e migração do estado ao GCS concluídas. Três contas de serviço sem chaves gerenciadas pelo usuário; OIDC e permissões limitadas conferidos. Workflow de plano 45582818037 validou autenticação OIDC e acesso ao estado remoto.

Infraestrutura aplicada pelo workflow 45584126255: duas e2-micro em us-central1-a, três discos Standard de 10 GiB, banco sem IP público. API confirmou máximo de 21600 segundos, ação STOP e reinício automático desabilitado. Novo plano registrou nove recursos sem alterações. Nenhuma ampliação do IAM aprovado foi necessária.

Correções durante as execuções reais: manutenção E2 usa MIGRATE; Ansible delega SSH ao gcloud para renovar certificados OS Login; tokens OAuth explícitos duram uma hora; imagem Mongo é transferida comprimida; healthcheck leve evita processos mongosh periódicos; inicialização admite 300 segundos; primeira criação interrompida é recuperada pela exceção localhost, sem apagar volume ou redefinir usuários existentes. O teste isolado de recuperação passou e a CI corrigida 45599619903 concluiu com sucesso.

Todas as tentativas anteriores encerraram com ambas as VMs TERMINATED. O deploy 45599197611 publicou a aplicação com certificado válido e readiness 200. O segundo Ansible falhou antes de concluir por conflito temporário de mutação do OS Login, sem alterações detectadas (changed=0). As duas VMs foram desligadas e conferidas TERMINATED. A correção aa728cd repete somente esse erro anterior à conexão; teste real de pipe binário de 1 MiB passou e erro de permissão permaneceu sem repetição. Novo deploy 45603866409 está em execução; idempotência, backup remoto, rollback e ciclo completo ainda dependem dos próximos testes. Não confundir esse checkpoint com o inventário final.
