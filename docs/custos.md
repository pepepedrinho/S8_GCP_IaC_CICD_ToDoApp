# Custos e recursos preservados

Preços públicos revisados em **25/11/2026**, USD, us-central1, sem impostos nem conversão da fatura em BRL. Somente o projeto `triodelicia-mensal4-2026`. A aplicação é um projeto de faculdade sem evento real; a premissa é uma sessão de até seis horas seguida de parada explícita.

## Implantação e testes

| Item | Referência bruta fora das franquias |
| --- | --- |
| Duas e2-micro por seis horas | 12 VM-h × US$0,008376428 = US$0,10052 |
| Um IPv4 efêmero por seis horas | 6h × US$0,005 = US$0,03 |
| Três discos pd-standard de 10 GiB por seis horas | 180 GiB-h × US$0,000054795 = US$0,00986 |
| Reserva de tráfego não medido | 8 GiB × US$0,19 = US$1,52; não presume gratuidade de IAP; reserva ampliada para as transferências repetidas durante as correções |
| Storage/operações pequenas | Reserva adicional US$0,02 |

Envelope de referência inferior a US$2 para uma sessão de seis horas; **meta operacional de US$5 para a implantação e os testes**, sem teto rígido garantido. A estimativa final baseada nos ciclos reais fica em `evidencias/cost-estimate.json`. Usa janelas de início/parada das operações da GCP como aproximação conservadora, soma discos desde sua criação e mantém reservas separadas para tráfego/operações. Não é uma leitura da fatura; o custo efetivamente faturado ainda pode ter atraso, créditos, impostos e conversão.

Consolidação histórica da implantação, em 25/11/2026 às 13:57UTC−3: **US$1,6259 estimados**, 6,8403 VM-h e 3,1918 IPv4-h. Inclui todas as tentativas/correções registradas e reservas de US$1,54; não é custo de fatura. GCS totaliza 100.375 bytes em todas as versões, com referência bruta de US$0,00000187/mês nesse tamanho, mais operações. CPU/RAM e IPv4 deixam de consumir com ambas TERMINATED. Coleta: 2026-11-25T16:57:35.046142+00:00.

Fontes das tarifas: [Compute E2](https://cloud.google.com/products/compute/pricing/general-purpose), [discos](https://cloud.google.com/compute/disks-image-pricing), [IPv4 e tráfego](https://cloud.google.com/vpc/network-pricing) e [Cloud Storage](https://cloud.google.com/storage/pricing).

## Inventário que permanece após parar

| Recurso | Quantidade / retenção | Cobrança residual possível |
| --- | --- | --- |
| VMs `todo-app`, `todo-db` | Duas e2-micro preservadas | CPU/RAM deixam de ser cobradas quando TERMINATED; novos starts retomam o consumo |
| Discos `todo-app`, `todo-db`, `todo-mongo-data` | 10 GiB cada, pd-standard | 30 GiB provisionados, cerca de **US$1,20 por 730h brutos** fora da faixa gratuita, mesmo com as VMs paradas |
| Bucket `triodelicia-mensal4-2026-todo-state` | Standard regional, estado versionado; versões antigas após 30 dias | Bytes de todas as versões e operações; objetos atuais preservados |
| Bucket `triodelicia-mensal4-2026-todo-backups` | Standard regional; retenção mínima/lifecycle 7 dias | Backups, manifests e operações; lifecycle não remove no segundo exato |
| IPv4 da aplicação | Efêmero, não reservado | Liberado quando a VM para; o endereço pode mudar na reativação |
| VPC/sub-rede/firewalls, IAM, três contas de serviço, OIDC e alerta | Preservados | Sem tarifa fixa nessa configuração; tráfego/operações dos serviços seguem suas tabelas |

O inventário exato e o tamanho dos objetos/versionamentos estão em `evidencias/cloud-final.json`. A rede `default` gerada pela plataforma também permanece sem VMs conectadas a ela. Não há IP estático reservado, roteador/NAT gerenciado, forwarding rule de balanceador, Cloud SQL, GKE ou terceira VM criada pelo projeto.

## Franquias e comparação mensal

O [Free Tier](https://docs.cloud.google.com/free/docs/free-cloud-features) oferece uso equivalente a uma e2-micro elegível/mês e 30 GiB de disco Standard, compartilhados por conta, além de faixas de GCS. Não há uma VM gratuita por instância. Não foi presumido saldo de franquia disponível em outros projetos da conta; os números acima são brutos. As cotas regionais foram consultadas: E2_CPUS24, instâncias24 e discos4096GiB, inicialmente sem uso.

Referência comparativa de 730h contínuas: duas VMs US$12,23 + um IPv4 US$3,65 + discos US$1,20 ≈ **US$17,08/mês**, mais GCS/operações/tráfego. Com a franquia Compute de uma VM e 30 GiB de disco integralmente disponíveis, o subtotal cairia para aproximadamente US$9,76. O ambiente real está limitado a seis horas por inicialização; não foi configurado para execução mensal contínua.

## Controles aplicados

O orçamento de alerta **R$5**, com limiares 50/90/100%, foi criado com filtro exclusivo `projects/271680307280`; esse número foi confirmado na API como `triodelicia-mensal4-2026`. O alerta é mais conservador que a meta em USD, mas não bloqueia gastos e não equivale a um limite de US$5. [Documentação de budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets).

As proteções efetivas são topologia limitada, allowlist antes de apply, duas e2-micro, três discos pequenos, IP efêmero, ausência de serviços caros, `maxRunDuration=21600`, `instanceTerminationAction=STOP`, `automaticRestart=false` e parada explícita ao concluir. O [limite nativo](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime) foi confirmado na API Compute das duas VMs. Recomeça a cada start; não há reinício periódico.

O faturamento já estava vinculado e não foi alterado durante a implantação. Não foram fechadas contas, excluídos projetos/organizações nem executado Terraform destroy. Os discos, backups e estados são preservados para reativação e continuam exigindo acompanhamento de custo.

## Pipelines e imagens

O fork é público e usa runners padrão hospedados pelo GitHub, contemplados pela [gratuidade do Actions para repositórios públicos](https://docs.github.com/en/actions/concepts/billing-and-usage). O [armazenamento e a transferência do GHCR são atualmente gratuitos](https://docs.github.com/en/billing/concepts/product-billing/github-packages). Não foram contratados runners maiores, planos adicionais ou um domínio pago. As imagens e os artifacts permanecem sujeitos às políticas de uso e retenção desses serviços.

A reorganização de branches e documentação não incluiu inicialização de VMs ou nova implantação. O valor acumulado acima corresponde ao horário da coleta original; o armazenamento continua sujeito à cobrança ao longo do tempo.
