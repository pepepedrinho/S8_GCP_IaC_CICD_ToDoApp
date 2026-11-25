# ToDo App — Terraform, Ansible e GitHub Actions na GCP

Projeto acadêmico baseado no [código do professor](https://github.com/LaercioMLB/todo-app). Cadastrar, listar, concluir, reabrir e excluir tarefas continuam sendo as únicas funções de negócio. A lista é compartilhada, sem login. O cenário de feira está no [escopo original](docs/escopo.md); o usuário confirmou que esta entrega é um trabalho de faculdade, sem evento real.

**Estado da entrega — 25/11/2026:** bootstrap e infraestrutura aplicados no projeto autorizado. OIDC, duas VMs, proteção nativa de seis horas, Ansible completo e segunda execução sem alterações foram comprovados. O HTTPS em **https://triodelicia.duckdns.org** passou no CRUD público e em 100 leituras com 10 conexões simultâneas, sem erros. Backup GCS e restauração remota isolada passaram, com checksum e hash dos dados iguais, sem sobrescrever o banco principal. O CRUD completo também passou no navegador DuckDNS e o dry-run da renovação passou. A matriz registra **15/16 itens (93,75%)**, com o ensaio humano ACE-10 ainda pendente; consulte a [matriz](docs/matriz-aceite.md), as [evidências](docs/evidencias/README.md) e o [relatório](docs/relatorio-entrega.md) para o resultado final.

Para reativar, execute `gh workflow run operate.yml -R pepepedrinho/S8_GCP_IaC_CICD_ToDoApp --ref feat/infra-terraform-ansible-actions -f operation=start`, aguarde o job e acesse o domínio. Ao terminar, use o mesmo comando com `-f operation=stop`. A atualização DuckDNS acompanha o IP efêmero; a URL permanece a mesma. As duas VMs foram confirmadas **TERMINATED** ao final, com discos e backups preservados. Estimativa incremental consolidada: **US$1,6259**, com reservas, sem valor de fatura apurado. Antes da apresentação, conclua a [rotação do token DuckDNS](docs/manual-operacao.md#rotação-do-token-duckdns) informada no manual.

## Arquitetura

```mermaid
flowchart LR
    Browser[Navegador] -->|HTTPS 443| App[VM todo-app: Nginx TLS + React + Express]
    App -->|10.42.0.20:27017 privado| DB[VM todo-db: MongoDB autenticado]
    DB --> Disk[Disco persistente 10 GiB]
    DB -->|Backup validado| GCS[Bucket privado: retenção 7 dias]
    GH[GitHub Actions / OIDC] -->|IAP SSH 22| App
    GH -->|IAP SSH 22| DB
    GH --> State[GCS: estado Terraform versionado]
    DB -->|Proxy apt restrito 3128| App
```

Provisionadas duas `e2-micro`, `us-central1-a`, discos `pd-standard` totalizando 30 GiB. A aplicação tem IPv4 efêmero; o banco não tem IP público. SSH somente por IAP/OS Login. Não há NAT gerenciado, balanceador ou Kubernetes. O host público baixa imagens; Ansible transfere o Mongo por SSH ao host privado. O proxy Squid só permite ao banco acessar repositórios Ubuntu/Canonical.

Cada VM tem `max_run_duration = 21600`, ação `STOP` e reinício automático desabilitado. Esse limite recomeça a cada inicialização. O deploy autônomo também desliga ambas explicitamente ao terminar. A [estimativa de custos](docs/custos.md) usa tarifas brutas sem presumir franquia disponível e inclui armazenamento que permanece após desligar.

## Executar localmente

Pré-requisitos: Docker Desktop com contêineres Linux e Compose v2, Python 3 e Git. Node 24 é necessário para testes fora do Docker. `scripts/install-tools.ps1` instala Node e Terraform portáteis em `.tools/`, com hashes oficiais, sem alterar o PATH global.

```powershell
python scripts/init-local.py
docker compose -p todo-implementation up --build -d --wait --wait-timeout 180
python scripts/smoke.py http://127.0.0.1:8080
```

Abra **http://127.0.0.1:8080**. Somente essa porta é publicada, restrita ao computador local. Frontend e API usam a mesma origem; Mongo e API não publicam portas locais. Senhas aleatórias são geradas uma única vez em `.local/secrets/`, ignorada pelo Git. O volume nomeado preserva tarefas; os dados iniciais entram somente na primeira inicialização do volume.

```powershell
docker compose -p todo-implementation ps
docker compose -p todo-implementation logs --tail 100 backend
docker compose -p todo-implementation stop
```

Use sempre o mesmo nome de projeto Compose para reencontrar seu volume. `down` preserva o volume; **`down -v` apaga os dados**. Não use a remoção de volumes como rotina de desligamento.

## Testes

```powershell
cd backend
npm ci
npm test
cd ../frontend
npm ci
npm test
npm run build
cd ..
python scripts/integration.py
python scripts/test-release.py
```

Os dois scripts de integração usam o projeto `todo-implementation` por padrão; defina `COMPOSE_PROJECT_NAME` se usar outro. Exercitam Mongo real, persistência, indisponibilidade do banco, atualização, rollback manual e recuperação de imagem defeituosa. Os testes de release usam a mesma fonte da aplicação em duas imagens com configurações/versionamento distintos; não testam migração de schema.

Backup local com Bash, mantendo o Compose em execução:

```bash
export COMPOSE_PROJECT_NAME=todo-implementation
export TODO_ROOT="$PWD/.local" COMPOSE_FILE="$PWD/docker-compose.yaml" MONGO_IMAGE=todo-mongo:local
bash scripts/backup.sh
```

No Git Bash do Windows, use `COMPOSE_FILE="$(pwd -W)/docker-compose.yaml"` e `MSYS_NO_PATHCONV=1`. O backup é validado automaticamente em outro volume e contêiner **sem rede**. O Mongo principal é parado temporariamente para caber na memória de uma `e2-micro`, e reiniciado por `trap`, inclusive em falha. A restauração nunca monta o volume principal. Arquivos ficam em `.local/backups/`; não os publique.

## Infraestrutura e pipelines

`infra/terraform/bootstrap/` define APIs, dois buckets protegidos, IAM restrito, três contas de serviço, OIDC e alerta de orçamento. `infra/terraform/main/` define apenas rede, firewalls, discos e duas VMs. A separação permite criar o bucket antes de migrar o estado. `infra/ansible/` configura os hosts; não formata discos que já contenham filesystem inesperado.

O bootstrap foi autorizado e aplicado em 25/11/2026: 27 recursos, sem alteração/exclusão de recursos existentes. O número do projeto foi confirmado antes de criar o alerta. O estado foi migrado para `todo/bootstrap`; os pipelines acessam somente `todo/main`. Os [planos revisados e a validação real](docs/evidencias/README.md) foram preservados. Para uma instalação nova, os scripts `terraform-plan.py` e `bootstrap.py` devem ser usados pelo proprietário após revisão do escopo; não reaplique estados locais antigos sobre o backend já existente.

| Workflow | Acionamento | Resultado |
| --- | --- | --- |
| Validate (`ci.yml`) | Push/PR | Testes, auditoria npm, Terraform, Ansible, integração e backup reais |
| Publish images (`images.yml`) | CI aprovada em push ou manual | Frontend/backend GHCR identificados pelo SHA do commit |
| Infrastructure (`infra.yml`) | Manual; `apply` exige `PROVISION` | Plano com allowlist e provisionamento explícito |
| Configure and deploy (`deploy.yml`) | Manual; SHA completo | Imagens, Ansible, idempotência, HTTPS, CRUD/carga e desligamento final |
| Operate (`operate.yml`) | Manual | Iniciar, parar, saúde, logs, diagnóstico, backup, restore, rollback e aceitação extensa |
| Decommission (`destroy.yml`) | Manual; `DESTROY-TODO` | Backup final validado antes de remover a infraestrutura principal |

Push comum **não cria VMs**. Os workflows de nuvem compartilham um grupo de concorrência. O [manual de operação](docs/manual-operacao.md) explica pré-requisitos, variáveis/secrets, parâmetros, resultados esperados e recuperação. Publicar a branch não equivale a validar provisionamento, OIDC ou execução remota.

## Documentação e evidências

- [Escopo do professor](escopo.pdf) e [versão textual](docs/escopo.md).
- [Matriz REQ/ACE](docs/matriz-aceite.md), [evidências](docs/evidencias/) e [progresso](docs/progresso-implementacao.md).
- [Manual de operação](docs/manual-operacao.md), [custos](docs/custos.md) e [permissões do bootstrap](docs/seguranca-bootstrap.md).
- [Relatório da entrega e pendências](docs/relatorio-entrega.md) e [registro do ensaio pelos alunos](docs/ensaio-alunos.md).

Limitações: a carga curta mede somente uma amostra de 100 leituras/10 conexões; não garante capacidade para uso contínuo. DNS gratuito depende do DuckDNS e de seu token; a URL permanece fixa com atualização automática do IP. O relatório distingue renovação configurada de dry-run efetivamente aprovado. Não há autenticação de usuários, alta disponibilidade ou sincronização automática entre navegadores. A demonstração pelos alunos continua sendo uma etapa humana de aceite.
