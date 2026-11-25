# Reorganização do repositório

A estrutura de branches representa marcos cumulativos do desenvolvimento. A main é a referência operacional e deve apontar para o mesmo commit de 05-entrega-final. Os marcos não foram divididos por tecnologia quando o código foi introduzido no mesmo commit.

## Marcos preservados

| Branch | Marco original | Marco traduzido | Conteúdo |
| --- | --- | --- | --- |
| `00-base-professor` | `4814004` | `4814004` | Projeto original e três commits do professor, sem adaptações. |
| `01-aplicacao-containers` | `ede9a98` | `88100d1` | Aplicação/Compose, Mongo privado, persistência e recuperação local. |
| `02-infraestrutura-e-cicd` | `9a3a4bf` | `a2a1a96` | Terraform, Ansible, GHCR e pipelines introduzidos em conjunto; preparação da integração. |
| `03-implantacao-gcp` | `0d4aa22` | `91b2971` | Infraestrutura e configurações reais na GCP, transporte IAP/OS Login, autenticação Mongo e DuckDNS. |
| `04-operacao-e-recuperacao` | `8ca67a4` | `c4bddd1` | Prontidão do rollback, backup/restore, lock de manutenção, recuperação e reativação. |
| `05-entrega-final` | `fdee678` | `7defe1a` | Consolidação dos resultados e revisão acadêmica do repositório. |

A última branch inclui commits editoriais e de compatibilidade posteriores ao marco 7defe1a, com a main acompanhando a consolidação. As branches intermediárias são snapshots; não há implantação associada à sua criação.

## Reescrita e segurança do histórico

Foram traduzidas **30 mensagens de commit** da implementação. As árvores, a autoria e as datas de autoria/commit foram preservadas em todos os casos. Os três commits originais do professor mantêm exatamente seus objetos, hashes e histórico; 00-base-professor permanece em 4814004.

O arquivo [commits-reescritos.json](historico/commits-reescritos.json) relaciona cada hash anterior ao novo, à árvore original, à mensagem em português e às datas preservadas. As evidências e as tags de imagem continuam usando os hashes em que os testes ocorreram. A tradução não constitui nova execução desses testes.

Antes da reescrita, o workspace e a sincronização remota foram conferidos e um Git bundle completo foi criado e verificado. A cópia privada fica em `.local/history-backups/20261125T194551Z/repositorio-antes-da-reorganizacao.bundle`, ignorada pelo Git. SHA-256 do bundle: `f511cba1be11e09509420bc14f96d88931e18ff3ca8bd6908ca5a2a7fa00e8ca`. Estados, credenciais e backups da aplicação continuam fora do repositório público.

A main pode avançar por fast-forward a partir da base preservada; a publicação não exige force push. A branch antiga só é removida após a verificação das novas referências, CI e compatibilidade operacional. Não se publica o bundle privado nem se alteram referências do repositório do professor.

## Compatibilidade operacional

- Infraestrutura, deploy, operação e desativação possuem somente workflow_dispatch. Pushes e criação de branches não iniciam ações na GCP.
- Validate acompanha pushes na main e pull requests. Publicação de imagens permanece ligada à CI aprovada na main e à execução manual específica.
- Os comandos do manual usam main; a condição OIDC implantada já aceita essa branch. A referência legada no Terraform foi mantida para representar fielmente o IAM aplicado, sem novo apply.
- Os quatro manifests GHCR dos SHAs 9a2747c/fa626de foram reconferidos por HEAD 200, com digests em [compatibilidade-ghcr.json](evidencias/compatibilidade-ghcr.json). Imagens existentes não foram renomeadas.
- O código de aplicação, Compose, Dockerfiles, scripts operacionais, Terraform, Ansible e testes foi preservado. A revisão de workflows limita-se aos gatilhos e filtros de branches.

## Limpeza e documentação

O README passou a apresentar objetivo, requisitos, arquitetura, evolução, diretórios, automação e operação, com detalhes no manual. Relatório, matriz, segurança, custos e cronologia foram revisados para linguagem técnica e acadêmica. O escopo distingue o cenário de referência da demonstração atual. O relatório anterior foi arquivado; resultados e falhas históricos permanecem rastreáveis.

Foram arquivados privadamente 65 arquivos/diretórios locais: logs, roteiros de diagnóstico, rascunhos de implantação e o build frontend/dist. Não houve exclusão de arquivos funcionais versionados. Dependências locais instaladas foram mantidas e ignoradas para uso posterior. A pasta de dados/backups, estados, planos, chaves e segredos foi preservada. O .gitignore também cobre caches, editores, bundles, archives MongoDB, chaves e arquivos Terraform sensíveis.

## Verificações e estado

As verificações da reorganização distinguem integridade Git, validações estáticas/CI e leituras do estado GCP. A CI desta etapa não representa novo teste remoto de implantação. O registro final das execuções e verificações fica em `evidencias/reorganizacao-validacao.json`.

O aceite permanece em **15/16 (93,75%)**. ACE-10 e rotação do token DuckDNS continuam pendentes. Não houve inicialização de VMs, deploy, Terraform apply/destroy, alteração de credenciais ou mudança de arquitetura. Leituras CLI em [reorganizacao-vms.json](evidencias/reorganizacao-vms.json) confirmam o estado TERMINATED.
