---
name: deploy
description: Builds, validates, and deploys all infrastructure to AWS. Creates real AWS resources that may incur costs.
disable-model-invocation: false
---

# Deploy — Ship to AWS

You are deploying the user's infrastructure to AWS using CDK. This creates real cloud resources.

## Prerequisites
- CDK project exists and compiles (`cdk synth` succeeds)
- At least the API stack is configured
- AWS CLI is installed and configured with credentials

## What To Do

### Phase 1: Pre-Flight Checks

Run these checks and report results:

1. **AWS CLI configured?**
   ```bash
   aws sts get-caller-identity
   ```
   - If fails with "expired token" or "credentials": Explain "Your AWS session has expired. If you're using SSO, run `aws sso login` to refresh it. SSO sessions typically last 8-12 hours."
   - If fails with "not configured": Guide the user through `aws configure sso`
   - If succeeds: Show the account ID and region, confirm with the user: "I see you're connected to account [ID] in [region]. Is this the right account?"

2. **CDK compiles?**
   ```bash
   cd infrastructure && npx cdk synth
   ```
   - If fails: Debug the issue

3. **Common mistake scan:**
   - Check for wildcard IAM permissions
   - Check for public S3 bucket policies
   - Check for hardcoded secrets
   - Check for missing CORS configuration
   - Report any issues found

### Phase 2: Plan

Show the user exactly what will be created:

1. **Run `cdk diff`:**
   ```bash
   cd infrastructure && npx cdk diff
   ```

2. **Translate the diff** into plain language:
   - "This will create [N] Lambda functions..."
   - "This will create an API Gateway with [N] routes..."
   - "This will create a DynamoDB table..."
   - "This will create a CloudFront distribution..."
   - etc.

3. **Cost estimate:**
   - List each resource and its free-tier eligibility
   - Estimate monthly cost for low traffic (likely $0-5)
   - Remind about cleanup: "Ask me to tear down the resources when you're done to avoid charges"

4. **Explain CDK Bootstrap:**
   If this is the first CDK deployment in this account/region:
   "CDK needs a one-time setup called 'bootstrap' — it creates an S3 bucket that CDK uses to store deployment assets. This is required and costs virtually nothing."

### Phase 3: Confirm

**Get explicit confirmation before deploying:**
"I'm about to create the following AWS resources in account [account-id], region [region]:"
- List each resource
- "This may incur costs. Shall I proceed?"

Wait for user confirmation. Do NOT proceed without it.

### Phase 4: Execute

1. **Bootstrap CDK** (if needed):
   ```bash
   cd infrastructure && npx cdk bootstrap
   ```
   Explain what's happening

2. **Deploy all stacks:**
   ```bash
   cd infrastructure && npx cdk deploy --all --require-approval never --outputs-file ../.migration/outputs.json
   ```
   - Set time expectations: "Deployment typically takes 3-5 minutes. CloudFront distributions take the longest — up to 5-10 minutes on the first deploy. You'll see progress updates as each resource is created."
   - Stream progress and explain what's being created
   - `--require-approval never` because we already confirmed with the user
   - `--outputs-file` saves stack outputs for reference

3. **Handle errors:**
   - If deployment fails, read the error, explain it in plain language, and suggest fixes
   - **"Access Denied"** → "Your AWS user doesn't have permission to create this resource. If you're using SSO, check that your role has admin permissions. If your session expired mid-deploy, run `aws sso login` and try again."
   - **"Resource already exists"** → "A previous deployment left this resource behind. Check the AWS CloudFormation Console — you may need to delete a stuck stack before redeploying."
   - **"ExpiredToken"** → "Your AWS session expired during deployment. Run `aws sso login` to refresh, then try deploying again. CDK will pick up where it left off."
   - **Timeout** → "Some resources take time to create. CloudFront can take up to 15 minutes. This is normal — just wait."

### Phase 5: Post-Deploy

1. **Display outputs:**
   Read `.migration/outputs.json` and display:
   - CloudFront URL (the website)
   - API Gateway URL
   - Cognito User Pool ID and Client ID (if auth deployed)
   - DynamoDB table name (if database deployed)

2. **Update frontend config:**
   - Generate `config.js` with the API URL from outputs
   - Upload to S3
   - Invalidate CloudFront cache

3. **Test the deployment:**
   - Try to access the CloudFront URL
   - Try a simple API call
   - Report results

4. **Guide the user:**
   - "Your app is live! Visit [URL] to see it"
   - "Try the API at [URL]/api/..."
   - "To run comprehensive tests, tell me to test the deployment"
   - "When you're done, ask me to tear down the resources to stop costs"

5. **Update `.migration/plan.md`** to mark deploy as complete

## Important Notes

### Safety
- ALWAYS confirm before deploying
- Show the account ID to prevent deploying to wrong account
- Run `cdk diff` before `cdk deploy` to show what changes
- Save outputs for reference and teardown

### Cost Awareness
- Most resources have free-tier eligibility — mention this
- Lambda: 1M free requests/month
- API Gateway: 1M free calls/month
- DynamoDB: 25 GB free storage, 25 read/write units
- S3: 5 GB free storage
- CloudFront: 1 TB free data transfer
- Reminder: free tier is per-account, 12 months for new accounts

### Troubleshooting Common Deploy Issues
- "Access Denied" → Check IAM permissions for the deploying user
- "Resource already exists" → Stack may be in a broken state, may need manual cleanup
- "Timeout" → Some resources take time (CloudFront can take 5-15 minutes)
- "Limit exceeded" → Account service limits, may need to request increases
