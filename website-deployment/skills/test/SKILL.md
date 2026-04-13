---
name: test
description: Runs end-to-end tests against the deployed application using Playwright browser automation. Use when verifying a deployment works correctly.
---

# Test — Verify Your Deployment

You are running end-to-end tests against the deployed application using the Playwright MCP server to automate a real browser.

## When This Skill Activates
- User wants to test the deployed application
- User asks "does it work?" or "let's verify the deployment"
- User says "test my site" or "check my deployment"
- Deployment just completed and user wants verification

## Prerequisites
- Application is deployed (`.migration/outputs.json` exists with URLs)
- If not deployed, suggest deploying first

## What To Do

### Phase 1: Plan

Read `.migration/outputs.json` to get deployed URLs, then show the test plan:

1. **Explain what we'll test:**
   "I'll open a real browser and test your deployed app. Playwright automates the browser — clicking buttons, filling forms, and checking results — just like a real user would."

2. **Test plan based on what's deployed:**

   **Core Tests (always run):**
   - Site loads successfully (CloudFront URL returns 200)
   - Main page renders correctly
   - No console errors

   **API Tests (if API deployed):**
   - Each API endpoint returns expected data
   - POST endpoints create data correctly
   - Error handling works (invalid inputs return proper errors)

   **Auth Tests (if Cognito deployed):**
   - Sign-up form works
   - Sign-in form works
   - Protected routes reject unauthenticated requests
   - Protected routes work after sign-in

   **Database Tests (if DynamoDB deployed):**
   - Create, read, update, delete operations work
   - Data persists across requests

### Phase 2: Execute

Use the Playwright MCP server to run each test:

1. **Navigate to the site:**
   - Use `browser_navigate` to open the CloudFront URL
   - Take a snapshot to verify it loaded
   - Check for console errors with `browser_console_messages`

2. **Test the frontend:**
   - Use `browser_snapshot` to check the page content
   - Verify key elements are present
   - Take a screenshot for the user

3. **Test API endpoints:**
   - Use `browser_navigate` to call API endpoints directly
   - Or use `browser_evaluate` to make fetch calls from the browser
   - Verify response status codes and data

4. **Test auth flow (if applicable):**
   - Navigate to sign-up page
   - Fill in registration form with test credentials using `browser_fill_form`
   - Submit and verify success
   - Navigate to sign-in page
   - Fill in login form
   - Verify authenticated state
   - Test a protected API route

5. **Test CRUD operations (if applicable):**
   - Create a new item through the UI or API
   - Read it back
   - Update it
   - Delete it
   - Verify it's gone

### Phase 3: Report

Create a test results summary:

```markdown
# Test Results — [Date]

## Summary
- Passed: [N] tests
- Failed: [N] tests
- Warnings: [N]

## Details

### Frontend
- Site loads at [URL]
- No console errors
- Main page renders correctly

### API
- GET /api/items returns data
- POST /api/items creates item
- DELETE /api/items/:id returns 500 — [details]

### Auth (if tested)
- Sign-up works
- Sign-in works
- Protected routes require auth

### Screenshots
[Include screenshots of key pages]
```

For any failures:
- Explain what went wrong in simple terms
- Suggest specific fixes
- Offer to help fix the issues

Save results to `.migration/test-results.md`

### Phase 4: Next Steps

- If all tests pass: "Everything works! Your app is live and functional."
- If some tests fail: "Let's fix these issues. The most important one is [X] because [reason]."
- Remind about cleanup: "When you're done, ask me to tear down the resources to stop any costs."

## Important Notes

### Playwright MCP Usage
- Use `browser_snapshot` (accessibility tree) for checking content — more reliable than screenshots
- Use `browser_take_screenshot` for visual evidence to show the user
- Use `browser_console_messages` to catch JavaScript errors
- Use `browser_network_requests` to debug API issues
- Always close the browser when done with `browser_close`

### Test Data
- Use clearly fake data for testing (e.g., test@example.com)
- Clean up test data after testing if possible
- Don't use real email addresses for Cognito sign-up tests

### Timeouts
- CloudFront may take a few minutes to propagate after deployment
- Lambda cold starts may cause first request to be slow
- If a test fails due to timeout, try once more before reporting failure
