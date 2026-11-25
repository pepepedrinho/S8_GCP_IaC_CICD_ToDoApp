# Índice e origem das evidências

Atualização:25/11/2026. Projeto exclusivo triodelicia-mensal4-2026. O relatório e a matriz relacionam os seis requisitos e dez critérios aos resultados. As conclusões abaixo distinguem execução local, runner GitHub e recursos GCP; configuração isoladamente não equivale a teste aprovado.

## Resultados atuais da GCP

| Arquivo | Origem e resultado comprovado |
| --- | --- |
| `terraform-bootstrap-plan.json` | Plano prévio de 27 criações revisado; conta de faturamento redigida |
| `bootstrap-validation.json` | Bootstrap real aplicado, projeto/número/filtro, identidades, OIDC e buckets no momento inicial |
| `security-final.json` | Leitura final de contas/keys, buckets e OIDC; orçamento lido da Billing Budgets API com filtro projects/271680307280 |
| `terraform-main-reviewed-plan.json` | Plano revisado antes de concluir as duas VMs |
| `terraform-main-plan.json` | Replanejamento posterior: nove no-op, sem mudanças a aplicar |
| `plan-guard.json` | Dois planos reais aceitos e dez mutações fora do escopo recusadas |
| `github-cloud-runs.json` | IDs, links, commits, etapas e conclusões reais; sucessos e falhas preservados |
| `deploy-context.json`, `gcp-idempotence.json` | Run 45618276777: segunda execução completa site.yml; dois hosts changed=0/failed=0/unreachable=0 |
| `gcp-smoke.json` | Mesmo run: DuckDNS HTTPS, CRUD completo e100GET/10 simultâneos, zero erros, p95≈381ms |
| `runtime-acceptance-context.json`, `gcp-runtime-45644032806.json` | Onze verificações GCP aprovadas: isolamento, privilégio Mongo, restart/recreate, imagens/rollback e outage. **Arquivo mantém passed=false**, pois backup posterior falhou |
| `gcp-backup-diagnosis.json` | Journal do serviço: sonda Mongo com prazo 2000ms falhou; diagnóstico não confirmou OOM |
| `gcp-operations-idempotence.json` | Controlador Linux externo ao GitHub/VMs GCP: playbook operacional atualizado duas vezes, zero alterações na segunda |
| `gcp-owner-backup.json` | Serviço systemd na VM DB: dump, validação isolada e upload privado GCS aprovados |
| `gcp-manual-restore.json` | Mesma fase: comando cloud.py restore real, download de archive/manifest, checksum, mongorestore isolado e hash igual; produção preservada |
| `gcp-backup-schedule.json` | Timer ativo/Persistent e serviço success/0. Não foi aguardado o próximo disparo diário |
| `vm-cycle-backup-hash.json` | Fonte: backup GCP após reativação. Conferência: Mongo **local** isolado sem rede; quatro documentos e hash completo iguais ao anterior ao ciclo |
| `reactivation-context.json`, `gcp-reactivation-start.json`, `gcp-reactivation-dns.json`, `reactivation-smoke.json` | Workflow start 45657904915 aprovado: OIDC, VMs existentes, atualização automática DuckDNS para IP atual, certificado reaproveitado e CRUD HTTPS |
| `gcp-vm-cycle.json` | Controlador Linux externo ao GitHub: hash completo pela API pública após reativação igual ao anterior ao desligamento |
| `gcp-certificate-renewal.json` | Certbot na VM: dry-run do certificado triodelicia.duckdns.org aprovado |
| `gcp-browser.json`, `gcp-interface.jpg` | Navegador real no DuckDNS: cadastrar/listar/concluir/reabrir/excluir e reload; captura da tarefa concluída antes da limpeza. Somente duas tarefas fictícias próprias foram removidas |
| `gcp-final-backup.json` | Backup após limpeza da interface, validado por restore isolado antes do upload; objeto165326Z |
| `gcp-final-validation.json` | Consolida somente a última janela: ciclo, certificado, navegador e backup; não altera conclusões de runs antigos |
| `gcp-final-stop.json`, `owner-final-controller.json` | Duas camadas de parada explícita/consulta CLI, ambas TERMINATED |
| `cloud-final.json` | Inventário final com horário UTC, duas VMs, três discos, objetos/versionamentos e ausência dos recursos adicionais consultados |
| `cost-estimate.json` | Estimativa por janelas reais de operação/discos e reservas. billing_actual:null: **não é fatura** |

Backup/restore das16:08–16:27UTC e testes finais após o start aprovado foram orquestrados por controlador Linux local com credencial temporária da conta administradora. Os comandos operaram nas VMs GCP, sem chaves JSON ou novos grants. Esses arquivos declaram `orchestrator` e `source_commit`; não são apresentados como jobs de restore/acceptance bem-sucedidos no GitHub. A autenticação OIDC foi comprovada separadamente pelos workflows.

`cloud-start.json`, `cloud-backup.json`, `cloud-restore.json` e `cloud-status.json` são snapshots operacionais do horário em que o comando os gravou, sem timestamp próprio. `cloud-stop.json` recebe o estado da última parada do controlador; para origem/horário use os arquivos contextuais e o inventário final. Um snapshot RUNNING antigo não contradiz um inventário posterior TERMINATED.

## Falhas e checkpoints preservados

| Arquivo | Interpretação |
| --- | --- |
| `gcp-owner-dns.json`, `gcp-owner-recovery.json`, `gcp-owner-stop.json`, `owner-controller-final.json` | Fase anterior: backup/restore passaram, DNS ainda apontava para IP antigo; resultado global false e parada real. DNS/certificado/navegador foram comprovados **depois**, sem editar essa falha |
| `github-dispatch-failures.json` | HTTP 500/502 observados ao criar runs; não houve run nesses erros nem causa/indisponibilidade oficial comprovada. Dispatch voltou a funcionar posteriormente |
| `start-failure-45656567842.json` | Start e DuckDNS passaram, Ansible atingiu12s aguardando sudo/IAP. Workflow falhou e parou as VMs;8ca67a4 corrigiu o prazo, start seguinte passou |
| `historico/` | Checkpoints de inventário/custos/progresso, captura de endereço anterior e relatórios de 23/11 e 25/11 anteriores à revisão editorial; não são a documentação operacional atual |

## Preparação local e registros de 23/11

`baseline.json` registra a aplicação original. `local-*.json` comprovam Docker local, não GCP. `mongo-bootstrap-recovery.json` valida a exceção localhost em Mongo isolado, sem redefinir usuário existente. `ssh-transport.json` valida pipe binário/repetição pré-SSH e recusa de erro de permissão. `rollback-readiness.json` valida espera HTTP transitória e recusa de falha permanente. `github-ci.json`, `github-integration.json` e `github-configuration.json` são históricos da preparação de 23/11; os runs atuais ficam em github-cloud-runs.json.

Os artifacts GitHub expiram em 7–14 dias. Cópias públicas sanitizadas permanecem versionadas; planos binários, estados brutos, backups binários, senhas, chaves e credenciais temporárias ficam fora do Git. O runner limpa somente resultados conhecidos no checkout descartável antes de cada execução e grava contexto do run para evitar reapresentar evidência antiga como atual.

ACE-10 depende do registro humano em `../ensaio-alunos.md`; nenhum JSON desta pasta substitui esse ensaio. A rotação do token DuckDNS exposto em captura continua sendo ação de segurança coordenada com as demais integrações, sem valor da credencial nas evidências.

## Reorganização e compatibilidade

`compatibilidade-ghcr.json` registra HEAD 200/digests dos quatro manifests históricos, sem publicar ou renomear imagens. `reorganizacao-vms.json` registra somente leituras do estado TERMINATED durante a organização do repositório. A tradução de commits está em `../historico/commits-reescritos.json`; os source_commit e URLs dos JSON anteriores continuam originais. O relatório anterior à revisão editorial foi preservado em `historico/relatorio-20261125-antes-reorganizacao.md`.

As verificações de CI posteriores à reorganização avaliam código e integração no runner, sem constituir nova implantação ou teste remoto na GCP. Os resultados correspondentes são identificados no registro da reorganização.

`reorganizacao-validacao.json` consolida integridade e compatibilidade; `reorganizacao-ci.json` preserva os dois runs posteriores na main; `github-readme.jpg` registra a apresentação renderizada. `limpeza-repositorio.json` registra o arquivamento privado de 65 itens e a preservação dos arquivos funcionais.
