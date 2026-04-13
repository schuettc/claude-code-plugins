# Website Deployment Plugin for Claude Code

A plugin that helps you deploy web applications to AWS. Claude analyzes your app, explains what needs to happen, and guides you through each step — adapting to whatever your app looks like.

## What It Does

This plugin gives Claude the skills to take your locally-running web app and deploy it to AWS. Depending on your app, that might include:

- Hosting static files via S3 + CloudFront
- Converting server-side routes to Lambda functions behind API Gateway
- Adding a database with DynamoDB
- Adding authentication with Cognito
- Managing everything as infrastructure-as-code with CDK

Claude figures out what your app needs and suggests the right approach. You stay in control of every decision.

## Prerequisites

- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **AWS CLI v2** with credentials configured — [Installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Claude Code 1.0.33+** — [code.claude.com](https://code.claude.com/docs/en/quickstart)
- **Python & uvx** — for the bundled AWS Documentation MCP server

We recommend using [AWS IAM Identity Center (SSO)](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html) for credentials:

```bash
aws configure sso
```

Verify your credentials work:

```bash
aws sts get-caller-identity
```

## Installation

Open Claude Code and add the marketplace:

```
/plugin marketplace add schuettc/claude-code-plugins
```

Then install the plugin:

```
/plugin install website-deployment@schuettc-claude-code-plugins
```

For local development, clone this repo and load the plugin directly:

```bash
git clone https://github.com/schuettc/claude-code-plugins.git
claude --plugin-dir ./claude-code-plugins/website-deployment
```

## Usage

Open your project in Claude Code and tell Claude what you want:

```
I want to deploy this app to AWS
```

Claude will analyze your app, explain what it finds, and walk you through the migration. The plugin includes skills for each phase — analyzing your app, scaffolding infrastructure, converting routes, setting up hosting, deploying, testing, and cleaning up. Claude activates the right skill based on context.

You can ask Claude about progress, skip steps that don't apply, or go back and change things. If you get stuck, just ask — Claude has access to AWS documentation and can help debug issues.

When you're done experimenting, ask Claude to tear down the resources to avoid charges.

## Bundled MCP Servers

The plugin includes two MCP servers that start automatically:

- **AWS Documentation** — Claude can search and read official AWS docs to answer questions and look up configuration details
- **Playwright** — Claude can open a browser to test your deployed app end-to-end

## Cost Awareness

Most AWS resources this plugin creates are free-tier eligible. For a development app with low traffic, your monthly cost will likely be $0. Claude will explain cost implications as it creates resources and remind you to clean up when you're done.

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/schuettc/claude-code-plugins).

## License

MIT
