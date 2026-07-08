# Push This Project to GitHub

Your project is committed locally. Follow these steps to upload it.

## Option A: GitHub CLI (Recommended)

Open PowerShell in this folder and run:

```powershell
cd "D:\EDUCATON\_\01 - Projects\AB-Test-Meta-Analysis"

# 1. Log in to GitHub (follow the browser prompts)
& "C:\Program Files\GitHub CLI\gh.exe" auth login

# 2. Create repo and push in one command
& "C:\Program Files\GitHub CLI\gh.exe" repo create ab-test-meta-analysis --public --source=. --remote=origin --description "A/B Test Meta-Analysis Engine - experimentation program audit portfolio project" --push
```

If the repo name is taken, use a different name:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" repo create ab-test-meta-analysis-portfolio --public --source=. --remote=origin --push
```

## Option B: Manual (GitHub Website)

1. Go to https://github.com/new
2. Repository name: `ab-test-meta-analysis`
3. Visibility: **Public**
4. Do **NOT** initialize with README (you already have one)
5. Click **Create repository**

Then run:

```powershell
cd "D:\EDUCATON\_\01 - Projects\AB-Test-Meta-Analysis"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ab-test-meta-analysis.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## After Uploading

Add this to your resume/portfolio:

- **GitHub:** `https://github.com/YOUR_USERNAME/ab-test-meta-analysis`
