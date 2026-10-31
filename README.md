# API de Gerenciamento de Tarefas

API REST desenvolvida para a GS de **Cloud Security Prevention e DevSecOps**. A solução utiliza FastAPI, SQLite e autenticação por chave de API, com implantação em uma instância Amazon EC2.

## Acessos

- API: <https://3-20-240-225.sslip.io>
- Health check: <https://3-20-240-225.sslip.io/health>
- Swagger UI: <https://3-20-240-225.sslip.io/docs>

## Funcionalidades

- CRUD completo de tarefas.
- Persistência em SQLite.
- Validação de entrada com Pydantic.
- Autenticação pelo cabeçalho `X-API-Key`.
- Documentação interativa com Swagger UI.
- Pipeline com testes, Bandit e auditoria de dependências.

## Arquitetura na AWS

```text
Cliente HTTPS
      |
      v
Nginx (TLS e proxy reverso)
      |
      v
FastAPI/Uvicorn em 127.0.0.1:8000
      |
      v
SQLite no volume EBS criptografado
```

Infraestrutura utilizada:

- Amazon EC2 `t3.micro` em `us-east-2` (Ohio).
- Ubuntu Server 26.04 LTS.
- Volume EBS gp3 de 8 GiB criptografado.
- IMDSv2 obrigatório.
- HTTP/HTTPS públicos e SSH restrito ao IP do administrador.
- Nginx, systemd e certificado HTTPS da Let's Encrypt.

## Endpoints

| Método | Caminho | Descrição | Protegido |
|---|---|---|---|
| GET | `/` | Informações da API | Não |
| GET | `/health` | Saúde da API e do banco | Não |
| POST | `/tarefas` | Cria uma tarefa | Sim |
| GET | `/tarefas` | Lista tarefas | Sim |
| GET | `/tarefas/{id}` | Consulta uma tarefa | Sim |
| PATCH | `/tarefas/{id}` | Atualiza uma tarefa | Sim |
| DELETE | `/tarefas/{id}` | Exclui uma tarefa | Sim |

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export API_KEY="uma-chave-segura"
python -m uvicorn app.main:app --reload
```

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:API_KEY = "uma-chave-segura"
python -m uvicorn app.main:app --reload
```

## Implantação automatizada na AWS

Use como **User Data** de uma instância Ubuntu:

```bash
#!/bin/bash
set -euo pipefail
curl --fail --silent --show-error --location \
  https://raw.githubusercontent.com/DaviSuedt/api-gerenciamento-tarefas/main/deploy/cloud-init-aws.sh \
  | bash
```

O instalador clona o repositório, cria o ambiente Python, gera uma API Key aleatória, configura permissões, systemd e Nginx e valida o endpoint `/health`. A chave fica em `~/api-key.txt` e não deve ser publicada.

## Controles de segurança

- Segredos carregados por variáveis de ambiente.
- Consultas SQL parametrizadas.
- Validação de tamanho e valores com Pydantic.
- Uvicorn acessível somente pelo Nginx local.
- Serviço executado com usuário sem login e proteções do systemd.
- EBS criptografado, IMDSv2 obrigatório e SSH restrito.
- HTTPS com renovação automática.

## Testes e DevSecOps

```bash
python -m pytest -q
bandit -r app -x tests
pip-audit -r requirements.txt
```

O workflow `.github/workflows/seguranca.yml` é executado em pushes e pull requests.
