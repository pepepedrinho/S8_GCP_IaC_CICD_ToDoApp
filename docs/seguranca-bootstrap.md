# Escopo concreto do bootstrap

Projeto único permitido: `triodelicia-mensal4-2026`. A aplicação inicial do bootstrap foi rejeitada pela aprovação automática por conter papéis administrativos predefinidos amplos. **Nenhum apply foi executado.** O código foi reduzido antes de uma nova avaliação.

## Escopo reduzido proposto

- Substituídos `compute.instanceAdmin.v1`, `networkAdmin`, `securityAdmin`, `storageAdmin`, `osAdminLogin` e o consumidor de APIs por **um papel customizado com a lista explícita de permissões Compute** em `infra/terraform/bootstrap/main.tf`.
- A automação não pode alterar IAM de projeto, criar identidades, habilitar APIs, vincular faturamento ou administrar buckets. Essas permissões não fazem parte do papel customizado.
- IAP limitado por condição a porta 22 e destinos privados `10.42.0.10`/`10.42.0.20`.
- `iam.serviceAccountUser` somente nas duas identidades runtime `todo-app` e `todo-db`.
- OIDC aceita apenas o repository ID/owner ID verificados do fork e as branches main/implementação; não cria chaves JSON permanentes.
- Acesso a estado limitado aos objetos `todo/main/` e locks; bucket privado com versionamento e proteção contra destruição. Estado bootstrap separado não fica legível para a automação por esse grant.
- Banco pode criar/ler objetos de backup no bucket próprio, com retenção mínima de 7 dias e prevenção de acesso público. Aplicação não recebe acesso aos backups.
- Orçamento de alerta nominal R$ 5, filtrado exclusivamente ao projeto. Não é um bloqueio de gastos e não substitui a meta US$ 5.

O papel customizado continua permitindo criar/remover a topologia Compute deste projeto e administrar o sistema operacional das duas VMs via IAP. Isso é necessário para Terraform/Ansible e deve ser considerado ao aprovar. OIDC/credenciais ficam restritos ao fork; alguém com escrita numa branch confiável pode alterar workflows, portanto controlar acesso ao repositório continua necessário.

A validação local e o plano não comprovam aplicação do IAM, emissão de credenciais OIDC, acesso remoto ou execução na GCP. Esses resultados serão registrados apenas após aprovação e execução reais.

Uma segunda avaliação do escopo reduzido também foi rejeitada: a aprovação automática exigiu autorização direta do usuário para as alterações persistentes de IAM, OIDC, contas de serviço, buckets, APIs e orçamento. A pergunta de aprovação foi apresentada; não houve resposta até o fechamento deste registro. Nenhum apply foi executado nem foi usada outra rota para realizar essas mudanças.

As variáveis/secrets do fork foram configuradas separadamente, dentro da autorização para configurar pipelines. Os valores de provider/conta apontam para as identidades planejadas; sua presença no GitHub não cria recursos nem comprova autenticação GCP.
