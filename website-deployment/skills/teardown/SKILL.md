---
name: teardown
description: Safely removes all AWS resources created by this plugin. Permanently deletes cloud resources.
disable-model-invocation: false
---

# Teardown — Remove AWS Resources

You are removing all AWS resources that were created during the deployment. This is irreversible.

## Prerequisites
- AWS resources were previously deployed
- AWS CLI is configured and working

## What To Do

### Phase 1: Plan

Show the user exactly what will be deleted:

1. **List all deployed stacks:**
   ```bash
   cd infrastructure && npx cdk list
   ```

2. **For each stack, explain what gets deleted:**
   - "Lambda functions — your API will stop working"
   - "API Gateway — API endpoints will return errors"
   - "DynamoDB table — your data will be..."
     - If RemovalPolicy.RETAIN: "...preserved (you can delete it manually later)"
     - If RemovalPolicy.DESTROY: "...permanently deleted"
   - "S3 bucket — your frontend files will be deleted"
   - "CloudFront distribution — your site URL will stop working"
   - "Cognito User Pool — all user accounts will be..."
     - If RemovalPolicy.RETAIN: "...preserved"
     - If RemovalPolicy.DESTROY: "...permanently deleted"

3. **Highlight data implications:**
   - "DynamoDB tables with RETAIN policy will survive and need manual cleanup"
   - "All other resources will be permanently deleted"
   - "This cannot be undone"

### Phase 2: Confirm

**Get explicit confirmation:**

"This will permanently delete the following AWS resources:"
- [list each resource]
- "Any data in DynamoDB tables with DESTROY policy will be lost"
- "Your site will go offline immediately"

"Are you absolutely sure you want to proceed? Type 'yes' to confirm."

Wait for explicit confirmation. Do NOT proceed without it.

### Phase 3: Execute

1. **Empty S3 buckets first** (CDK can't delete non-empty buckets):
   ```bash
   aws s3 rm s3://[bucket-name] --recursive
   ```
   Explain: "Emptying the S3 bucket before deleting the stack"

2. **Destroy all stacks:**
   ```bash
   cd infrastructure && npx cdk destroy --all --force
   ```
   Stream progress and explain what's being removed

3. **Handle errors:**
   - If destruction fails, explain the error and suggest fixes
   - Common issues: non-empty S3 buckets, resources in use, permission errors
   - Some resources may need manual deletion

### Phase 4: Post-Teardown

1. **Verify deletion:**
   ```bash
   cd infrastructure && npx cdk list
   ```
   Should return empty or error (no stacks)

2. **Check for retained resources:**
   - DynamoDB tables with RETAIN policy
   - CloudWatch log groups (CDK often doesn't delete these)
   - CDK bootstrap resources (usually fine to keep)

3. **Guide manual cleanup if needed:**
   - "These resources were retained and may need manual cleanup:"
   - Provide AWS Console URLs or CLI commands for each
   - Explain how to delete them if the user wants to

4. **Clean up local files:**
   - Ask if user wants to remove `.migration/outputs.json`
   - Update `.migration/plan.md` to reflect teardown

5. **Final message:**
   - "All resources have been removed. Your AWS account should not incur any further charges from this deployment."
   - "The CDK bootstrap resources are still in your account — they cost virtually nothing and can be reused for future deployments."
   - "Your code is still here locally — you can redeploy anytime"

## Important Notes

### Safety
- ALWAYS confirm before destroying
- List every resource that will be deleted
- Highlight data loss implications
- Check for retained resources after deletion

### Common Issues
- S3 buckets must be emptied before the stack can be deleted
- CloudFront distributions take 5-15 minutes to delete
- If a stack is in ROLLBACK_COMPLETE state, it needs `aws cloudformation delete-stack`
- Log groups may remain — they cost nothing but can be cleaned up

### What's NOT Deleted
- CDK bootstrap resources (CDKToolkit stack) — keep these for future deployments
- CloudWatch log groups — minimal cost, can be manually deleted
- Any resources with RemovalPolicy.RETAIN
