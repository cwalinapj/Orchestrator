# GitHub Secrets Configuration

This guide explains how to configure GitHub Secrets for workflows in this repository.

## Setting Up OPENAI_API_KEY Secret

The `codex-auto-fix.yml` workflow uses OpenAI's API to automatically fix failing CI checks. To enable this feature, you need to configure the `OPENAI_API_KEY` secret in your repository settings.

### Prerequisites

Before setting up the secret, you need to obtain an OpenAI API key:

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API keys** section (https://platform.openai.com/api-keys)
4. Click **"Create new secret key"**
5. Give it a descriptive name (e.g., "GitHub Actions - Orchestrator")
6. Copy the generated API key (you won't be able to see it again!)

### Step-by-Step Instructions

#### For Repository Owners/Administrators

1. **Navigate to Repository Settings**
   - Go to your GitHub repository page
   - Click on **Settings** tab (you need admin access to see this)

2. **Access Secrets and Variables**
   - In the left sidebar, expand **Secrets and variables**
   - Click on **Actions**

3. **Add New Repository Secret**
   - Click the **"New repository secret"** button
   - Enter the following details:
     - **Name**: `OPENAI_API_KEY` (must be exactly this name)
     - **Secret**: Paste your OpenAI API key
   - Click **"Add secret"**

4. **Verify Secret Configuration**
   - The secret should now appear in the list (the value will be hidden)
   - The `codex-auto-fix.yml` workflow will now have access to this secret

### Testing the Configuration

After configuring the secret, you can test it by:

1. Triggering a CI workflow that fails
2. The `codex-auto-fix.yml` workflow should automatically run after the CI failure
3. Check the workflow run logs to confirm the secret is being used

### Security Best Practices

- **Never commit API keys** to your repository
- **Rotate keys regularly** - update the secret if you regenerate your API key
- **Use separate keys** for different environments (development, production)
- **Monitor usage** - check your OpenAI usage dashboard regularly
- **Revoke compromised keys** immediately if exposed

### Troubleshooting

#### "OPENAI_API_KEY secret is not set" Error

If you see this error in the workflow logs:
- Verify the secret name is exactly `OPENAI_API_KEY` (case-sensitive)
- Ensure you have admin access to the repository
- Check that the secret was saved correctly in Settings → Secrets and variables → Actions

#### Workflow Not Running

If the auto-fix workflow doesn't trigger:
- Ensure the CI workflow completes (even if it fails)
- Check that the workflow file hasn't been disabled
- Verify repository permissions allow workflow runs

### Alternative: Using Environment Secrets

For organizations with multiple repositories, you can configure the secret at the organization level:

1. Go to your organization settings
2. Navigate to **Secrets and variables** → **Actions**
3. Click **"New organization secret"**
4. Add `OPENAI_API_KEY` with repository access rules
5. Select which repositories can access this secret

## Other Secrets

Currently, this repository only requires the `OPENAI_API_KEY` secret for the auto-fix workflow. Other workflows may be added in the future that require additional secrets.

### GITHUB_TOKEN

Note: The `GITHUB_TOKEN` is automatically provided by GitHub Actions and doesn't need to be configured manually. It's used for:
- Creating pull requests
- Pushing changes
- Accessing repository contents

## Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OpenAI API Keys Documentation](https://platform.openai.com/docs/api-reference/authentication)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
