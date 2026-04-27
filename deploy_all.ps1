# PowerShell script to automate build, sync, container, and deployment for KidWall

# 1. Upgrade Flutter if needed and build/recompile APKs
Write-Host "Checking for new Flutter version..."
flutter upgrade
Write-Host "Building APKs..."
Set-Location -Path "d:/kidwall/colepago-parents-app"
./build_both_apks.ps1
Set-Location -Path "d:/kidwall"

# 2. Sync all code to GitHub (force push all branches)
git add .
git commit -m "Automated sync and deployment"
git push -f origin main
git checkout colepago
git push -f origin colepago
git checkout colepago-parents-app
git push -f origin colepago-parents-app
git checkout colepagokidwall
git push -f origin colepagokidwall
git checkout main

# 3. Build Docker image for wallet backend
Write-Host "Building Docker image for colepago..."
Set-Location -Path "d:/kidwall/colepago"
docker build -t colepago:latest .
Set-Location -Path "d:/kidwall"

# 4. Apply Terraform to deploy/update container
Write-Host "Applying Terraform deployment..."
Set-Location -Path "d:/kidwall/terraform"
terraform init
terraform apply -auto-approve
Set-Location -Path "d:/kidwall"

Write-Host "All steps completed."
