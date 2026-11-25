# Progresso da implementação

Atualizado em 25/11/2026. Projeto acadêmico sem evento real. Escopo exclusivo: `triodelicia-mensal4-2026`, número `271680307280`, duas e2-micro em us-central1-a, três discos Standard de 10 GiB e limite nativo de seis horas/STOP por inicialização. Não houve expansão de IAM, contratação de serviços adicionais pagos ou destruição da infraestrutura.

## Resultados comprovados

| Etapa | Resultado real | Evidência |
| --- | --- | --- |
| Aplicação local e CI | React/Express/Mongo reais, CRUD, persistência, outage, backup/restore e rollback passaram | `local-*.json`, `github-ci.json` histórico e runs atuais |
| Bootstrap | Plano de 27 criações revisado; número/filtro do orçamento conferidos antes do apply; estado migrado ao GCS | `bootstrap-validation.json`, plano bootstrap |
| Infraestrutura | Nove recursos principais; duas VMs, banco sem IP público; 21600/STOP/sem restart confirmados pela API | Planos revisados, run 45584126255, inventários |
| Proteção do plano | Planos reais aceitos; dez alterações proibidas rejeitadas, incluindo disco extra, região indevida, SSH público e duração excessiva | `plan-guard.json` |
| Mongo administrativo | Verificações administrativas confirmaram credencial montada e autenticação nos dois testes; nova sonda distingue rejeição explícita de erro transitório, com timeout e no_log | Commit 6d68cd3 e Ansible remoto aprovado |
| Ansible completo | Segunda execução: todo-app changed=0/failed=0/unreachable=0; todo-db changed=0/failed=0/unreachable=0 | `gcp-idempotence.json`, run 45618276777 |
| DuckDNS e HTTPS | Domínio definitivo configurado, DNS atualizado; certificado válido e CRUD público completos | `gcp-smoke.json`, `deploy-context.json` |
| Carga GCP | 100 leituras, 10 simultâneas, zero erros, p95 de 381ms; amostra curta, sem garantia de capacidade sustentada | `gcp-smoke.json` |
| Correção do rollback | HTTP real: indisponibilidade transitória aguardada e falha permanente recusada; atualização e rollback de imagens distintas passaram na GCP | `rollback-readiness.json`, `gcp-runtime-45644032806.json` |
| Backup após boot | Mongo inicialmente parado foi iniciado; dump, validação isolada e upload privado passaram na GCP | `local-backup-autostart.json`, `gcp-owner-backup.json` |
| Restore manual real | Download de archive/manifest GCS, checksum e mongorestore em volume isolado; hash igual e produção preservada | `gcp-manual-restore.json` |
| Ciclo das VMs | Backup produzido na GCP após reativação foi restaurado em Mongo local sem rede; hash completo dos quatro documentos igual ao anterior ao desligamento | `vm-cycle-backup-hash.json`; execução da conferência local identificada no arquivo |
| Segurança final | Três SAs sem chaves de usuário; orçamento BRL 5 lido da API com filtro projects/271680307280 | `security-final.json` |

Os arquivos JSON citados ficam em `docs/evidencias/`. Os checkpoints anteriores, inclusive a captura sslip.io, foram preservados em `docs/evidencias/historico/`.

## Histórico das correções

| Execução / situação | Causa observada e tratamento |
| --- | --- |
| Preparação de 23/11 | Aplicação adaptada, testes locais e CI/GHCR passaram; pré-requisitos do bootstrap foram preparados antes do provisionamento |
| 45583605439 | E2 padrão recusou manutenção TERMINATE; corrigido para MIGRATE, preservando 21600/STOP |
| 45584309429 | SSH/scp do SDK funcionavam; SSH direto do Ansible não usava o certificado federado. Transporte passou a delegar ao gcloud |
| 45585407780 | Credencial federada inicial expirou; jobs passaram a obter access token de 3600s, sem novos grants |
| 45588264540 | Inicialização Mongo excedeu 120s; sonda TCP leve, prazo 300s e parada graciosa 60s. Diagnóstico 45593069785 passou e encerrou as VMs |
| 45594899799 | Primeira inicialização interrompida havia deixado dados sem administrador; recuperação pela exceção localhost, sem apagar volume ou redefinir usuário existente |
| 45599197611 | Primeiro HTTPS funcionou; segunda execução falhou por conflito transitório de mutação OS Login. Repetição limitada anterior à conexão foi testada com pipe binário real |
| 45603866409 | A sonda administrativa inesperadamente falhou e acionou recuperação indevida. O diagnóstico confirmou administrador/credenciais funcionais e ausência de OOM; causa transitória exata não foi comprovada. Commit 6d68cd3 separou autenticação recusada de outros erros |
| 45612036397 | Secret DuckDNS vazio. O secret foi recadastrado com entrada segura; commit 0d4aa22 valida presença antes de ligar VMs |
| 45618276777 | Ansible completo, idempotência e HTTPS/carga passaram. Teste falhou na checagem HTTP imediata do rollback; execução acabou cancelada pelo limite antigo. Ambas VMs foram confirmadas TERMINATED pelo CLI após o encerramento |
| Recuperação operacional | Commit 475c4be aguarda prontidão no rollback, inicia Mongo antes do backup e adiciona Operate acceptance. Commit 02d7f1a separa a aceitação extensa e reserva tempo para parar as VMs; CI 45643716835 passou |
| 45644032806 | Onze verificações remotas passaram, incluindo isolamento, readWrite, persistência, imagens/rollback e outage. Backup falhou com MongoServerSelectionError em sonda de 2000ms; arquivo mantém passed=false. Diagnóstico não confirmou OOM |
| 1c14dde / 9aac06b | Backup/restore passaram a usar loopback explícito, sondas limitadas e lock compartilhado de manutenção. Operação recovery permite retomar somente verificações pendentes; CIs 45649345254 e 45649966499 passaram |
| Dispatch HTTP 500/502 | Operate e Infrastructure falharam ao criar runs; nenhuma causa externa foi comprovada. Posteriormente o dispatch validate 45656491227 foi aceito e passou; não se atribui o erro ao novo input ou a incidente oficial |
| Controlador Linux externo ao GitHub 16:08–16:27 UTC | Mesmo código versionado executou backup GCS e restore manual reais, com credencial temporária, sem grants novos. DNS apontava para IP anterior, portanto certificado/interface não foram declarados aprovados nessa etapa. Duas VMs TERMINATED ao final |

Os commits 6d68cd3, 79c7507 e 0d4aa22 consolidaram a correção da sonda administrativa e a integração DuckDNS. O domínio definitivo passou a ser `triodelicia.duckdns.org`; endereços anteriores permanecem somente no histórico. Os hashes desta cronologia são os originais usados nos testes; a correspondência após tradução está em [commits reescritos](historico/commits-reescritos.json).

## Consolidação da entrega

O backup/restore pendente do run 45644032806 foi corrigido e executado nas VMs GCP pelo controlador Linux externo ao GitHub, preservando a conclusão failure do run original. O timer foi consultado ativo, com serviço concluído em sucesso; não foi aguardada uma nova virada diária. O hash completo após um ciclo das VMs foi conferido primeiro pelo backup restaurado localmente e depois pela API pública, sem diferença.

Após os erros 500/502, o dispatch voltou a funcionar. A tentativa start 45656567842 atualizou DNS, mas falhou no Gathering Facts com timeout 12s de escalonamento sudo. As VMs foram paradas. Commit 8ca67a4 ampliou somente o prazo de transporte para 60s; validação/lint locais e CI 45657864624 passaram. **Start 45657904915 passou**, atualizou DuckDNS para o novo IP, reaproveitou o certificado e aprovou o smoke.

Na última janela, o dry-run Certbot do domínio definitivo e o CRUD completo no navegador passaram. As três tarefas preexistentes foram preservadas; somente duas tarefas fictícias criadas nestes testes foram removidas. O controlador produziu backup final após a limpeza, saiu com código 0 e confirmou ambas TERMINATED pelo CLI em 25/11/2026 às 13:57:36 (Brasília, UTC−3). O inventário final, os horários e os custos consolidados estão no relatório e nos JSON correspondentes; os estados RUNNING em checkpoints antigos não representam o encerramento.

**Aceite: 15/16 itens (93,75%)** pelo critério de pesos iguais da matriz. A rotação do token DuckDNS exposto em captura depende da atualização coordenada das integrações da conta. O ensaio ACE-10 exige participação dos alunos e tem formulário próprio. Essas pendências permanecem abertas na entrega. Não foi executado destroy.

## Organização acadêmica do repositório

As branches cumulativas preservam a base do professor e os marcos reais da implementação. As mensagens dos 30 commits próprios foram traduzidas sem modificar suas árvores, autoria ou datas. A main e 05-entrega-final consolidam a entrega; novas referências operacionais usam main. Os registros e hashes de testes anteriores permanecem inalterados. Consulte [reorganização do repositório](reorganizacao-repositorio.md).
