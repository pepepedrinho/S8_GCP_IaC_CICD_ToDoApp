# Registro do ensaio acadêmico — ACE-10

**Estado: não realizado por participantes humanos.** Preencher durante o ensaio; não assinar com base apenas nos testes automatizados. O projeto não tem evento real agendado.

Participantes: ____________________  Data/hora: ____________________

Repositório: `pepepedrinho/S8_GCP_IaC_CICD_ToDoApp`, branch `feat/infra-terraform-ansible-actions`. Somente o projeto GCP `triodelicia-mensal4-2026`.

| Etapa conduzida pelos alunos | Resultado / evidência |
| --- | --- |
| Executar Operate → start, aguardar sucesso e conferir atualização DuckDNS | A preencher |
| Abrir https://triodelicia.duckdns.org em outro dispositivo, cadastrar uma tarefa fictícia e recarregar | A preencher |
| Concluir, recarregar, reabrir, recarregar e excluir somente a tarefa do ensaio | A preencher |
| Explicar a lista compartilhada, sem login, e preparar intencionalmente dados fictícios para o professor | A preencher |
| Executar Operate → health e logs; explicar ready503/live200 quando o banco está indisponível | A preencher |
| Explicar reinício dos serviços, disco dedicado e diferença entre stop e destroy | A preencher |
| Executar Operate → backup e identificar o objeto; executar restore com esse objeto e conferir hash/produção preservada | A preencher |
| Explicar versão por SHA, rollback e ausência de teste de migração de schema | A preencher |
| Executar Operate → stop, confirmar ambas TERMINATED e explicar custos residuais | A preencher |

Para acionar pela CLI, use `gh workflow run operate.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref feat/infra-terraform-ansible-actions -f operation=start`. Troque a operação conforme a etapa. Para restore acrescente `-f backup_object=todo/todo-YYYYMMDDTHHMMSSZ.archive.gz` com o nome real emitido pelo backup, nunca o exemplo literal. Acompanhe o run até terminar.

As rotinas backup/restore interrompem o Mongo principal temporariamente para caber na e2-micro; a API pode ficar indisponível durante a manutenção. O restore usa outro volume e não promove a cópia à produção. Evite executar outra operação simultânea. O manual contém diagnóstico, recuperação e comandos completos.

Dúvidas e correções necessárias: ________________________________________

Conclusão dos participantes / professor: ________________________________

Nunca incluir senhas, token DuckDNS, chave SSH ou estado Terraform neste registro. Ao terminar, preservar discos e backups; não executar destroy nesta entrega.
