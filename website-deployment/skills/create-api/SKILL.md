---
name: create-api
description: Converts Express routes into Lambda functions behind API Gateway. Use when creating a serverless API, Lambda functions, or API Gateway.
---

# Create API — Express Routes to Serverless

You are converting Express routes into individual Lambda functions behind API Gateway.

## Prerequisites
- `.migration/plan.md` exists with route mapping
- `infrastructure/` directory exists with CDK project

## What To Do

### Phase 1: Plan

Read `.migration/plan.md` and show the user:

1. **Route mapping table:**
   ```
   Express Route              →  Lambda Handler         →  API Gateway Route
   GET /api/items             →  get-items.ts           →  GET /items
   POST /api/items            →  create-item.ts         →  POST /items
   GET /api/items/:id         →  get-item.ts            →  GET /items/{id}
   PUT /api/items/:id         →  update-item.ts         →  PUT /items/{id}
   DELETE /api/items/:id      →  delete-item.ts         →  DELETE /items/{id}
   ```

2. **Express vs Lambda comparison** for the simplest route:
   ```typescript
   // Before (Express):
   app.get('/api/items', (req, res) => {
     res.json(items);
   });

   // After (Lambda):
   export const handler = async (event: APIGatewayProxyEvent) => {
     return {
       statusCode: 200,
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify(items),
     };
   };
   ```

Ask the user:
1. "Does this route mapping look right?"
2. "Any routes to combine or split differently?"
3. "Which routes should be public vs require login?" (if auth is planned)
4. "Any routes that do something special?" (file uploads, long processing, etc.)

### Phase 2: Execute

1. **Create handler files** at `infrastructure/lambda/handlers/[name].ts`
   - Import types from `aws-lambda` (`APIGatewayProxyEvent`, `APIGatewayProxyResult`)
   - Translate the Express handler logic
   - Add error handling with try/catch
   - Add input validation for POST/PUT routes
   - Return API Gateway response format (`statusCode`, `headers`, `body`)
   - Add CORS headers

2. **Create shared utilities** at `infrastructure/lambda/shared/`
   - `response.ts` — consistent API response helper
   - `errors.ts` — error types and error response helper

3. **Update CDK stack** at `infrastructure/lib/api-stack.ts`
   - Create a REST API (not HTTP API — needed for Cognito authorizer compatibility)
   - For each handler: Lambda function (Node.js 20), IAM role with minimal permissions, API Gateway resource/method
   - Configure CORS on API Gateway
   - Output the API URL

### Phase 3: Verify

1. Run `cd infrastructure && npx cdk synth` to verify compilation
2. Show summary: Lambda function count, API routes, IAM permissions granted
3. Update `.migration/plan.md` to mark create-api as complete

## Important Notes

### Security
- Each Lambda MUST have its own IAM role with only needed permissions
- Never use `Action: '*'` or `Resource: '*'`
- Validate all input in POST/PUT handlers
- Set specific CORS origins (not `*`) — use a placeholder replaced at deploy time

### Lambda Defaults
- Node.js 20.x runtime
- 30-second timeout (less for simple reads)
- 256MB memory
- Environment variables for configuration
- Bundle each handler individually (tree-shaking)

### API Gateway
- Use REST API (not HTTP API) — explain if asked: "AWS has two types of API Gateway. REST API supports Cognito authorization directly, which we need if you add login later. HTTP API is simpler and cheaper but would require more custom code for auth. REST API is the safer default."
- Enable CORS at the API Gateway level — explain if asked: "CORS (Cross-Origin Resource Sharing) is a browser security feature. Since we're routing everything through CloudFront, we shouldn't hit CORS issues, but we configure it as a safety net in case you test the API directly."
- Add throttling defaults (1000 req/s, 500 burst) — explain if asked: "This limits how many requests your API handles per second. It protects you from unexpected traffic spikes (or accidental loops in your code) that could run up your Lambda bill."
