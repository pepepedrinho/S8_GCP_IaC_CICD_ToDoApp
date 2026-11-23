# Custos e autorização financeira

Preços públicos consultados em 23/11/2026, USD, sem impostos/conversão. Somente `triodelicia-mensal4-2026`.

## Implantação inicial: meta inferior a US$ 5

- Duas e2-micro em us-central1-a, máximo nativo de 6 horas **por inicialização**, ação STOP; sem reinício automático/periódico.
- CPU + RAM: 12 VM-h × US$ 0,008376428 = **US$ 0,10052 brutos**. A franquia mensal disponível pode abater integralmente; não se presume uma franquia por VM.
- IPv4 efêmero somente na aplicação: até **US$ 0,03/6 h**, sem reservar endereço estático; liberado ao parar a VM.
- Três discos pd-standard de 10 GiB: **US$ 0,00987/6 h brutos**, aproximadamente **US$ 1,18/30 dias** se não houver franquia. Disco de dados continua existindo com VMs desligadas.
- Dois buckets Standard regionais us-central1, objetos de backup/state pequenos e retenção limitada. Referência de storage: US$ 0,02/GiB-mês; faixa gratuita compartilhada de 5 GiB-mês, com cotas de operações.
- Tráfego Standard Tier explicitamente configurado na aplicação; tabela consultada oferece 200 GiB/mês por conta. Não presumir a mesma cota para IAP e outras rotas. Reserva conservadora: até 2 GiB × US$ 0,19 = **US$ 0,38** fora de franquias para transferências dos ensaios.
- Envelope inicial de referência: **inferior a US$ 1** para uma sessão de até seis horas, mais variações/tributos. Meta operacional US$ 5 não é limite rígido garantido.

Não há Load Balancer, Cloud NAT, Cloud SQL, GKE, IP estático, Secret Manager pago ou terceira VM. Backups são restaurados isoladamente na própria VM de banco, de forma sequencial para caber na RAM.

## Recursos preservados depois dos testes

VMs devem terminar `TERMINATED`. Discos 30 GiB, buckets, state/versionamento, backups validados (7 dias), contas de serviço e OIDC permanecem. Podem existir cobranças de disco/storage/operações se as franquias compartilhadas estiverem consumidas. O custo não é declarado zero apenas porque as VMs pararam.

Budget é alerta, não bloqueio. Não existe teto absoluto de US$ 5 aplicado a todas as cobranças Compute por orçamento. Proteções reais: duas VMs e2-micro, allowlist do plano, ausência de serviços caros, IP efêmero, STOP nativo em seis horas e desligamento explícito após testes. A emissão de alerta depende da API/permissão de budgets e não pode ser tratada como trava.

## Fontes

- [Free Tier](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Compute](https://cloud.google.com/products/compute/pricing/general-purpose)
- [Discos](https://cloud.google.com/compute/disks-image-pricing)
- [IPv4 e rede](https://cloud.google.com/vpc/network-pricing)
- [Cloud Storage](https://cloud.google.com/storage/pricing)
- [Duração máxima nativa](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime)
- [Budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)

## Referência mensal e sessão acadêmica

Para 730 horas contínuas com duas VMs: aproximadamente US$ 12,23 de CPU/RAM brutos, US$ 3,65 de IPv4 e US$ 1,18 de discos, total de **US$ 17,06/mês**, mais GCS, operações e tráfego. A faixa gratuita de Compute cobre o equivalente a uma e2-micro/mês elegível e é compartilhada entre instâncias; se integralmente disponível, o subtotal poderia cair para cerca de US$ 9,77 (uma VM coberta e discos dentro da faixa), antes de outros serviços. Não se presume que as duas VMs contínuas sejam gratuitas.

Não há data ou duração de evento: é projeto de faculdade. Premissa operacional de uma sessão de até seis horas com dez acessos simultâneos em teste curto, seguida de desligamento. Não é compromisso de capacidade: a medição em e2-micro ainda está pendente. A proteção nativa de seis horas é incompatível com execução contínua sem novos starts intencionais; a referência mensal serve para comparação de custos, não como configuração de produção.

O faturamento já foi vinculado pelo mecanismo de permissões. O bootstrap IAM/OIDC/buckets foi rejeitado pela aprovação automática e não aplicado. Nenhuma VM/disco/bucket foi criado por esta implementação até esse bloqueio. Não há custo real de implantação apurado; faturamento pode ter atraso e deve ser conferido novamente após qualquer teste real. Não atribuir custos históricos de projetos antigos ao projeto novo.

As franquias acima vêm da tabela pública. O saldo de franquia disponível e a cota regional de Compute na conta ainda não foram confirmados pela API, que continua desabilitada até a aprovação do bootstrap. Conferir ambos antes do primeiro apply principal.
