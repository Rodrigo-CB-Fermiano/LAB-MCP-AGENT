# MCP Agent — Arquitetura AWS

## Visão Geral

Aplicação conversacional baseada em **LangChain + MCP (Model Context Protocol)** para investigação de problemas em infraestrutura AWS microservicada.

O agente recebe perguntas em linguagem natural e decide automaticamente quais ferramentas acionar para investigar — cruzando dados de múltiplos serviços sem intervenção manual.

---

## Componentes Principais

### Frontend Conversacional

Duas opções de arquitetura, dependendo do contexto de uso:

| Opção | Stack | Indicada para |
|---|---|---|
| **Opção A** | Streamlit no ECS Fargate | MVP, uso interno, time técnico |
| **Opção B** | React/Vue no S3 + CloudFront | Produção, múltiplos usuários, acesso externo |

#### Opção A — Streamlit (ECS Fargate)
- Frontend Python, sem necessidade de JS
- Mais rápido de construir e iterar
- Requer processo rodando continuamente (não é estático)
- Container exposto via ECS dentro da VPC

#### Opção B — S3 + CloudFront + API Gateway
- Arquivos estáticos (HTML/JS/CSS) servidos pelo S3
- CloudFront como CDN: HTTPS, cache, distribuição global
- API Gateway roteia chamadas `/api/*` para o backend
- **Amazon Cognito** para autenticação de usuários
- Backend nunca exposto diretamente

```
Usuário → CloudFront → S3 (assets estáticos)
                    ↘ API Gateway → FastAPI + LangChain (ECS Fargate)
```

---

### Backend — LangChain Agent

**ECS Fargate** com container Python:

- **FastAPI** — expõe API REST consumida pelo frontend
- **LangChain** — orquestra o agente e decide quais tools acionar
- **langchain-mcp-adapters** — converte tools MCP em tools LangChain nativas
- **ElastiCache (Redis)** — armazena histórico de conversa por sessão

---

### Servidores MCP

Cada servidor MCP expõe **tools** e **resources** para um serviço específico. O agente LangChain chama os servidores via MCP Protocol.

| Servidor MCP | Tools expostas | Deploy ideal |
|---|---|---|
| PostgreSQL | `query_db`, `explain_query`, `list_tables` | Fargate ou Lambda + RDS Proxy |
| DynamoDB | `scan_table`, `get_item`, `query` | Lambda |
| MongoDB | `find_documents`, `aggregate`, `list_collections` | Fargate ou Lambda + Atlas Data API |
| S3 | `list_objects`, `get_object`, `list_buckets` | Lambda |
| Glue Jobs | `get_job_run`, `list_failed_runs`, `get_job_metrics` | Lambda |
| Java Apps | `get_metrics`, `get_health`, `get_logs` | Lambda |
| Datadog | `search_logs`, `get_metrics`, `get_alerts` | Lambda |

---

## Deploy dos Servidores MCP — Lambda vs Fargate

### Pode ser Lambda ✅

| Servidor | Motivo |
|---|---|
| DynamoDB | SDK boto3, stateless, baixa latência |
| S3 | SDK boto3, stateless |
| Glue Jobs | Chama API AWS, stateless |
| Datadog | Chama API REST externa, stateless |
| Java Apps | Chama endpoints de métricas/health, stateless |

### Cuidado com Lambda ⚠️

| Servidor | Problema | Solução |
|---|---|---|
| **PostgreSQL** | Conexão TCP persistente — Lambda abre/fecha conexão a cada invocação, podendo esgotar o pool do RDS | Usar **RDS Proxy** na frente do RDS |
| **MongoDB** | Mesmo problema de pool de conexões | Usar **MongoDB Atlas Data API** (HTTP stateless) ou Fargate |

### Decisão recomendada

```
Lambda            → DynamoDB, S3, Glue, Datadog, Java Apps
Lambda + RDS Proxy → PostgreSQL
Lambda + Atlas API → MongoDB
Fargate           → PostgreSQL e MongoDB sem RDS Proxy disponível
```

---

## Serviços de Suporte

| Serviço | Função |
|---|---|
| **Amazon ECR** | Registry das imagens Docker dos containers |
| **Secrets Manager** | Credenciais de bancos, API keys (Datadog, etc.) |
| **ElastiCache (Redis)** | Histórico de conversa por sessão do usuário |
| **Amazon Bedrock** | LLM (Claude) consumido pelo LangChain Agent |
| **Amazon Cognito** | Autenticação de usuários (Opção B) |
| **CloudWatch** | Logs dos containers e funções Lambda |
| **IAM Roles** | Permissões mínimas por container/Lambda |

---

## Stack Python

```python
# Backend
fastapi                  # API REST do agente
langchain                # orquestrador de tools
langchain-mcp-adapters   # integração MCP ↔ LangChain
boto3                    # acesso aos serviços AWS
redis                    # memória conversacional

# Frontend (Opção A)
streamlit                # UI conversacional em Python
```

---

## Arquivos de Referência

| Arquivo | Descrição |
|---|---|
| `mcp-aws-architecture.drawio` | Diagrama — Opção A (Streamlit + ECS) |
| `mcp-aws-architecture-s3-cloudfront.drawio` | Diagrama — Opção B (S3 + CloudFront + API Gateway) |

---

## Considerações de Segurança

- Todos os servidores MCP devem ter acesso **somente leitura** aos serviços monitorados
- Credenciais nunca em variáveis de ambiente — sempre via **Secrets Manager**
- Backend dentro de VPC privada, nunca exposto diretamente à internet
- API Gateway com autenticação obrigatória (JWT / Cognito)
- IAM Roles com princípio de menor privilégio por serviço

---

## Caminho Sugerido de Implementação

1. Rodar tudo localmente com **Docker Compose**
2. Subir o backend FastAPI + LangChain no **ECS Fargate**
3. Adicionar o frontend (Streamlit ou React) no mesmo cluster / S3
4. Migrar servidores MCP stateless para **Lambda**
5. Configurar **RDS Proxy** para o MCP do PostgreSQL
6. Adicionar **Redis** para memória de sessão
7. Configurar **Cognito + API Gateway** se necessário
