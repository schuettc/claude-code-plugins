---
name: scaffold
description: Creates the CDK TypeScript infrastructure project alongside the existing app. Use when setting up infrastructure or the CDK project.
---

# Scaffold — Set Up Infrastructure Project

You are creating the AWS CDK TypeScript project that defines the cloud infrastructure for the user's app.

## Prerequisites
- `.migration/plan.md` exists (from analyze step)

## What To Do

### Phase 0: Environment Check

Before creating the CDK project, verify the user's environment can support it. Catching these issues now saves confusing errors later.

1. **Check Node.js version** — Run `node --version`. CDK and TypeScript compilation require Node.js 18+. If older:
   "CDK needs Node.js 18 or newer to work properly. You're on [version]. I'd recommend upgrading first — you can use nvm (`nvm install 20`) or download from nodejs.org."

2. **Check AWS CLI is installed** — Run `aws --version`. If not found:
   "We'll need the AWS CLI to deploy later. You don't need it right now for scaffolding, but let's get it installed so you're ready. Here's how: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"

3. **Check AWS credentials** — Run `aws sts get-caller-identity`. If it fails, don't block — just note it:
   "AWS credentials aren't configured yet. That's fine for now — we can set those up before we deploy. Just keep in mind you'll need an AWS account and credentials before the deploy step."

If all checks pass (or the user acknowledges the warnings), proceed.

### Phase 1: Plan

Show the proposed directory layout:
```
infrastructure/
├── bin/
│   └── app.ts              ← CDK app entry point
├── lib/
│   └── api-stack.ts        ← Lambda + API Gateway (next step)
├── lambda/
│   ├── handlers/           ← Lambda function code (next step)
│   └── shared/             ← Shared utilities
├── cdk.json
├── tsconfig.json
└── package.json
```

Ask the user:
1. "What would you like to name your project?" — Explain that this becomes part of AWS resource names (e.g., 'my-app' becomes 'MyAppApiStack'). Suggest lowercase with hyphens. Keep it short — long names hit AWS character limits.
2. "Which AWS region do you prefer?" — Help them choose:
   - **us-east-1** (N. Virginia) — recommended default. Most AWS services launch here first, most examples/docs assume it, and pricing is standard.
   - **us-west-2** (Oregon) — good alternative if their users are on the west coast.
   - **eu-west-1** (Ireland) — if their users are primarily in Europe.
   - Explain: "Pick the region closest to your users for the fastest experience. All regions have the same pricing for these services. You can't easily change this later, but for a learning project it doesn't matter much."

### Phase 2: Execute

1. **Create `infrastructure/` directory**
2. **Create `infrastructure/package.json`** with:
   - `aws-cdk-lib` and `constructs` as dependencies
   - `typescript`, `ts-node`, `@types/node` as dev dependencies
   - `cdk` script pointing to `npx cdk`
3. **Create `infrastructure/cdk.json`** with standard CDK config
4. **Create `infrastructure/tsconfig.json`** with strict TypeScript config
5. **Create `infrastructure/bin/app.ts`** — CDK app entry point
   - Import and instantiate stacks
   - Set the AWS region from user preference
   - Add tags for identification
6. **Create `infrastructure/lib/api-stack.ts`** — Empty stack skeleton (resources come in create-api)
7. **Create `infrastructure/lambda/handlers/` and `infrastructure/lambda/shared/`** (empty, with .gitkeep)

After creating files:
- Run `cd infrastructure && npm install`

### Phase 3: Verify

1. Run `cd infrastructure && npx cdk synth` to verify the project compiles
2. If it fails, debug the issue with the user
3. Update `.migration/plan.md` to mark scaffold as complete

## Important Notes

- Use latest stable CDK version
- Use `RemovalPolicy.DESTROY` for development — explain what this means: "When you delete the stack, all resources get deleted too. For a learning project this is what you want — no leftover resources running up charges. For production, you'd use RETAIN so your database survives even if you accidentally delete the stack."
- Set `env` in the stack to use the user's preferred region
