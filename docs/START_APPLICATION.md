# Starting the InterviewAgent Application

This guide covers running the React frontend and FastAPI backend locally, using
Docker Compose for the complete stack, and provisioning the Azure-hosted
equivalents of SQL Server, Redis, Azure OpenAI, and Azure Speech.

## Frontend development server

Requires Node.js 24 LTS or newer and the backend API on port 8000.

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` and `/health` requests to the
backend. Use **Preview the workspace** to explore the complete interview flow
without a database or an authenticated account.

Voice answers use the browser speech-recognition API and work best in current
Microsoft Edge or Google Chrome. Grant microphone access when prompted. Preview
mode uses browser speech synthesis for the virtual interviewer; authenticated
sessions use the backend Azure Speech endpoint and require `AZURE_SPEECH_KEY`
and `AZURE_SPEECH_REGION` in `backend/.env`.

## Option A — Docker Compose (frontend + SQL Server + Redis + backend)

1. Copy the environment template and fill in secrets:
   ```powershell
   cd backend
   Copy-Item .env.example .env
   ```
   At minimum set `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` (and
   `AZURE_SPEECH_KEY` if you use speech features) — see Option C to provision
   those in Azure.

2. From the repo root, start the stack:
   ```powershell
   docker compose -f infra/docker/docker-compose.yml up --build
   ```

3. Verify the API is up:
   ```powershell
   curl http://localhost:8000/health
   ```

## Option B — Run the backend locally without Docker

Requires a local or remote SQL Server / Azure SQL instance and Redis instance.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt

Copy-Item .env.example .env
# Edit .env: point DATABASE_SERVER/DATABASE_NAME/DATABASE_USER/DATABASE_PASSWORD
# and REDIS_URL at your SQL Server/Redis instance

python -m scripts.init_db
uvicorn app.main:app --reload --port 8000
```

Run the test suite (uses in-memory SQLite + mocked Azure OpenAI, no external
services needed):
```powershell
pytest
```

## Option C — Provision Azure resources and run against the cloud

A script is provided to create the Azure services the backend needs, in
resource group **`Learn_RG`** under the `raazesh066@outlook.com` subscription:

```powershell
.\infra\scripts\create-azure-resources.ps1
```

This creates:
| Resource | SKU | Purpose |
|---|---|---|
| Azure SQL Database | Basic | App database (`interview_db`) |
| Azure Cache for Redis | Basic C0 | Rate limiting / caching |
| Azure OpenAI | S0 + `gpt-4o-mini` deployment | Interview question / evaluation agents |
| Azure AI Speech | S0 | Text-to-speech / speech-to-text |

Notes:
- The script signs you into the Azure CLI (`az login`) if needed, creates the
  resource group if it doesn't exist, and opens the SQL Server firewall to your
  current client IP plus Azure services.
- Azure OpenAI requires your subscription to have access approved
  (https://aka.ms/oai/access). If it's not approved yet, re-run with
  `-SkipOpenAI` and fill in `AZURE_OPENAI_*` manually later.
- Generated connection strings/keys are written to `backend/.env.azure`
  (git-ignored — never commit this file). Merge its contents into
  `backend/.env`.
- The SQL admin password is printed once at the end of the run — save it
  somewhere secure (e.g., a password manager or Key Vault).

After merging `backend/.env.azure` into `backend/.env`, initialize the schema and
start the API as in Option B:
```powershell
cd backend
python -m scripts.init_db
uvicorn app.main:app --reload --port 8000
```

### Tearing down

To avoid ongoing charges when you're done:
```powershell
az group delete --name Learn_RG --yes --no-wait
```
