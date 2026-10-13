# Azure release checklist

Do not check Azure deployment items until the human has intentionally completed them. No Azure resources are created by this repository automatically on push/PR.

## Local readiness

- [ ] Read [architecture and readiness](ARCHITECTURE.md) and [deployment operations](DEPLOYMENT.md).
- [ ] Keep `.env` values local/secret; confirm `.env` is Git-ignored without printing its contents.
- [ ] Run backend unit tests, `compileall`, and all three frontend JavaScript syntax checks.
- [ ] If Docker is installed, build and run the real image locally; check `/health` and `/ready`.
- [ ] Understand that Docker's SQLite/Chroma writes are ephemeral and local Docker is not the cloud persistence test.
- [ ] Decide whether to make one paid local OpenAI embedding call to create the RAG snapshot.

## Azure account and billing safety

- [ ] Select an active Azure subscription and verify its ID/tenant.
- [ ] Read current free-account/trial rules; distinguish trial credit from monthly service grants.
- [ ] Choose a monthly budget amount appropriate for the billing currency.
- [ ] Create actual and forecast cost alerts. Remember a budget alert does not pause spending.
- [ ] Review current region-specific estimates for ACA, ACR Basic, Cosmos serverless, Blob, Log Analytics, OpenAI, and optional Tavily.
- [ ] Explicitly approve potentially paid Cosmos serverless and the ACR recurring baseline.
- [ ] Choose supported Azure region and globally unique suffix.
- [ ] Create a dedicated resource group; do not reuse a group containing unrelated resources.

## Infrastructure and GitHub connection

- [ ] Install Azure CLI and select the correct subscription.
- [ ] Create Microsoft Entra app registration for GitHub deployer; do not create a client secret.
- [ ] Add OIDC federated credential with exact `repo:<owner>/<repo>:environment:azure-deployment` subject.
- [ ] Assign deployer `Contributor` only on the Koivu resource group.
- [ ] Create GitHub environment `azure-deployment`, optionally with required reviewer rules.
- [ ] Add environment variables: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZURE_LOCATION`, and `AZURE_RESOURCE_SUFFIX`.
- [ ] Verify that normal push/pull-request CI has no Azure deployment permissions.
- [ ] Manually dispatch `foundation` only after budget and Cosmos approval; choose `yes` only after reviewing its resource/cost impact.
- [ ] Confirm Bicep deployment and output names before continuing.

## Identity, secrets, and RAG data

- [ ] Assign runtime identity `AcrPull` on ACR.
- [ ] Assign runtime identity `Storage Blob Data Reader` on Storage.
- [ ] Assign runtime identity Cosmos DB built-in data-plane contributor on the Cosmos account.
- [ ] Assign GitHub identity `AcrPush` on ACR.
- [ ] Assign the human upload identity `Storage Blob Data Contributor` on Storage.
- [ ] Verify each role is scoped to the Koivu resource/service, not the whole subscription.
- [ ] Generate/use OpenAI key and set provider-side usage limit.
- [ ] Add environment secrets `OPENAI_API_KEY` and `SUPPORT_AGENT_API_KEY` to GitHub; add `TAVILY_API_KEY` only if needed.
- [ ] Initialize local Chroma once if needed, stop backend, and create a manifest/checksum snapshot ZIP.
- [ ] Upload ZIP under a unique blob name using Azure CLI `--auth-mode login`; do not use SAS/account keys.
- [ ] Add environment variable `RAG_INDEX_BLOB_NAME` matching the exact blob name.
- [ ] Verify private Blob exists and runtime managed identity can read it.

## Application deployment and verification

- [ ] Manually dispatch `application`, choose `yes`, and approve environment protection if configured.
- [ ] Confirm deterministic tests and frontend checks pass before Azure login.
- [ ] Confirm image with the current Git SHA was pushed to ACR.
- [ ] Confirm provider keys were configured as Container Apps secrets, not plaintext Bicep values or frontend config.
- [ ] Confirm HTTPS application URL, `/health`, and `/ready` with nonzero catalog count.
- [ ] Browser-check account registration, Secure/HttpOnly/SameSite cookie, logout/login, and owner-scoped order operations.
- [ ] Browser-check support-case creation and the protected support console with demo-only content.
- [ ] Validate AI/web routes only if provider charges and data transmission are understood.
- [ ] Do not claim real commerce, order fulfillment, inventory, or support integration.

## Security, cost, operations and cleanup

- [ ] Confirm production uses Cosmos, secure cookies, HTTPS, no wildcard CORS, private Blob, and managed identity.
- [ ] Confirm the public support console's shared key is only a demo safeguard; do not use real customer data.
- [ ] Review application/system logs and verify no prompts, keys, cookies, or personal data are logged.
- [ ] Check daily costs and Cosmos RU/storage, Container Apps replica state, ACR storage, Blob, and Log Analytics ingestion.
- [ ] Keep previous image SHA and RAG ZIP until the release is verified.
- [ ] Export any needed test data before cleanup.
- [ ] Verify the exact dedicated resource group before deletion.
- [ ] Delete the Koivu resource group when finished and confirm it no longer exists.
- [ ] Revoke provider API keys in their provider dashboards; remove unused GitHub environment secrets.
