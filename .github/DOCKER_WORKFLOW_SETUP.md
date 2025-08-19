# Docker Build and Push Workflow Setup

## Required Secrets

To enable the GitHub Actions workflow to push images to Quay.io, you need to configure the following secrets in your repository:

1. **QUAY_USERNAME**: Your Quay.io username (takinosh)
2. **QUAY_PASSWORD**: Your Quay.io password or robot account token

## Setting up Secrets

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:
   - Name: `QUAY_USERNAME`, Value: Your Quay.io username
   - Name: `QUAY_PASSWORD`, Value: Your Quay.io password or robot token

## Using Robot Accounts (Recommended)

For better security, it's recommended to use a Quay.io robot account:

1. Log into Quay.io
2. Go to your repository (quay.io/takinosh/aider-lint-fixer)
3. Click on "Robot Accounts" in the left sidebar
4. Create a new robot account with write permissions
5. Use the robot account credentials as your GitHub secrets

## Workflow Triggers

The workflow will automatically run on:
- Pushes to the `main` branch
- Creation of tags starting with `v` (e.g., v1.0.0)
- GitHub release publications
- Manual trigger via workflow_dispatch

## Image Tags

The workflow will create the following tags:
- `latest` - for the main branch
- Version tags for releases (e.g., `v1.0.0`, `1.0`, `1`)
- Branch names for feature branches
- Short SHA tags for traceability

## Multi-Architecture Support

The workflow builds for both:
- linux/amd64 (x86_64)
- linux/arm64 (ARM 64-bit)

This ensures compatibility across different platforms including Apple Silicon and cloud providers.