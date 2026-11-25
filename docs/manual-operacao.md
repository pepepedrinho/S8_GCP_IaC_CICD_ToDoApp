# Manual de implantação e operação

Projeto permitido: `triodelicia-mensal4-2026`, número `271680307280`. Repositório: `pepepedrinho/S8_GCP_IaC_CICD_ToDoApp`. Branch: `feat/infra-terraform-ansible-actions`. Bootstrap e infraestrutura aplicados em 25/11/2026 após autorização explícita. Consulte o relatório e as evidências para o resultado dos testes.

## Preparação única

1. O escopo exato de IAM/OIDC descrito em `seguranca-bootstrap.md` foi autorizado pelo usuário em 25/11/2026. Não ampliá-lo sem nova autorização. O faturamento já estava vinculado e não foi alterado nesta aplicação.
2. Com sessão `gcloud` do proprietário, gerar e revisar `python scripts/terraform-plan.py bootstrap`. Evidência pública sanitizada: `evidencias/terraform-bootstrap-plan.json`. O plano binário, logs e estados locais ficam ignorados pelo Git.
3. Depois da autorização, executar `python scripts/bootstrap.py`. Cria buckets antes de migrar o estado, separando prefixos `todo/bootstrap` e `todo/main`. Não cria VMs. Preservar a cópia de estado em local seguro; uma recuperação do estado deve partir da geração correta do objeto GCS, sem executar dois operadores simultaneamente.
4. As variáveis Actions `GCP_WIF_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `DUCKDNS_DOMAIN=triodelicia.duckdns.org` e os secrets `MONGO_ROOT_PASSWORD`, `MONGO_APP_PASSWORD` e `DUCKDNS_TOKEN` estão cadastrados no fork. As identidades GCP foram criadas. O token DuckDNS deve estar preenchido antes de iniciar as VMs; ele é usado somente no runner para atualizar o domínio. O script `python scripts/configure-github.py` reproduz a configuração sem sobrescrever secrets existentes; usa valores aleatórios de 48 caracteres e cópia privada em `.local/cloud-secrets.json`, ignorada pelo Git. Conferir os outputs do bootstrap. As senhas precisam permanecer as mesmas em deploys posteriores; alterar um arquivo de secret não altera usuários já existentes no Mongo. Rotação exige procedimento autenticado no banco.
5. Os workflows são registrados pelo push inicial. Segundo a [documentação GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch), depois de registrado por uma execução, um workflow pode ser acionado por CLI/API em outra branch. O botão da interface exige o arquivo na branch padrão; `main` continua preservada. Use os comandos abaixo com a branch explícita. Antes de qualquer provisionamento, valide o dispatch sem GCP: `gh workflow run infra.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref feat/infra-terraform-ansible-actions -f action=validate`. Esse modo só valida código; não autentica na GCP nem cria recursos.

Não crie chaves JSON de conta de serviço. OIDC emite credenciais temporárias apenas ao repositório/owner numéricos e às branches autorizadas. Os jobs solicitam access token de uma hora, dentro da permissão existente `workloadIdentityUser`; não há `TokenCreator` adicional. A conta de automação não administra IAM, billing, APIs nem buckets. O bootstrap permanece uma operação do proprietário.

O estado de bootstrap já foi migrado ao GCS. Não reaplique um estado local antigo. O modo `python scripts/bootstrap.py --migrate-only` corrige exclusivamente uma migração interrompida; não substitui a revisão de um novo plano. Ansible usa `infra/ansible/gcloud-ssh.py` e transferência `piped`, permitindo que o SDK renove os certificados OS Login da identidade federada a cada conexão.

## Provisionar e implantar

Na aba Actions do fork, selecione a branch de implementação nos acionamentos que já estiverem habilitados:

Se o botão não aparecer enquanto `main` permanece original, use a CLI autenticada. Exemplo de plano: `gh workflow run infra.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref feat/infra-terraform-ansible-actions -f action=plan`. Exemplo de parada: `gh workflow run operate.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref feat/infra-terraform-ansible-actions -f operation=stop`.

1. **Validate** deve passar; confirme a publicação das duas imagens GHCR para o SHA completo desejado. PRs só validam e não publicam imagens.
2. **Infrastructure**, `action=plan`: confira exatamente duas `e2-micro`, três discos `pd-standard` de 10 GiB, um IP efêmero e os quatro firewalls previstos. A allowlist rejeita recursos adicionais e exclusões no fluxo normal.
3. **Infrastructure**, `action=apply`, `confirmation=PROVISION`: cria as VMs. O status produzido precisa confirmar `STOP`, máximo 21600 segundos, sem reinício automático e sem IP público no banco.
4. Execute imediatamente **Configure and deploy** com o SHA de imagem já publicado. O runner autentica no GHCR, transfere as imagens por IAP e não copia a credencial do registry para as VMs. Ansible prepara aplicação, relay de pacotes, Mongo privado, disco, backups e HTTPS.
5. O deploy executa CRUD público e carga curta de 100 leituras/10 conexões. O passo final para as duas VMs, inclusive em falha, e confere `TERMINATED`. O job tem até 50 minutos, abaixo da validade de uma hora do token OIDC. Baixe os artifacts de evidência: expiram após 7–14 dias no GitHub.
6. Para a aceitação extensa, execute **Operate → acceptance**, informando `comparison_commit` com o SHA completo da segunda imagem já transferida. Esse fluxo inicia os hosts existentes, atualiza DuckDNS/HTTPS e somente os scripts operacionais; testa persistência, troca real de imagem, rollback, indisponibilidade do banco, backup GCS, download/restauração isolada e renovação do certificado. O job tem até 40 minutos e sempre encerra com parada das VMs. Não executa Terraform nem refaz a configuração completa e a idempotência já medidas.

Se os testes de persistência/rollback já passaram e a recuperação foi interrompida, **Operate → recovery** executa somente as verificações restantes de recuperação, sem exigir imagem de comparação. Confira os checkpoints do run anterior antes de escolher esse modo. Não dispare outro fluxo de nuvem enquanto uma operação estiver ativa.

Um apply bem-sucedido sozinho deixa as VMs em execução para configuração. Se o deploy não puder seguir, execute **Operate → stop**. O limite de seis horas é proteção de emergência. Nenhum teste deve deixar as VMs rodando ao fim da sessão autônoma.

A conexão Ansible permite até 60 segundos para negociação IAP/OS Login e resposta inicial de sudo. Esse ajuste corrige o timeout de transporte de 12 segundos observado na reativação 45656567842, sem relaxar autenticação ou ignorar falhas. Referência: [plugin SSH oficial](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html).

Ansible deve ser reexecutado com os mesmos parâmetros para medir idempotência; registrar recap e investigar mudanças inesperadas. Lint não comprova idempotência nem funcionamento remoto.

## Reativar para apresentar

Execute **Operate**, `operation=start`. O fluxo liga o banco e a aplicação, prepara SSH temporário, sobe primeiro Mongo com `--wait`, depois os contêineres da aplicação, atualiza o DuckDNS para o IPv4 efêmero atual, confirma a resolução DNS e testa HTTPS/CRUD. O certificado válido do mesmo domínio é reaproveitado. A URL aparece no resumo do job: **https://triodelicia.duckdns.org**. Uma falha de reativação aciona desligamento.

O domínio definitivo é `triodelicia.duckdns.org`, reutilizado por autorização explícita do usuário em 25/11/2026. O IPv4 efêmero pode mudar após a parada; `cloud.py dns` atualiza o registro pela API HTTPS do DuckDNS e aguarda a resolução para o endereço atual, preservando a URL. O token permanece no GitHub Secret e não é copiado às VMs. Certbot usa HTTP-01 na porta 80 e hook de reload do Nginx; o dry-run seleciona somente o certificado desse domínio. As referências a sslip.io nas evidências anteriores são históricas. O domínio permanece conhecido quando as VMs estão paradas, mas a aplicação fica indisponível até a reativação.

O fluxo `start` deixa o ambiente disponível por até seis horas para a demonstração. Ao terminar, execute **Operate → stop** e confira os dois estados `TERMINATED`. Discos e backups permanecem. Não existe reinício periódico.

## Saúde, logs e falhas

- **Operate → health**: inventário e smoke público. `/health/live` confirma o processo; `/health/ready` exige ping autenticado no Mongo e retorna 503 se falhar. Um resultado 200 apenas na página não comprova o banco.
- **Operate → logs**: status dos contêineres e últimas execuções do serviço de backup. Para investigação adicional, usar IAP/OS Login e `sudo docker compose ... logs --tail 100`, sem copiar arquivos de credenciais para evidências. Os logs do backend não incluem URI/senha.
- **Operate → diagnose**: liga os dois hosts existentes, coleta logs limitados, memória e indicadores OOM e os desliga novamente, inclusive em falha. Não recria infraestrutura.
- API 503: conferir Mongo saudável, credencial persistida, IP privado e firewall 27017. Não publicar a porta para diagnosticar.
- Imagem nova falhou: script restaura `release.previous.env` e retorna erro. **Operate → rollback** aplica a versão anterior já existente no host e valida saúde. Preservar duas versões; não executar prune indiscriminado.
- Certificado falhou após novo IP: conferir resolução pública, HTTP-01 e logs Certbot; manter VMs desligadas enquanto o impedimento externo não puder ser resolvido.
- Falta de memória: coletar `free`, `docker stats --no-stream` e OOMs do kernel. Otimizar primeiro. Não aumentar a máquina sem estimativa e autorização.

O healthcheck do contêiner Mongo verifica a porta do daemon final no IP interno do contêiner, sem iniciar `mongosh` a cada dez segundos; o limite de inicialização é 300 segundos. Readiness da API continua exigindo autenticação real no banco. Se uma primeira inicialização interrompida deixar arquivos sem usuários, Ansible pode criar o primeiro administrador pela [exceção localhost oficial do MongoDB](https://www.mongodb.com/docs/manual/core/localhost-exception/), com autenticação habilitada. O servidor recusa esse caminho quando já existem usuários; o procedimento não redefine senhas nem apaga dados. O usuário da aplicação permanece restrito a `readWrite` em `todo-app`.

## Backup e restauração

O timer `todo-backup.timer` agenda diariamente às 03:00 UTC, `Persistent=true`. Hosts desligados não produzem backup novo. Ao executar, o script inicia e aguarda o Mongo existente antes do dump, inclusive quando o timer é retomado após boot. O serviço é limitado a dez minutos. **Operate → backup** aciona o mesmo serviço systemd, evitando duas execuções simultâneas desse serviço.

O serviço, a inicialização operacional do Mongo e o restore compartilham o lock `/run/lock/todo-mongo-maintenance.lock`. Isso evita que um backup pendente após boot concorra com outra manutenção. As sondas administrativas usam loopback explícito, seleção de servidor de dez segundos e prazo total limitado; falha transitória não autoriza recriar usuários ou apagar dados.

O backup bloqueia gravações por pouco tempo para obter snapshot consistente, faz dump autenticado sem senha nos argumentos e desbloqueia. A validação isolada interrompe temporariamente o Mongo principal, evitando dois working sets simultâneos em 1 GiB de RAM. A API pode retornar 503 durante essa manutenção. Um volume temporário, sem rede, recebe a restauração. Compara-se SHA-256 dos documentos ordenados e do arquivo; o banco principal nunca é sobrescrito. O `trap` remove somente recursos temporários com prefixo próprio e reinicia o Mongo principal.

Somente depois de validar, arquivo e manifest vão para GCS privado. Retenção mínima de sete dias no bucket, lifecycle e limpeza local limitada a backups antigos previamente validados após um novo sucesso. Lifecycle não garante remoção no segundo exato. O relatório de aceite distingue o serviço executado, o estado do timer e a restauração realmente observada; não foi aguardada uma virada de calendário com a VM ligada.

Para conferir uma cópia remota, execute **Operate → restore**, `backup_object=todo/todo-YYYYMMDDTHHMMSSZ.archive.gz`. O nome é validado, os dois objetos são baixados, checksum é conferido e a restauração isolada é repetida. Essa operação **não promove dados à produção**. Uma recuperação real que substitua a demonstração requer backup do estado atual e decisão explícita de qual cópia recuperar.

## Preparar a lista da demonstração

A lista é pública e compartilhada. Use apenas dados fictícios. Pela interface, remova intencionalmente tarefas de demonstrações anteriores e cadastre os exemplos desejados; confirme em outro navegador. Não confundir essa limpeza com remoção de volumes ou destruição de infraestrutura. O script de inicialização não reinsere tarefas em um volume já inicializado.

## Encerramento definitivo

Não foi executado nesta entrega. **Decommission infrastructure** exige `DESTROY-TODO`, liga o ambiente se necessário, cria e valida backup final e só então aplica o plano de destruição principal. Se o backup falhar, não deve destruir; o caminho de falha tenta parar as VMs.

Terraform principal remove VMs, discos e rede; os buckets/IAM/OIDC do bootstrap ficam preservados separadamente. Confira inventários de instâncias, discos e endereços e os objetos retidos. Estado versionado e backups podem continuar gerando cobrança. A remoção final do bootstrap é uma operação distinta do proprietário, após recuperar e exportar os dados desejados; não remova buckets/estado para resolver erros de lock. Não apague projetos, organizações ou conta de faturamento por esse fluxo.

## Ensaio pelos alunos

Após a nuvem estar validada, cada responsável deve executar start, abrir a URL em outro dispositivo, cadastrar/concluir/reabrir/excluir, conferir persistência, consultar saúde/logs, explicar o restore isolado e encerrar com stop. Registrar participante, data, resultado e dúvidas. A documentação e os testes automatizados não substituem esse ACE-10.

## Rotação do token DuckDNS

O usuário informou que uma captura do diagnóstico mostrou o token. Trate a credencial como potencialmente comprometida. A rotação na conta DuckDNS e a atualização das outras integrações que usam esse token exigem participação do titular. Não publique o valor em chat, histórico de comandos, código ou evidências.

1. Identifique os clientes da conta DuckDNS que usam o token atual e escolha uma janela para atualizá-los.
2. Na conta oficial DuckDNS, faça a rotação pelo procedimento disponibilizado pelo serviço.
3. No fork, abra **Settings → Secrets and variables → Actions** e atualize o secret `DUCKDNS_TOKEN` com o novo valor, diretamente no campo protegido.
4. Atualize os demais clientes autorizados dessa conta e confirme a atualização DNS.
5. Execute **Operate → start**, confira o domínio e HTTPS e encerre com **Operate → stop**.

A rotação não é realizada automaticamente nesta entrega, pois o token pode atender outras integrações da conta. O relatório registra essa pendência sem incluir a credencial.
