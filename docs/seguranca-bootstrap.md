# Segurança e bootstrap da infraestrutura

O bootstrap foi aplicado em **25/11/2026** no projeto `triodelicia-mensal4-2026`, número **271680307280**, conferido na API antes do apply. Os recursos, identidades e permissões ficam limitados a esse projeto; a configuração da conta de faturamento não foi alterada.

O bootstrap criou 27 recursos, sem alterações/exclusões de recursos existentes: onze registros de APIs necessárias, três contas de serviço, dois buckets, IAM restrito, pool/provider OIDC e alerta de orçamento. Evidência: `evidencias/bootstrap-validation.json`. A migração do estado foi concluída após corrigir a sintaxe do arquivo HCL gerado; o modo `bootstrap.py --migrate-only` permite retomar essa fase sem reaplicar o plano.

## Permissões e identidades

- `todo-automation`: papel customizado `todoInfrastructure`, com permissões Compute explicitadas em `infra/terraform/bootstrap/main.tf`. Não recebeu administração de IAM, billing, APIs ou buckets.
- IAP apenas para porta 22 e destinos privados 10.42.0.10/10.42.0.20. SSH usa OS Login; não há porta 22 aberta ao público.
- `iam.serviceAccountUser` apenas nas identidades runtime `todo-app`/`todo-db`.
- `todo-db`: acesso `storage.objectUser` somente ao bucket de backups. `todo-app` não recebeu acesso a backups/estado.
- Estado da automação limitado ao prefixo `todo/main/` e locks. Estado de bootstrap em `todo/bootstrap` permanece administrado pelo proprietário. A permissão de listagem no bucket pode revelar nomes, mas não concede leitura dos objetos de bootstrap por esse grant.
- OIDC exige repository ID 1468894543 e owner ID 55161713, issuer oficial GitHub e ref `main` ou `feat/infra-terraform-ansible-actions`. O provider está ACTIVE e a autenticação/plan remotos foram verificados no [workflow](https://github.com/pepepedrinho/S8_GCP_IaC_CICD_ToDoApp/actions/runs/45582818037).
- As três contas criadas foram inspecionadas e não possuem chaves privadas permanentes de usuário. Não foram criados grants adicionais depois do bootstrap inicial.

A operação atual utiliza a **main**, já aceita pelo provider implantado. A condição Terraform também conserva a referência legada `feat/infra-terraform-ansible-actions` para representar exatamente a configuração aplicada. A reorganização não modificou IAM; as branches numeradas são históricas e não receberam confiança OIDC. A remoção da referência legada do provider seria uma alteração separada de infraestrutura.

Quem pode escrever nas branches confiáveis pode alterar os workflows que usam a automação; controlar o acesso ao fork continua necessário. O papel permite administrar o sistema operacional das VMs previstas e seu ciclo de vida dentro deste projeto.

## Credenciais temporárias

O GitHub emite token OIDC para obter um access token de serviço limitado a **3600 segundos**, usado durante jobs de até 50 minutos; não há chave JSON permanente. Isso evita depender da curta validade inicial do token federado durante instalações longas. A [documentação oficial da ação](https://github.com/google-github-actions/auth) descreve a emissão de access tokens por Workload Identity Federation através de conta de serviço. Não foram usados Domain-Wide Delegation, Token Creator adicional ou extensão de política de organização.

O transporte Ansible passa pelo `gcloud` e pelo IAP em cada conexão, preservando o mecanismo de certificados/credenciais temporárias do OS Login. A chave SSH do runner expira em uma hora; os arquivos temporários do runner são removidos ao terminar. Imagens são autenticadas no GHCR pelo runner e carregadas nas VMs; a credencial do registry permanece no runner.

As senhas Mongo estão em GitHub Secrets e em arquivos protegidos nos hosts; valores não constam no repositório/evidências. A aplicação usa um usuário `readWrite` próprio e recebe apenas sua URI por arquivo. A senha administrativa é usada somente no host do banco e em operações protegidas de configuração/backup.

A conferência final está em `evidencias/security-final.json`: três contas sem chaves de usuário e filtro do orçamento lido diretamente da Billing Budgets API. A consulta atribui a quota ao próprio projeto, sem ampliar permissões. Durante erros HTTP 500/502 do dispatch do GitHub, backup/restore foram executados pelo mesmo código versionado em controlador Linux local, com a credencial temporária da conta administradora. Essa etapa tem identidade/orquestração distintas do OIDC; não é apresentada como execução de workflow. Não houve criação de chaves JSON nem grants adicionais.

## Armazenamento e alerta

Os dois buckets Standard regionais têm acesso uniforme e prevenção de acesso público. O estado tem versionamento e proteção contra destruição; backups têm retenção mínima de sete dias e lifecycle limitado. O workflow de encerramento principal não destrói o bootstrap nem os buckets.

O alerta nominal **R$5** tem filtro exclusivo `projects/271680307280`, conferido com o número real de `triodelicia-mensal4-2026`. Limiares 50/90/100%; alerta não bloqueia cobranças nem substitui a meta operacional de US$5.

A implantação não alterou organizações, outros projetos ou a conta de faturamento. A reorganização do repositório também não executa apply/destroy nem altera credenciais.

O token DuckDNS é usado somente pelo runner para o domínio configurado `triodelicia.duckdns.org`. Sua presença é verificada antes de iniciar as VMs. Após exposição em captura anterior, a rotação do token e a atualização das integrações da conta permanecem pendentes; o manual descreve o procedimento. O valor não integra código, evidências ou relatórios.
