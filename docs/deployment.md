# Deployment Guide

## Azure Functions Deployment

### Prerequisites
- Azure CLI installed and authenticated
- Azure Functions Core Tools v4
- Python 3.12+

### Setup
```bash
# Create resource group
az group create --name templatemill-rg --location eastus

# Create storage account
az storage account create --name templatemillstorage --location eastus --resource-group templatemill-rg

# Create function app
az functionapp create --resource-group templatemill-rg --consumption-plan-location eastus \
  --runtime python --runtime-version 3.12 --functions-version 4 \
  --name templatemill-functions --storage-account templatemillstorage

# Deploy
func azure functionapp publish templatemill-functions
```

### Environment Variables
Set all required environment variables in Azure Function App Settings:
```bash
az functionapp config appsettings set --name templatemill-functions \
  --resource-group templatemill-rg \
  --settings DATABASE_URL="..." ANTHROPIC_API_KEY="..." ETSY_API_KEY="..."
```

## Database Setup
```bash
# Run migrations
alembic upgrade head

# Seed initial keywords
python scripts/seed_keywords.py
```

## Dashboard Deployment
The Flask dashboard can be deployed to Azure App Service or any WSGI-compatible host.
