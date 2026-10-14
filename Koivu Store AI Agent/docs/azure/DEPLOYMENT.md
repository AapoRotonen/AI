# Azure deployment and operations

This guide describes the manual release path. It does not assume that a particular Azure subscription has been provisioned; check its resource group and the latest workflow run before acting. Keep user-specific portal notes and account details outside the public repository.

## 1. Prerequisites

- Active Azure subscription and accepted monthly spending limit for serverless Cosmos DB, ACR Basic, and any usage over free grants.
- A dedicated Azure resource group for this demo, created manually so the workflow can stay scoped to that group.
- Azure CLI on the operator workstation for subscription selection, role assignments, local Blob upload, log inspection, and cleanup. The workflow itself runs on GitHub-hosted Ubuntu, which supplies Azure CLI, Docker Buildx, and Python/Node setup actions.
- GitHub repository environment `azure-deployment`, OIDC federated credential, exact Azure identity/region/suffix variables, and environment secrets. Do not use a long-lived Azure client secret.
- OpenAI API key. Tavily key is optional. The catalog index archive is required before application deployment.

## 2. Local configuration and verification

For ordinary local development, preserve SQLite and Chroma. Use Python 3.12. Copy `backend/.env.example` to `backend/.env` only when the latter does not exist, then set local provider values in your editor. Never print `.env`, paste it into chat, commit it, or put secrets in `frontend/app-config.js`.

From the repository root:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q main.py agent core tests evals scripts
Set-Location ..
node --check frontend/store.js
node --check frontend/support-console.js
node --check frontend/app-config.js
```

The API can serve the static app itself at `http://127.0.0.1:8000/`; alternatively the existing local static preview can use `?apiPort=8000`. `GET /health` is liveness only and must not initialize retrieval or call providers. `GET /ready` checks the initialized database and local catalogue; a local empty catalogue can be not ready until `/setup` is run.

The Docker image builds from the repository root:

```powershell
docker build -t koivu-store:local .
docker run --rm -p 8000:8000 --env-file backend/.env koivu-store:local
```

The Dockerfile runs as a non-root user, binds to `0.0.0.0`, uses a configurable `PORT`, and does not trust forwarded headers. This local Docker run has ephemeral SQLite/Chroma data. Do not use it as a persistence test for Azure.

## 3. Prepare the RAG artifact

`backend/data/products.txt` is the versioned source. If the local Chroma index is empty, start the backend with local keys, set an unpredictable `CATALOG_SETUP_API_KEY`, and run the protected local endpoint once. This is a paid OpenAI embedding operation:

```powershell
$catalogHeaders = @{ "X-Catalog-Setup-Key" = $env:CATALOG_SETUP_API_KEY }
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/setup -Headers $catalogHeaders
```

Stop the API to close Chroma files, then from `backend/` create a versioned archive:

```powershell
python scripts/build_rag_snapshot.py --output ../.rag-snapshots/index-YYYYMMDD.zip
```

This packaging command makes no provider call. Upload it after foundation deployment and runtime identity permissions are set:

```powershell
az storage blob upload `
  --account-name <storage-account-name> `
  --container-name koivu-rag `
  --name <unique-index-YYYYMMDD.zip> `
  --file ../.rag-snapshots/index-YYYYMMDD.zip `
  --auth-mode login `
  --content-type application/zip `
  --overwrite false
```

The developer's Entra user needs `Storage Blob Data Contributor` for upload. The runtime managed identity only needs `Storage Blob Data Reader`. The blob container is private and the storage account disables shared-key auth. No SAS URL is used.

## 4. Provision the foundation

No resource group is created by Bicep. After choosing an active subscription, create a dedicated group and configure the variables and secrets listed in the workflow and this document. The Bicep uses one lowercase alphanumeric suffix for globally unique names and accepts a region parameter.

The first workflow run is manual:

1. GitHub repository → **Actions** → **gated Azure deployment** → **Run workflow**.
2. Select `foundation`.
3. Select `yes` only after reviewing current price estimates and cost alerts.
4. Click **Run workflow** and approve the `azure-deployment` environment if protection rules require it.

Before Azure login it runs deterministic tests, Python compilation, and Node syntax checks. It then compiles `infra/main.bicep` and deploys to the selected resource group. It creates no user data or provider key. The temporary Microsoft sample container is only an infrastructure bootstrap; it is replaced by the next stage.

Bicep outputs resource names and an internal-only Container Apps hostname, not secret values. The foundation sample is not publicly reachable. The application stage publishes the real app over HTTPS and prints its public URL. Save the output names or use the exact suffix formulas in the manual guide. If Bicep compilation fails, no resources have been deployed. If deployment fails part-way, inspect deployment operations in the resource group before retrying.

## 5. Assign runtime and deployer roles

The deployment identity must have:

- `Contributor` at the dedicated resource group scope, to deploy/update resources.
- `AcrPush` at the dedicated ACR resource scope, to push the image.

The Container App's user-assigned identity must have:

- `AcrPull` at the ACR resource scope.
- `Storage Blob Data Reader` at the storage account scope.
- Cosmos DB native `Cosmos DB Built-in Data Contributor` on the Cosmos account, data scope `/`.

The human developer's Azure identity needs `Storage Blob Data Contributor` at the storage account scope for the one-time archive upload. Do not grant the GitHub deploy identity Cosmos data access. Verify the scoped role assignments in Azure before deploying the application.

Cosmos data-plane role assignment uses `az cosmosdb sql role assignment create`; ordinary ARM `Contributor` is not equivalent. The Bicep template intentionally does not grant roles. This keeps the workflow deploy identity from requiring broad RBAC administration rights; the developer assigns the narrow roles once.

## 6. Deploy the application

Before the application run, upload the RAG archive and add these **GitHub environment secrets** to `azure-deployment`:

- `OPENAI_API_KEY` (required)
- `SUPPORT_AGENT_API_KEY` (required; generate a random value at least 32 characters long)
- `TAVILY_API_KEY` (optional)

Set environment variable `RAG_INDEX_BLOB_NAME` to the exact uploaded blob name. Then dispatch **gated Azure deployment** with stage `application` and confirmation `yes`. The job reruns all deterministic tests, builds the Docker image on the GitHub runner, pushes an immutable `GITHUB_SHA` tag, writes the provider values as Container Apps secrets, configures production environment variables and secret references, replaces the private bootstrap image, enables public HTTPS ingress on port 8000, and checks `/health` and `/ready`.

After success, open the printed HTTPS app URL in a normal browser. Verify these manually:

1. Store loads, catalog products render, and `https://<app-host>/health` returns `{"status":"ok"}`.
2. `/ready` returns `status=ready` and a nonzero catalogue count.
3. A new demo account can register and login; browser dev tools show an HTTPS `HttpOnly`, `Secure`, `SameSite=Strict` `koivu_session` cookie.
4. Create a synthetic demo order; it remains after a Container App restart/revision because it is in Cosmos, and a second user cannot read it.
5. Create a support case and use the operator view with the server-side support key. Never use real customer content.
6. Greeting and other deterministic UI paths work. If you explicitly choose to validate live model/search routes, understand that OpenAI/Tavily charges apply and real messages are sent to those providers.

There are no pre-seeded demo accounts. Use registration in the browser. The optional Stripe test checkout is not configured by this Azure workflow and therefore stays disabled in the deployed app. No live payment, inventory, shipment, or production support integration exists.

## 7. Configuration reference

| Setting | Local | Azure | Secret? |
| --- | --- | --- | --- |
| `APP_ENVIRONMENT` | `local` | `production` | No |
| `DATABASE_BACKEND` | `sqlite` | `cosmos` | No |
| `DATABASE_PATH` | SQLite path | Unused in Cosmos mode | No |
| `COSMOS_ENDPOINT` / `COSMOS_DATABASE_NAME` | Blank/default | Cosmos endpoint and `koivu` | Endpoint is not a secret |
| `AZURE_CLIENT_ID` | Blank | User-assigned runtime identity client ID | No |
| `COOKIE_SECURE` | `false` for HTTP localhost | `true` | No |
| `CORS_ALLOWED_ORIGINS` | Local preview origins | Empty for same origin | No |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | `/tmp/koivu/chroma_db` | No; ephemeral runtime cache |
| `RAG_INDEX_BLOB_URL` | Blank | Private HTTPS blob URL without SAS | No; access comes from identity RBAC |
| `OPENAI_API_KEY` | `backend/.env` | GitHub environment secret → Container Apps secret | **Yes** |
| `TAVILY_API_KEY` | Optional local `.env` | Optional GitHub environment secret → Container Apps secret | **Yes** |
| `SUPPORT_AGENT_API_KEY` | Local `.env` | GitHub environment secret → Container Apps secret | **Yes** |
| `CATALOG_SETUP_API_KEY` | Local-only setup route | Not used; `/setup` returns 404 in production | **Yes** |
| `PROVIDER_TIMEOUT_SECONDS` | `30` | `30` | No |

Production settings validate the required OpenAI, Cosmos endpoint, RAG blob URL, long support key, durable backend, HTTPS cookie, and non-wildcard CORS conditions at startup. Tavily is optional. Provider keys are never emitted in infrastructure outputs.

## 8. CI/CD, rollback and updates

The repository-root `.github/workflows/newslens-ci.yml` runs NewsLens checks. Koivu's project-local `.github/workflows/ci.yml` is not loaded by GitHub from this nested path. Koivu's deterministic tests and syntax checks are run by the repository-root `../.github/workflows/azure-deploy.yml` before Azure login. That workflow is manually dispatched, requires explicit `yes` confirmation, can require environment approval, and uses OIDC. It does not deploy on pushes or pull requests.

To roll back, select an existing image digest/SHA from ACR or a prior Container App revision, then run `az containerapp update --image <registry>.azurecr.io/koivu-store:<old-sha>`. Keep the matching RAG blob. The automatic GitHub workflow builds the current checked-out commit, so the CLI is needed for a prior SHA. Verify `/ready` after rollback. Single-revision mode shifts traffic to the new revision; inspect `az containerapp revision list` if that update does not complete.

To release new code, review and commit the intended changes, then manually dispatch `application` with `yes`; the workflow reruns Koivu's deterministic checks before Azure login. To change the catalogue, make a new artifact and blob, update `RAG_INDEX_BLOB_NAME`, and dispatch `application` again.

## 9. Logs, monitoring and troubleshooting

CLI:

```powershell
az containerapp logs show --name <app-name> --resource-group <resource-group> --type console --follow
az containerapp revision list --name <app-name> --resource-group <resource-group> --output table
az containerapp show --name <app-name> --resource-group <resource-group> --query properties.configuration.ingress.fqdn --output tsv
```

Portal: Azure Portal → resource group → Container App → **Monitoring** → **Log stream**; choose **Console** for process logs or **System** for platform events. In the Log Analytics workspace, query only the minimum records needed; logs can contain request IDs, paths, timing, provider token counts and internal IDs, but app event logs do not contain message/answer bodies or credentials. Azure platform logs may have separate data.

| Symptom | Checks |
| --- | --- |
| Foundation action cannot authenticate | Verify subscription/tenant/client ID GitHub environment variables, exact `repo:<owner>/<repo>:environment:azure-deployment` federated subject, `id-token: write`, selected subscription, and Contributor at the target resource group. |
| Bicep deployment fails on a resource provider | Inspect resource group → **Deployments** → failed deployment → operation details. If the message says provider not registered, register the named namespace in the selected subscription, then retry. |
| Image pull denied | Verify Container App identity is assigned `AcrPull` on this ACR and ACR is in the same resource group; verify ACR ARM token authentication is enabled. |
| Cosmos startup/access error | Confirm `COSMOS_ENDPOINT`, database/container names and Cosmos native data-plane role on the runtime identity. Azure Resource Manager Contributor does not authorize database data reads/writes. |
| RAG snapshot restore fails | Confirm private blob exists under the exact `RAG_INDEX_BLOB_NAME`, its URL is correct, runtime identity has Blob Data Reader, and archive manifest/hash is valid. Build a new ZIP only with the app stopped. |
| `/health` works but `/ready` is 503 | Liveness can work while DB/index initialization fails. Inspect startup console logs and role assignments; do not put real data into tests. |
| Login cookie missing | Use the ACA HTTPS URL (not HTTP/local direct API), inspect browser cookie attributes, verify `COOKIE_SECURE=true`, and keep frontend/API on the same host. |
| App looks like the sample hello world | The `foundation` stage has run but `application` has not. Set roles, upload index, add secrets/variables, then dispatch application stage. |
| AI route fails while health/readiness works | Check OpenAI key in the `azure-deployment` environment and Container Apps secret refs. Check provider usage limits/account. Tavily is optional; only external-search routes need it. |

## 10. Backups and recovery

- The immutable RAG ZIP in Blob is the catalog restore artifact. Keep the previous blob until the new release is verified. Storage does not automatically create a second regional copy in this LRS design.
- Cosmos account uses one region and `Session` consistency. The application's user records are not replicated to another region by this Bicep; review the chosen account backup policy in Azure Portal before storing anything beyond demo data. No database export/restore utility is included. Before deleting the resource group, export any data that is genuinely needed; deletion is otherwise permanent from this deployment.
- ACR stores SHA-tagged images. Keep a known-good image until the new version is verified. Retained images consume the included registry capacity; remove obsolete tags only after checking revision/rollback references.
- No production recovery point objective, disaster recovery region, user-data migration, or legal retention guarantee is claimed.

## 11. Cost review and cleanup

At least weekly during a live demo, open Azure Portal → **Cost Management + Billing** → **Cost analysis**. Filter to the demo resource group and group by service. Open Cosmos DB → **Metrics** to review consumed RUs. Review the budget alert mail, Container Apps replica/usage metrics, and Log Analytics ingestion. Budget alerts do not pause or delete resources.

To stop charges and remove the demo, export anything you need first, confirm the exact dedicated resource group name, and run:

```powershell
az group show --name <exact-koivu-resource-group> --query "{name:name,id:id}" --output table
az group delete --name <exact-koivu-resource-group> --yes --no-wait
```

Then wait and verify `az group exists --name <exact-koivu-resource-group>` returns `false`. Do not delete a shared resource group. Deleting the group deletes the app, ACR, Cosmos data, Blob snapshots, and workspace together; AI provider usage and local `.env` keys are separate and must be managed in their own accounts/workstation.

## Official references

- [Azure Container Apps billing](https://learn.microsoft.com/azure/container-apps/billing), [scale rules](https://learn.microsoft.com/azure/container-apps/scale-app), and [managed-identity ACR pull](https://learn.microsoft.com/azure/container-apps/managed-identity-image-pull).
- [Cosmos DB serverless](https://learn.microsoft.com/azure/cosmos-db/serverless/), [cost estimation](https://learn.microsoft.com/azure/cosmos-db/plan-manage-costs), [native data-plane RBAC](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-connect-role-based-access-control), and [Python client guide](https://learn.microsoft.com/azure/cosmos-db/how-to-python-get-started).
- [Azure Blob Python SDK and managed identity](https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python).
- [GitHub Actions OIDC for Azure](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect).
- [Azure CLI install](https://learn.microsoft.com/cli/azure/install-azure-cli/), [CLI sign-in](https://learn.microsoft.com/cli/azure/authenticate-azure-cli), and [Container Apps logs](https://learn.microsoft.com/azure/container-apps/log-streaming).
- [Cost Management budget creation](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets) and [Azure Monitor pricing](https://azure.microsoft.com/pricing/details/monitor/).
