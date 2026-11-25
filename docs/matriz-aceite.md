# Matriz de requisitos e aceite

Referência: escopo.pdf e docs/escopo.md. Atualização: 25/11/2026. Projeto acadêmico sem evento real. Os testes locais e os testes GCP são identificados separadamente. Uma falha posterior não apaga as verificações anteriores registradas em checkpoint; também não torna a execução inteira aprovada.

| ID | Implementação / arquivos | Resultado e evidência observados | Estado / pendência |
| --- | --- | --- | --- |
| REQ-01 — Duas VMs, banco exclusivo | Terraform main, cloud.py | Duas e2-micro us-central1-a, banco separado, três discos Standard total 30 GiB; provisionamento 45584126255 | Validado GCP; conferir inventário cloud-final.json e horário da última parada |
| REQ-02 — Mongo privado | Terraform VPC/firewalls, Compose database_host | DB sem IP público; portas públicas 22/27017/3128 indisponíveis; app conecta 10.42.0.20 | Validado GCP: gcp-runtime-45644032806.json |
| REQ-03 — Administração e segredos | IAM limitado, WIF, OS Login/IAP, secret files | OIDC real; três SAs sem chaves de usuário na conferência final; papel Mongo somente readWrite em todo-app confirmado remotamente | Controles do professor validados; token DuckDNS exposto em captura requer rotação e atualização das integrações |
| REQ-04 — Persistência e backup | Disco dedicado, backup.sh, restore-isolated.sh, gcs.py | Restart/recreate/update preservam tarefa+estado na GCP; serviço corrigido produziu backup privado validado e restore isolado real | Validado GCP: gcp-owner-backup.json e gcp-manual-restore.json |
| REQ-05 — Mesmo endereço HTTPS | Fetch relativo, Nginx/TLS, DuckDNS, Certbot | https://triodelicia.duckdns.org com certificado válido; frontend e CRUD pela mesma origem | Validado GCP: gcp-smoke.json, gcp-certificate-renewal.json e start 45657904915 |
| REQ-06 — Saúde e diagnóstico | Restart unless-stopped, healthchecks, operate.yml | ready503/live200 com Mongo parado; recuperação e limites de memória observados; diagnóstico por IAP | Validado GCP; persistência no ciclo também conferida pelo backup GCP em vm-cycle-backup-hash.json (verificação em Mongo local isolado) |
| ACE-01 — Reprodução por código | Terraform, Ansible, CI, manual | Infra criada por pipeline; Ansible completo e segunda execução real sem alterações | Validado: planos, github-cloud-runs.json e gcp-idempotence.json |
| ACE-02 — Duas VMs | Terraform outputs/inventário | todo-app e todo-db e2-micro com os IPs privados previstos, sem terceira VM criada | Validado GCP: cloud-final.json |
| ACE-03 — Isolamento | VPC/firewalls, IAP, DB sem IP público | Teste externo negativo 22/27017/3128 e conexão privada 27017 passaram | Validado GCP: gcp-runtime-45644032806.json |
| ACE-04 — CRUD externo HTTPS | smoke.py, React e Nginx | CRUD/reload completos via cliente externo e interface real; carga 100/10 zero erros, p95 381ms | Validado GCP e navegador externo: gcp-browser.json e gcp-interface.jpg |
| ACE-05 — Persistência em três cenários | Disco, Compose, deploy-images.sh | Restart, recriação Mongo e atualização entre imagens distintas preservaram tarefa e completed | Validado GCP: gcp-runtime-45644032806.json |
| ACE-06 — CI/CD e rollback | Workflows, GHCR SHA, deploy transacional | CI passou; imagens publicadas/transferidas; troca real de imagem e rollback corrigido passaram na GCP | Validado por etapas/runs; não declarar o run de backup falho como sucesso global |
| ACE-07 — Backup e restore | systemd timer/service, GCS privado e volume isolado | Serviço systemd corrigido, upload GCS, download archive/manifest, checksum e mongorestore remoto isolado passaram; produção preservada | Validado GCP: gcp-manual-restore.json e gcp-backup-schedule.json; não foi aguardada virada diária do timer |
| ACE-08 — Operação segura | Operate start/stop/diagnose, manual, destroy preparado | Start/DNS/HTTPS passaram; várias paradas conferidas pelo CLI; destruição fora da rotina de encerramento | Validado: ciclo, restore manual e parada final CLI; ambas TERMINATED em cloud-final.json |
| ACE-09 — Custos e resíduos | custos.md, final-inventory.py, guard 21600/STOP, alerta BRL 5 | Tarifas/fontes e recursos residuais documentados; estimativa com reservas, sem alegar valor de fatura | Validado: inventário final sem extras e US$1,6259 estimados com reservas; fatura não apurada |
| ACE-10 — Transferência aos alunos | Roteiro no manual e formulário ensaio-alunos.md | Nenhum ensaio humano registrado | Pendente alunos; teste automatizado não substitui a demonstração |

Os caminhos JSON são relativos a docs/evidencias/. gcp-runtime-45644032806.json conserva passed=false porque o teste completo falhou no backup, após registrar onze verificações aprovadas. O relatório combina essas evidências com os resultados da recuperação, sem reclassificar a execução original.

As imagens de comparação contêm a mesma fonte funcional da aplicação com metadados/configurações distintos. Foram comprovadas troca de ID de imagem, restauração da versão e preservação dos dados; migração de schema não foi testada. O limite de seis horas foi verificado na API Compute, sem aguardar seis horas de execução como teste.

Contagem de aceite após as validações técnicas: **15/16 itens = 93,75%**, seis REQ e nove ACE, com pesos iguais e sem crédito parcial. ACE-10 requer demonstração humana. A rotação do token DuckDNS potencialmente exposto permanece uma ação de segurança pendente, explicitamente separada da implementação dos controles REQ-03. O aceite permanece em 93,75% até a conclusão do ensaio; a pendência de segurança também permanece registrada.
