# Manual de implantação e operação

Projeto permitido: `triodelicia-mensal4-2026`. Repositório: `pepepedrinho/S8_GCP_IaC_CICD_ToDoApp`. Branch: `feat/infra-terraform-ansible-actions`. Nenhum procedimento usa projetos antigos. Os passos de nuvem estão implementados, mas ainda não foram executados; consulte o progresso antes de utilizá-los.

## Preparação única

1. Aprovar o escopo exato de IAM/OIDC descrito em `seguranca-bootstrap.md`. O faturamento já foi vinculado, mas a autorização automática rejeitou o bootstrap; não contorne esse bloqueio.
2. Com sessão `gcloud` do proprietário, gerar e revisar `python scripts/terraform-plan.py bootstrap`. Evidência pública sanitizada: `evidencias/terraform-bootstrap-plan.json`. O plano binário, logs e estados locais ficam ignorados pelo Git.
3. Depois da autorização, executar `python scripts/bootstrap.py`. Cria buckets antes de migrar o estado, separando prefixos `todo/bootstrap` e `todo/main`. Não cria VMs. Preservar a cópia de estado em local seguro; uma recuperação do estado deve partir da geração correta do objeto GCS, sem executar dois operadores simultaneamente.
4. Cadastrar no fork as variáveis Actions `GCP_WIF_PROVIDER` e `GCP_SERVICE_ACCOUNT` com os outputs do bootstrap. Cadastrar secrets `MONGO_ROOT_PASSWORD` e `MONGO_APP_PASSWORD` com senhas aleatórias distintas de pelo menos 24 caracteres. As senhas precisam permanecer as mesmas em deploys posteriores; alterar um arquivo de secret não altera usuários já existentes no Mongo. Rotação exige procedimento autenticado no banco.
5. Confirmar que os workflows estão disponíveis para `workflow_dispatch`. O GitHub exige o arquivo na branch padrão para oferecer o acionamento manual; a implementação preserva `main` como referência original. A integração/revisão da branch para habilitar o fluxo padrão é uma pendência da entrega, sem merge automático. `--ref feat/infra-terraform-ansible-actions` seleciona a revisão depois que o workflow estiver disponível.

Não crie chaves JSON de conta de serviço. OIDC emite credenciais temporárias apenas ao repositório/owner numéricos e às branches autorizadas. A conta de automação não administra IAM, billing, APIs nem buckets. O bootstrap permanece uma operação do proprietário.

## Provisionar e implantar

Na aba Actions do fork, selecione a branch de implementação nos acionamentos que já estiverem habilitados:

1. **Validate** deve passar; confirme a publicação das duas imagens GHCR para o SHA completo desejado. PRs só validam e não publicam imagens.
2. **Infrastructure**, `action=plan`: confira exatamente duas `e2-micro`, três discos `pd-standard` de 10 GiB, um IP efêmero e os quatro firewalls previstos. A allowlist rejeita recursos adicionais e exclusões no fluxo normal.
3. **Infrastructure**, `action=apply`, `confirmation=PROVISION`: cria as VMs. O status produzido precisa confirmar `STOP`, máximo 21600 segundos, sem reinício automático e sem IP público no banco.
4. Execute imediatamente **Configure and deploy** com o SHA de imagem já publicado. O runner autentica no GHCR, transfere as imagens por IAP e não copia a credencial do registry para as VMs. Ansible prepara aplicação, relay de pacotes, Mongo privado, disco, backups e HTTPS.
5. O deploy executa CRUD público, carga curta de 100 leituras/10 conexões, backup e restauração isolada. O passo final tenta parar as duas VMs mesmo em falha e comprovar `TERMINATED`. Baixe os artifacts de evidência: expiram após 7–14 dias no GitHub.

Um apply bem-sucedido sozinho deixa as VMs em execução para configuração. Se o deploy não puder seguir, execute **Operate → stop**. O limite de seis horas é proteção de emergência. Nenhum teste deve deixar as VMs rodando ao fim da sessão autônoma.

Ansible deve ser reexecutado com os mesmos parâmetros para medir idempotência; registrar recap e investigar mudanças inesperadas. Lint não comprova idempotência nem funcionamento remoto.

## Reativar para apresentar

Execute **Operate**, `operation=start`. O fluxo liga o banco e a aplicação, prepara SSH temporário, sobe primeiro Mongo com `--wait`, depois os contêineres da aplicação, atualiza Nginx/certificado para o hostname do IP atual e testa HTTPS/CRUD. A URL aparece no resumo do job. Uma falha de reativação aciona desligamento.

DNS escolhido: `todo-<IP-com-hifens>.sslip.io`. Não exige token nem altera `triodelicia.duckdns.org`. O IP efêmero pode mudar a cada parada, portanto a URL anterior pode deixar de funcionar. A renovação Certbot usa HTTP-01 na porta 80 e hook de reload do Nginx. DNS compartilhado, limites de emissão, filtros de rebinding e disponibilidade do serviço externo podem impedir emissão; não relaxar a validação TLS para produzir resultado positivo. O endereço só será anunciado depois de validado publicamente.

O fluxo `start` deixa o ambiente disponível por até seis horas para a demonstração. Ao terminar, execute **Operate → stop** e confira os dois estados `TERMINATED`. Discos e backups permanecem. Não existe reinício periódico.

## Saúde, logs e falhas

- **Operate → health**: inventário e smoke público. `/health/live` confirma o processo; `/health/ready` exige ping autenticado no Mongo e retorna 503 se falhar. Um resultado 200 apenas na página não comprova o banco.
- **Operate → logs**: status dos contêineres e últimas execuções do serviço de backup. Para investigação adicional, usar IAP/OS Login e `sudo docker compose ... logs --tail 100`, sem copiar arquivos de credenciais para evidências. Os logs do backend não incluem URI/senha.
- API 503: conferir Mongo saudável, credencial persistida, IP privado e firewall 27017. Não publicar a porta para diagnosticar.
- Imagem nova falhou: script restaura `release.previous.env` e retorna erro. **Operate → rollback** aplica a versão anterior já existente no host e valida saúde. Preservar duas versões; não executar prune indiscriminado.
- Certificado falhou após novo IP: conferir resolução pública, HTTP-01 e logs Certbot; manter VMs desligadas enquanto o impedimento externo não puder ser resolvido.
- Falta de memória: coletar `free`, `docker stats --no-stream` e OOMs do kernel. Otimizar primeiro. Não aumentar a máquina sem estimativa e autorização.

## Backup e restauração

O timer `todo-backup.timer` agenda diariamente às 03:00 no relógio UTC da VM, `Persistent=true`: execução perdida é retomada quando o host volta. Hosts desligados não produzem backup novo. **Operate → backup** executa a mesma rotina imediatamente.

O backup bloqueia gravações por pouco tempo para obter snapshot consistente, faz dump autenticado sem senha nos argumentos e desbloqueia. A validação isolada interrompe temporariamente o Mongo principal, evitando dois working sets simultâneos em 1 GiB de RAM. A API pode retornar 503 durante essa manutenção. Um volume temporário, sem rede, recebe a restauração. Compara-se SHA-256 dos documentos ordenados e do arquivo; o banco principal nunca é sobrescrito. O `trap` remove somente recursos temporários com prefixo próprio e reinicia o Mongo principal.

Somente depois de validar, arquivo e manifest vão para GCS privado. Retenção mínima de sete dias no bucket, lifecycle e limpeza local limitada a backups antigos previamente validados após um novo sucesso. Lifecycle não garante remoção no segundo exato. O timer/armazenamento GCS ainda precisam ser comprovados remotamente.

Para conferir uma cópia remota, execute **Operate → restore**, `backup_object=todo/todo-YYYYMMDDTHHMMSSZ.archive.gz`. O nome é validado, os dois objetos são baixados, checksum é conferido e a restauração isolada é repetida. Essa operação **não promove dados à produção**. Uma recuperação real que substitua a demonstração requer backup do estado atual e decisão explícita de qual cópia recuperar.

## Preparar a lista da demonstração

A lista é pública e compartilhada. Use apenas dados fictícios. Pela interface, remova intencionalmente tarefas de demonstrações anteriores e cadastre os exemplos desejados; confirme em outro navegador. Não confundir essa limpeza com remoção de volumes ou destruição de infraestrutura. O script de inicialização não reinsere tarefas em um volume já inicializado.

## Encerramento definitivo

Não foi executado nesta entrega. **Decommission infrastructure** exige `DESTROY-TODO`, liga o ambiente se necessário, cria e valida backup final e só então aplica o plano de destruição principal. Se o backup falhar, não deve destruir; o caminho de falha tenta parar as VMs.

Terraform principal remove VMs, discos e rede; os buckets/IAM/OIDC do bootstrap ficam preservados separadamente. Confira inventários de instâncias, discos e endereços e os objetos retidos. Estado versionado e backups podem continuar gerando cobrança. A remoção final do bootstrap é uma operação distinta do proprietário, após recuperar e exportar os dados desejados; não remova buckets/estado para resolver erros de lock. Não apague projetos, organizações ou conta de faturamento por esse fluxo.

## Ensaio pelos alunos

Após a nuvem estar validada, cada responsável deve executar start, abrir a URL em outro dispositivo, cadastrar/concluir/reabrir/excluir, conferir persistência, consultar saúde/logs, explicar o restore isolado e encerrar com stop. Registrar participante, data, resultado e dúvidas. A documentação e os testes automatizados não substituem esse ACE-10.
