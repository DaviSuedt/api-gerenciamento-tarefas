# API de Gerenciamento de Tarefas

API REST desenvolvida para a GS de Cloud Security Prevention e DevSecOps. A aplicação usa FastAPI, SQLite e autenticação por chave de API.

[![Implantar no Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FDaviSuedt%2Fapi-gerenciamento-tarefas%2Fmain%2Fdeploy%2Fazuredeploy.json)

## Funcionalidades

- Criar, listar, consultar, atualizar e excluir tarefas.
- Persistir os dados em SQLite.
- Validar os dados de entrada.
- Proteger as rotas de tarefas com o cabeçalho `X-API-Key`.
- Documentação interativa no Swagger (`/docs`).
- Pipeline no GitHub Actions com testes, Bandit e auditoria de dependências.

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements-dev.txt
export API_KEY="uma-chave-segura"
uvicorn app.main:app --reload
```

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:API_KEY = "uma-chave-segura"
uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000/docs`. Nas rotas de tarefas, envie o cabeçalho `X-API-Key` com a chave configurada.

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

## Controles de segurança

- Segredos são lidos de variáveis de ambiente e não ficam no repositório.
- Consultas SQL usam parâmetros para impedir injeção de SQL.
- Pydantic valida tamanho e formato dos dados.
- O serviço Linux executa com usuário sem privilégios e proteções do systemd.
- O Nginx limita o tamanho das requisições e adiciona cabeçalhos de segurança.
- O pipeline executa testes, análise estática e auditoria de dependências.

## Testes

```bash
pytest -q
bandit -r app -x tests
pip-audit -r requirements.txt
```

## Arquitetura planejada no Azure

O cliente acessa o IP público da VM. O Network Security Group permite HTTP e restringe SSH. O Nginx recebe a requisição e a encaminha ao Uvicorn/FastAPI em uma porta interna. A API valida a chave e grava os dados no arquivo SQLite armazenado no disco persistente da VM.
