# Relatório técnico de entrega

## Resultado e aceite

A aplicação foi implantada na Google Cloud Platform e os fluxos técnicos foram validados. A matriz registra **15 de 16 itens comprovados (93,75%)**, considerando seis requisitos e dez critérios com pesos iguais, sem crédito parcial. O ACE-10 permanece pendente do ensaio humano dos alunos. A rotação preventiva do token DuckDNS é uma recomendação de segurança para manutenção, separada do aceite funcional.

A URL definitiva é **https://triodelicia.duckdns.org**. As VMs permanecem desligadas fora dos períodos de utilização para reduzir custos; o acesso depende de reativação por **Operate → start**, na main. O [manual](manual-operacao.md) contém comandos e procedimentos completos.

## Responsáveis pelos acessos

A administração operacional dos três serviços é de **Pedro Henrique Alves dos Santos ([@pepepedrinho](https://github.com/pepepedrinho))**, conforme confirmação da equipe Triodelicia na preparação da entrega.

| Serviço | Responsável e acesso |
| --- | --- |
| GitHub | Pedro Henrique: proprietário do repositório e responsável pelas permissões, Actions Variables e Secrets; propriedade e acesso administrativo conferidos pela API do GitHub |
| GCP | Pedro Henrique: responsável pela conta administrativa do projeto triodelicia-mensal4-2026 e pela gestão dos acessos; os pipelines utilizam a conta de serviço limitada por OIDC |
| DuckDNS | Pedro Henrique: responsável pelo domínio triodelicia.duckdns.org e pelo acesso à conta; o token de atualização permanece protegido em GitHub Secrets |

Os demais integrantes são Lipe ([@G4rb1n](https://github.com/G4rb1n)) e Eduardo ([@Eduol4](https://github.com/Eduol4)). A participação no grupo não implica concessão automática de permissões administrativas. Senhas, tokens e chaves não integram esta documentação ou o pacote de entrega.

## Arquitetura entregue

O projeto `triodelicia-mensal4-2026` (271680307280) utiliza duas e2-micro em us-central1-a. `todo-app` hospeda Nginx/TLS, React e Express; `todo-db` hospeda MongoDB autenticado, sem IP público. Os endereços privados são 10.42.0.10 e 10.42.0.20. Três discos pd-standard de 10 GiB incluem um disco exclusivo para dados.

A comunicação com o banco ocorre pela VPC privada. SSH utiliza IAP/OS Login; MongoDB e proxy de pacotes possuem regras de origem restritas. Terraform mantém bootstrap e infraestrutura em módulos separados, com estado GCS protegido. OIDC emite credenciais temporárias para GitHub Actions. Não há LB, Cloud NAT pago, Cloud SQL, GKE ou terceira VM.

Cada VM tem `maxRunDuration=21600`, ação STOP, reinício automático desabilitado e manutenção MIGRATE para E2 padrão. O limite foi confirmado na API, sem aguardar seis horas. A parada explícita e sua conferência CLI foram realizadas separadamente.

## Validações por ambiente

| Ambiente | Resultados comprovados |
| --- | --- |
| Docker local e runner Linux | Testes backend/frontend, build, auditoria npm na data da execução, CRUD real, persistência, outage, backup/restore e rollback |
| Validações estáticas | Terraform fmt/validate, Ansible syntax/lint, actionlint, ShellCheck e testes de proteção do plano/transporte |
| VMs GCP | Configuração completa, idempotência, integração privada, usuário readWrite restrito, restart/recreate Mongo, atualização/rollback e recuperação após outage |
| HTTPS externo e navegador | Criar/listar/concluir/reabrir/excluir, recarregar e conferir persistência; certificado válido e dry-run de renovação aprovado |
| Backup GCS e recuperação | Dump, checksum, upload privado, download archive/manifest e mongorestore isolado com hash igual, sem sobrescrever produção |
| Ciclo das VMs | Mesmo hash completo dos documentos antes do stop e após reativação, conferido por backup restaurado e pela API pública |

A carga pública de 100 GET com dez conexões simultâneas teve zero erros e p95 de 381ms. É uma amostra curta, sem garantia de capacidade sustentada. A segunda execução completa do Ansible teve app ok23 e db ok24, ambos changed=0/unreachable=0/failed=0. O playbook operacional atualizado também apresentou zero alterações na segunda execução. O plano Terraform principal posterior apresentou nove no-op.

## CI/CD e rastreabilidade das execuções

| Execução | Conclusão e interpretação |
| --- | --- |
| [45582818037](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45582818037) | OIDC e plano remoto aprovados |
| [45584126255](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45584126255) | Provisionamento das duas VMs aprovado |
| [45618276777](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45618276777) | Ansible, idempotência e HTTPS/carga aprovados; execução global cancelada pelo limite antigo após falha na checagem imediata do rollback |
| [45644032806](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45644032806) | Onze verificações GCP aprovadas, incluindo troca de imagem/rollback e persistência; execução global failure por falha posterior no backup |
| [45657864624](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45657864624) | CI da correção final de negociação IAP aprovada |
| [45657904915](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45657904915) | Reativação, atualização DuckDNS, reaproveitamento TLS e smoke aprovados |

A espera de prontidão corrigiu o rollback. A conexão explícita por loopback, os prazos limitados e o lock de manutenção corrigiram o backup. Durante erros 500/502 no dispatch, backup/restore foram executados nas VMs pelo mesmo código versionado, a partir de controlador Linux externo ao GitHub e com credencial temporária da conta administradora. Essa execução é identificada separadamente e não representa um workflow GitHub aprovado. O dispatch voltou a funcionar posteriormente.

As imagens efetivamente testadas mantêm os SHAs originais `9a2747cac51ca262a0fcf2557f23da78558d9d21` e `fa626deacdc5d0fffab1b82cdfcbeb64d720a456`. A [verificação das imagens](evidencias/compatibilidade-ghcr.json) registra os manifests e digests. Os identificadores das imagens e os hashes das execuções históricas foram mantidos para rastreabilidade.

## Backup, persistência e dados preservados

O backup `todo/todo-20261125T162134Z.archive.gz` teve checksum e restauração isolada conferidos na GCP. O caminho manual de restore baixou archive/manifest do GCS e executou mongorestore real, sem promover a cópia à produção. O serviço systemd foi consultado com Result=success/ExecMainStatus=0, e o timer com ActiveState=active/Persistent=true. Não foi aguardada a próxima virada diária; VMs desligadas não produzem novas cópias.

O hash completo dos quatro documentos antes do ciclo foi `53592e65627a97acdefd3547c032eda4f1cc59450d894cb32620253bad620121`, também confirmado após reativação. No fim do teste de navegador, foram removidas somente duas tarefas descartáveis criadas para validação, preservando as três preexistentes. Após essa limpeza foi produzido o backup validado `todo/todo-20261125T165326Z.archive.gz`.

## Estado final e custos

Ao encerrar a validação técnica, **todo-app e todo-db foram confirmadas TERMINATED** pelo CLI em 25/11/2026 às 13:57:36 (Brasília, UTC−3). As [conferências posteriores por CLI](evidencias/reorganizacao-vms.json) registram o estado desligado, sem inicialização ou novo deploy. Na conferência de entrega em 27/11/2026 às 19:49:36 (Brasília, UTC−3), ambas continuavam TERMINATED. Essa conferência foi somente de leitura.

Permanecem provisionados: duas VMs, três discos (30 GiB), dois buckets privados, VPC/sub-rede, quatro firewalls próprios, três contas de serviço, papel customizado/IAM limitado, WIF, alerta de orçamento e APIs necessárias. A rede default e suas quatro regras automáticas também permanecem, sem VMs conectadas. O inventário não identificou IP reservado, router/NAT, forwarding rule, snapshot, imagem customizada ou machine image.

A estimativa registrada ao fim da implantação é **US$1,6259 (aproximadamente US$1,63)**, incluindo reservas de tráfego/operações, sem valor de fatura apurado. Discos preservados representam cerca de US$1,20/730h, além de armazenamento/versionamentos e operações GCS. O alerta BRL5 não bloqueia gastos e não equivale à meta operacional US$5. Valores, data da coleta e fontes estão em [custos](custos.md); não são atualizados como se fossem uma fatura em tempo real.

## Evidências sanitizadas preservadas

Os registros abaixo estão versionados no GitHub e continuam disponíveis independentemente da expiração dos artifacts. As execuções do Actions complementam essas evidências.

| Verificação | Registro versionado |
| --- | --- |
| Configuração completa e idempotência | [Segunda execução Ansible](evidencias/gcp-idempotence.json) |
| HTTPS, CRUD e carga curta | [Smoke público e carga](evidencias/gcp-smoke.json) |
| Interface no navegador | [CRUD no navegador](evidencias/gcp-browser.json) e [captura da interface](evidencias/gcp-interface.jpg) |
| Isolamento, persistência, atualização e rollback | [Checkpoints remotos](evidencias/gcp-runtime-45644032806.json), preservando a falha global posterior do backup |
| Backup GCS e restore manual isolado | [Backup validado](evidencias/gcp-owner-backup.json) e [restauração real](evidencias/gcp-manual-restore.json) |
| Certificado e ciclo das VMs | [Renovação simulada](evidencias/gcp-certificate-renewal.json) e [hash após reativação](evidencias/gcp-vm-cycle.json) |
| Recursos preservados e estimativa | [Inventário](evidencias/cloud-final.json) e [cálculo de custos](evidencias/cost-estimate.json) |

## Limites e pendências

- Ensaio humano ACE-10 ainda não realizado; utilizar o [formulário dos alunos](ensaio-alunos.md).
- Recomenda-se programar a rotação preventiva do token DuckDNS e a atualização das integrações da conta em uma janela de manutenção. Trata-se de recomendação de segurança, não de funcionalidade pendente; a rotação não integra esta finalização.
- Imagens distintas usadas no rollback derivam da mesma fonte funcional, com metadados/configurações diferentes; migração de schema não foi testada.
- Sem alta disponibilidade; backup/restore interrompem temporariamente o banco para caber na memória disponível.
- Lista compartilhada sem login e sem sincronização automática entre navegadores; usar apenas dados fictícios.
- A causa exata da falha transitória anterior de autenticação Mongo não foi comprovada. O diagnóstico confirmou credenciais válidas e ausência de OOM naquele momento; a sonda passou a distinguir autenticação recusada de outros erros, sem redefinir usuários.

A [matriz](matriz-aceite.md), o [índice de evidências](evidencias/README.md) e a [evolução técnica](progresso-implementacao.md) complementam este relatório. Os documentos anteriores permanecem identificados como históricos; suas falhas e resultados não foram alterados para apresentar uma conclusão global diferente.
