# PegWatch: Google Cloud infrastructure (Terraform)

Creates everything PegWatch needs on Google Cloud, inside the always-free tier.

| Resource | Name | Free-tier note |
|---|---|---|
| Cloud Storage bucket | `pegwatch-bronze-<suffix>` | Regional in us-central1, raw files deleted after 90 days |
| BigQuery datasets | `pegwatch_bronze`, `pegwatch_silver`, `pegwatch_gold` | 10 GB storage + 1 TB queries/month free |
| Service accounts | `pegwatch-collector`, `pegwatch-jobs` | Least privilege |
| Secrets | `coingecko-api-key`, `riksbank-api-key` | Empty containers, values added by hand |
| VM | `pegwatch-collector` (e2-micro) | Always free in us-central1, 30 GB standard disk |

## Prerequisites

Enable these APIs once (Terraform needs IAM and Resource Manager to create service accounts and permissions):

```bash
gcloud services enable iam.googleapis.com cloudresourcemanager.googleapis.com storage.googleapis.com bigquery.googleapis.com run.googleapis.com cloudscheduler.googleapis.com compute.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com --async
```

Terraform is not preinstalled in Cloud Shell. Install it in your home folder so it survives restarts:

```bash
mkdir -p ~/bin && cd ~/bin
wget -q https://releases.hashicorp.com/terraform/1.17.2/terraform_1.17.2_linux_amd64.zip
unzip -o terraform_1.17.2_linux_amd64.zip && rm terraform_1.17.2_linux_amd64.zip
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

## Run it (from Cloud Shell)

```bash
git clone https://github.com/linehanna/pegwatch.git
cd pegwatch/platforms/gcp/infra
terraform init
terraform plan      # read it: nothing should cost money
terraform apply     # type yes
```

Terraform state is stored locally in Cloud Shell (`terraform.tfstate`) and is git-ignored. Don't delete the folder in Cloud Shell, or Terraform loses track of what it created.

## Add the API keys (never in code)

```bash
printf '%s' 'YOUR_COINGECKO_KEY' | gcloud secrets versions add coingecko-api-key --data-file=-
printf '%s' 'YOUR_RIKSBANK_KEY'  | gcloud secrets versions add riksbank-api-key  --data-file=-
```

## Tear everything down

```bash
terraform destroy
```

## Cost guardrails

- Only one e2-micro VM, in a free region, with a standard (not balanced) disk
- No streaming inserts into BigQuery: data is loaded from files in batches (free)
- Bronze files expire after 90 days
- Budget alert set manually in the console (see docs/setup-checklist.md)
