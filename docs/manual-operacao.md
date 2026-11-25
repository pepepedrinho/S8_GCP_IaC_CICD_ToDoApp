# Manual de implantação e operação

Ambiente: `triodelicia-mensal4-2026` (271680307280), us-central1-a. Repositório: `pepepedrinho/S8_GCP_IaC_CICD_ToDoApp`. As operações atuais utilizam a **main**. As branches numeradas documentam marcos históricos e não devem ser usadas como referência operacional.

O bootstrap e a infraestrutura foram aplicados em 25/11/2026. Para apresentar a versão instalada, basta reativar as VMs existentes. Não é necessário executar Terraform ou repetir o deploy.

## Pré-requisitos e configuração

Para acionar os workflows, utilizar GitHub CLI autenticada ou **Actions → workflow → Run workflow → Branch: main**. A execução manual `Infrastructure → validate` verifica Terraform sem autenticar na GCP. Os fluxos de nuvem são exclusivamente manuais e compartilham o grupo de concorrência `todo-gcp-mutations`.

| Actions Variables | Actions Secrets |
| --- | --- |
| GCP_WIF_PROVIDER | MONGO_ROOT_PASSWORD |
| GCP_SERVICE_ACCOUNT | MONGO_APP_PASSWORD |
| DUCKDNS_DOMAIN=triodelicia.duckdns.org | DUCKDNS_TOKEN |

Esses parâmetros já existem no repositório. Valores de secrets não devem ser copiados para código, relatórios ou logs. O script `scripts/configure-github.py` permite preparar uma instalação nova sem sobrescrever secrets existentes. As senhas MongoDB precisam permanecer compatíveis com os usuários persistidos; alterar apenas o arquivo de senha não atualiza a credencial no banco.

OIDC emite credenciais temporárias para a conta de automação. A configuração e os limites de acesso estão em [segurança do bootstrap](seguranca-bootstrap.md). Não são necessárias chaves JSON de conta de serviço.

## Iniciar e encerrar a apresentação

```bash
gh workflow run operate.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref main -f operation=start
gh run list -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --workflow operate.yml --limit 5
```

Acompanhar o run até sucesso. O fluxo liga primeiro o banco e depois a aplicação, prepara SSH temporário, inicia explicitamente os contêineres, atualiza o DuckDNS e confirma a resolução. O certificado válido é reaproveitado e um CRUD HTTPS verifica frontend, API e MongoDB.

Acessar **https://triodelicia.duckdns.org**. O IPv4 é efêmero, mas o domínio permanece fixo. Certbot utiliza HTTP-01 na porta 80, renovação e reload do Nginx; o dry-run seleciona o certificado desse domínio.

Ao terminar:

```bash
gh workflow run operate.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref main -f operation=stop
```

Conferir `todo-app=TERMINATED` e `todo-db=TERMINATED` no resultado e no GCP CLI. O limite nativo de 21600s/STOP por inicialização é proteção adicional. Discos, backups e estado Terraform permanecem após stop; a aplicação fica indisponível. Não existe reinício periódico.

## Saúde e diagnóstico

| Operação | Comportamento |
| --- | --- |
| `health` | Consulta estado e executa smoke público; requer ambiente ligado |
| `logs` | Consulta contêineres e serviço de backup; requer ambiente ligado |
| `diagnose` | Liga as duas VMs, coleta diagnóstico limitado e volta a desligá-las |
| `rollback` | Restaura a imagem/configuração anterior já existente e valida prontidão |
| `backup` | Executa o serviço systemd de backup; requer banco ligado |
| `restore` | Baixa uma cópia GCS e executa restauração isolada; requer banco ligado |

`/health/live` confirma o processo da API. `/health/ready` executa ping autenticado no MongoDB e retorna 503 quando o banco está indisponível. Uma resposta 200 somente na página não comprova integração.

Para API 503, conferir Mongo saudável, credencial persistida, IP privado e firewall 27017. Para TLS após mudança de IP, conferir DNS e logs Certbot. Em caso de memória insuficiente, coletar `free`, `docker stats --no-stream` e OOMs antes de alterar o dimensionamento. Não publicar portas administrativas para diagnosticar.

O healthcheck Mongo usa sonda TCP leve; readiness da API continua autenticada. A inicialização tem prazo 300s. O transporte Ansible delega IAP/OS Login ao gcloud e permite 60s de negociação/resposta inicial do sudo. A repetição cobre apenas conflito transitório anterior ao SSH, sem repetir comandos arbitrários ou ignorar falhas de permissão.

Uma primeira inicialização interrompida pode ser recuperada pela [exceção localhost do MongoDB](https://www.mongodb.com/docs/manual/core/localhost-exception/) quando ainda não há usuários. Esse caminho não redefine usuários existentes, não desativa autenticação e não apaga o volume.

## Deploy e rollback

1. Confirmar CI aprovada e existência das duas imagens para o SHA desejado. PRs não publicam imagens.
2. Acionar **Configure and deploy**, na main, com `image_commit` completo. Para reutilizar a versão validada, usar `9a2747cac51ca262a0fcf2557f23da78558d9d21`.
3. Informar opcionalmente `comparison_commit=fa626deacdc5d0fffab1b82cdfcbeb64d720a456` para transferir a segunda versão de comparação.
4. Conferir Ansible, segunda execução sem alterações, HTTPS/CRUD/carga e parada final. O job tem até 50min, com token temporário de uma hora.

O runner autentica no GHCR e transfere as imagens por IAP. A credencial de registry permanece no runner. Uma implantação sem prontidão restaura a versão anterior e retorna erro. O rollback manual usa `release.previous.env` no host e também aguarda prontidão; manter duas versões e evitar prune indiscriminado.

**A tradução do histórico Git não renomeia as imagens.** Usar os SHAs originais acima, cuja existência foi reconferida em [compatibilidade GHCR](evidencias/compatibilidade-ghcr.json). A correspondência com os novos commits está em [histórico reescrito](historico/commits-reescritos.json). Não substituir um SHA de imagem pelo novo hash traduzido sem publicação comprovada.

## Backup e restauração isolada

O timer `todo-backup.timer` agenda diariamente às 03:00 UTC, com `Persistent=true`. A execução pendente pode ocorrer após boot; VMs desligadas não produzem novas cópias. O serviço inicia e aguarda o MongoDB, tem prazo de dez minutos e compartilha lock de manutenção com start/restore.

O dump autenticado bloqueia brevemente gravações, gera archive/manifest e confere hashes. A validação para temporariamente o Mongo principal para caber em 1 GiB de RAM, restaura em outro volume sem rede e reinicia o banco por trap, inclusive em falha. A API pode retornar503 durante a manutenção. Somente cópias validadas são enviadas ao bucket privado, com retenção mínima/lifecycle de sete dias. Lifecycle não garante remoção no segundo exato.

**Operate → backup** executa o serviço. Para testar uma cópia, selecionar **Operate → restore**, informando `backup_object` real no formato `todo/todo-YYYYMMDDTHHMMSSZ.archive.gz`. O fluxo baixa archive/manifest, confere checksum e executa mongorestore isolado. Não é apenas uma verificação do arquivo e não promove dados à produção.

Uma recuperação que substitua o banco principal exige procedimento separado: identificar a cópia, salvar o estado atual e planejar a promoção. O restore de verificação não sobrescreve a demonstração.

## Provisionamento e configuração a partir do código

Esta seção documenta reprodução e alterações planejadas, não a reativação cotidiana.

- `scripts/terraform-plan.py bootstrap` produz o plano do bootstrap; `scripts/bootstrap.py` cria seus recursos e migra o estado ao GCS. Não reaplicar estado local antigo sobre o backend existente.
- Bootstrap em `todo/bootstrap` e automação em `todo/main` têm acessos distintos. `--migrate-only` retoma somente uma migração interrompida.
- **Infrastructure → plan** verifica exatamente duas e2-micro, três discos de 10 GiB e os firewalls previstos. A allowlist rejeita recursos adicionais e exclusões no fluxo normal.
- **Infrastructure → apply** exige `confirmation=PROVISION`. Após provisionar, configurar imediatamente os hosts por deploy ou desligar se a configuração não puder prosseguir.
- Ansible usa `site.yml` para configuração completa e `operations.yml` para scripts operacionais. Medir idempotência com os mesmos parâmetros e investigar alterações inesperadas.
- **Operate → acceptance** utiliza uma segunda imagem já transferida e valida isolamento, persistência, rollback, outage e recuperação. **recovery** retoma somente as verificações de recuperação pendentes. Ambos têm até 40min e encerram com parada.

Nenhum push aplica Terraform ou inicia VMs. Não executar operações de nuvem simultaneamente.

## Testes locais

Com Node.js 24, executar `npm ci`, `npm test` em backend e frontend e `npm run build` no frontend. Com Docker/Compose e Python 3, usar `scripts/integration.py` e `scripts/test-release.py`; ambos utilizam o projeto `todo-implementation` por padrão. Eles exercitam Mongo real, persistência, outage e rollback. Não apresentam esses resultados como execução GCP.

Para backup local, com o Compose disponível em Bash:

```bash
export COMPOSE_PROJECT_NAME=todo-implementation
export TODO_ROOT="$PWD/.local" COMPOSE_FILE="$PWD/docker-compose.yaml" MONGO_IMAGE=todo-mongo:local
bash scripts/backup.sh
```

No Git Bash/Windows, utilizar `COMPOSE_FILE="$(pwd -W)/docker-compose.yaml"` e `MSYS_NO_PATHCONV=1`. Volumes, credenciais e backups locais são privados; manter o mesmo nome de projeto Compose para reencontrar os dados.

## Lista da demonstração e ensaio

A lista é pública e compartilhada. Preparar intencionalmente dados fictícios pela interface, sem remover volumes. A inicialização não reinsere tarefas em um banco já inicializado. O [registro ACE-10](ensaio-alunos.md) deve ser preenchido pelos participantes após demonstrarem aplicação, diagnóstico e operações essenciais.

## Encerramento definitivo

O ambiente atual está preservado. **Decommission infrastructure** exige `DESTROY-TODO`, liga as VMs se necessário e valida backup final antes de remover VMs/discos/rede. Se o backup falhar, não deve destruir. Buckets/IAM/OIDC do bootstrap permanecem em módulo separado e podem manter cobrança de armazenamento/operações. A remoção desses dados exige planejamento próprio; não apagar estado para resolver lock.

## Rotação do token DuckDNS

**Pendente:** substituir a credencial potencialmente exposta em uma captura anterior e atualizar todas as integrações da mesma conta. A rotação não foi executada durante a reorganização.

1. Identificar os clientes que usam o token atual e reservar uma janela de atualização.
2. Rotacionar a credencial na conta oficial DuckDNS.
3. Atualizar `DUCKDNS_TOKEN` em **Settings → Secrets and variables → Actions**, diretamente no campo protegido.
4. Atualizar os demais clientes e conferir a resolução DNS.
5. Na próxima janela de utilização, validar start/HTTPS e encerrar com stop.

Não incluir o valor em chat, histórico de comandos, documentação ou evidências.
