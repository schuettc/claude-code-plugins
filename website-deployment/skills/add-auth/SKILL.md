---
name: add-auth
description: Adds Cognito authentication and route protection. Use when adding login, signup, authentication, or user management.
---

# Add Auth — Cognito Authentication

You are adding Cognito authentication to protect API routes and manage user accounts.

## Prerequisites
- Lambda handlers exist (from create-api step)
- API Gateway is configured

## What To Do

### Phase 1: Plan

Based on the migration plan, show the user:
- Public routes (no auth needed)
- Protected routes (require login)

Explain the auth flow before asking questions:
"Here's how authentication will work in your app:
1. New users sign up with their email and a password
2. They receive a verification code by email (this confirms they own the email)
3. After verifying, they can sign in
4. When signed in, the browser stores a token that gets sent with every API request
5. Your API checks the token and rejects requests without one"

Ask the user:
1. "Here are the routes I'll protect — does this look right?" — Explain: "Protected routes require the user to be signed in. Public routes work for everyone."
2. "Do you want email verification for new users?" — Explain: "Recommended — it prevents fake accounts. Users get a 6-digit code by email after signing up. Without it, anyone can sign up with any email address."
3. "Password requirements — min 8 characters, uppercase, lowercase, number, symbol. Sound good?" — Explain: "These are standard security defaults. You can relax them but it's not recommended."
4. "Do you want social login (Sign in with Google)?" — Explain: "This adds complexity. I'd recommend starting without it — you can always add it later."
5. "Should users be able to reset their password via email?" — Explain: "Users who forget their password get a reset code by email. Almost always yes."

### Phase 2: Execute

1. **Create `infrastructure/lib/auth-stack.ts`**
   - Cognito User Pool with:
     - Email as sign-in alias
     - Email verification enabled (auto-verify)
     - Strong password policy (min 8, mixed case, numbers, symbols)
     - Account recovery via email
     - Self-registration enabled
   - User Pool Client with:
     - No client secret (for browser-based auth)
     - Auth flows: USER_PASSWORD_AUTH, USER_SRP_AUTH
     - Token validity periods
   - Export User Pool ID and Client ID

2. **Add Cognito Authorizer to API Gateway**
   - Update `api-stack.ts` to:
     - Import the User Pool from auth-stack
     - Create a Cognito Authorizer
     - Apply authorizer to protected routes only
     - Leave public routes unprotected

3. **Create React auth integration** (if frontend exists)
   - Install: `cd frontend && npm install amazon-cognito-identity-js`
   - Create `frontend/src/lib/auth.ts` with:
     - `signUp(email, password)`, `confirmSignUp(email, code)`, `signIn(email, password)`
     - `signOut()`, `getSession()`, `getIdToken()`
   - Environment variables: `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_CLIENT_ID`
   - Create `frontend/src/hooks/useAuth.ts` — manages auth state, provides auth functions, checks session on mount
   - Create `frontend/src/context/AuthContext.tsx` — wraps app to provide auth state
   - Create components in `frontend/src/components/`:
     - `SignInForm.tsx`, `SignUpForm.tsx`, `ConfirmSignUp.tsx`, `ProtectedRoute.tsx`

4. **Update API client** to include auth token:
   Update `frontend/src/lib/api.ts`:
   ```typescript
   import { getIdToken } from './auth';

   export async function apiFetch(path: string, options?: RequestInit) {
     const token = await getIdToken();
     const headers: Record<string, string> = {
       'Content-Type': 'application/json',
       ...options?.headers as Record<string, string>,
     };
     if (token) {
       headers['Authorization'] = `Bearer ${token}`;
     }
     const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
     if (!response.ok) throw new Error(`API error: ${response.status}`);
     return response.json();
   }
   ```

5. **Update React Router** to protect routes:
   ```tsx
   <Route path="/dashboard" element={
     <ProtectedRoute>
       <DashboardPage />
     </ProtectedRoute>
   } />
   ```

### Phase 3: Verify

1. Run `cd infrastructure && npx cdk synth` to verify compilation
2. Show the user: Cognito config, protected vs public routes, frontend auth integration
3. Update `.migration/plan.md` to mark add-auth as complete

## Important Notes

### Security
- Cognito SDK stores tokens in localStorage by default — explain: "The browser remembers your login between page refreshes. This is standard for most web apps. For high-security apps (banking, medical), you'd use a different approach with server-side sessions."
- Set reasonable token expiration — explain: "Access tokens expire after 1 hour (you get a new one automatically). Refresh tokens last 30 days (how long you stay logged in without re-entering your password)."
- Use SRP auth flow — explain: "This means your password is never sent over the network in plain text. Cognito uses a secure challenge-response protocol instead."
- Mention MFA as an optional enhancement — explain: "Multi-factor authentication adds a second step like a code from an authenticator app. Good for production but adds friction during development."

### Best Practices
- Use email as the primary identifier (not username) — explain: "Users sign in with their email address. This is what most modern apps do — fewer things to remember."
- Enable email verification
- Configure account recovery via email only (not phone, to keep it simple)

### Testing Auth
- When testing sign-up, Cognito sends a real verification email. Use a real email address you have access to.
- For automated testing, you can create a test user in the AWS Console (Cognito > User Pools > Users) to skip the email verification flow.
- If the verification email doesn't arrive, check the spam folder. Cognito sends from `no-reply@verificationemail.com`.
