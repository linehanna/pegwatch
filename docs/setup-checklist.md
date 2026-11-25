# Setup checklist (week 1, day 1)

Tick each item when done.

## 1. GitHub
- [ ] Create a public repo `pegwatch` (no README, this skeleton has one)
- [ ] Push this skeleton (`git init`, `git add .`, `git commit -m "Initial skeleton"`, `git push`)
- [ ] Check that `.env` is NOT in the repo

## 2. Google Cloud
- [ ] Sign up for the free trial (card required, nothing is charged within free tier)
- [ ] Create project `pegwatch`
- [ ] Billing → Budgets & alerts → budget of 10 kr / $1 with email alerts at 50%, 90%, 100%
- [ ] Use region `us-central1` for everything (free-tier region)
- [ ] Enable APIs: Cloud Storage, BigQuery, Cloud Run, Cloud Scheduler, Compute Engine, Secret Manager
- [ ] Note: budget alerts only email you, they do not stop spending

## 3. Databricks Free Edition
- [ ] Sign up for Databricks Free Edition
- [ ] Click "Verify identity" and verify with LinkedIn (unlocks outbound internet access)
- [ ] Settings → Linked accounts → connect GitHub
- [ ] Create a Git folder from your repo

## 4. API keys (store in .env locally, never in code)
- [ ] CoinGecko: create a free Demo account and copy the API key
- [ ] Riksbank: register at the API portal and copy the Primary Key
- [ ] Anthropic: API key for the AI agent (can wait until week 4)

## 5. Local tools
- [ ] Git
- [ ] Python 3.11+
- [ ] Google Cloud CLI (`gcloud`), then `gcloud auth login`
- [ ] Terraform
- [ ] Databricks CLI, then `databricks auth login`
- [ ] .NET SDK and Node.js (can wait until week 4)

## 6. First comparison-log entries
- [ ] Log how long each platform's signup and setup took
- [ ] Log anything confusing or blocked
