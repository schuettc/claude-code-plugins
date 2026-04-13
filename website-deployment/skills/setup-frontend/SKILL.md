---
name: setup-frontend
description: Sets up a Vite + React frontend with S3 and CloudFront hosting. Use when setting up frontend hosting, CDN, static file serving, or creating the React app.
---

# Setup Frontend — Vite + React on S3 + CloudFront

You are creating a Vite + React frontend and setting up S3 + CloudFront hosting. This replaces Express's `express.static()` with a build pipeline and CDN hosting.

## Prerequisites
- API Gateway is configured (from create-api)
- Node.js 18+ installed

## What To Do

### Phase 1: Plan

Present the plan to the user, explaining each concept:

1. "We'll create a React app using Vite (a fast build tool). React lets you build your UI with reusable components. Vite compiles everything into optimized static files — HTML, CSS, and JavaScript — that any browser can load."
2. "Everything goes through one CloudFront URL — your website files AND your API. When someone visits your site, CloudFront serves the React app from S3. When the app calls `/api/...`, CloudFront routes that to API Gateway. This means no cross-origin issues."
3. "I'll convert your existing HTML pages into React components. The styling stays the same — we're reorganizing, not redesigning."
4. Ask about custom domain: "Your site will get a CloudFront URL like `d1234abcd.cloudfront.net`. If you want a custom domain like `myapp.com`, we'd need to set up Route53 (AWS's DNS service, ~$0.50/month per domain) and an SSL certificate (free). Want to set that up now, or use the default URL? You can always add a custom domain later."

### Phase 2: Execute

#### Step 1: Create the Vite + React project

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

Project structure:
```
frontend/
├── index.html
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   │   └── useApi.ts
│   ├── lib/
│   │   └── api.ts
│   ├── App.css
│   └── index.css
├── vite.config.ts
├── tsconfig.json
└── package.json
```

#### Step 2: Configure Vite

Update `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3000', // Proxy API calls to Express during development
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

#### Step 3: Set up API client

Create `frontend/src/lib/api.ts`:
```typescript
const API_BASE = import.meta.env.VITE_API_URL || '';

export async function apiFetch(path: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}
```

Note: `VITE_API_URL` is empty in production (same-origin). Vite injects `VITE_`-prefixed env vars at build time.

#### Step 4: Migrate existing HTML/CSS into React components

- Convert each HTML page into a React component in `src/pages/`
- Move CSS into component-level CSS or `src/index.css`
- Move static assets (images, fonts) into `public/`
- Replace direct DOM manipulation with React state and effects
- Replace `fetch()` calls with the `apiFetch` helper
- Add React Router if the app has multiple pages:
  ```bash
  cd frontend && npm install react-router-dom
  ```

#### Step 5: Create the CDK frontend stack

Create `infrastructure/lib/frontend-stack.ts`:

- **S3 Bucket:**
  - Block ALL public access
  - Enable server-side encryption (AES-256)
  - RemovalPolicy.DESTROY for development
  - Auto-delete objects on stack deletion

- **Origin Access Control (OAC):**
  - Create OAC — explain: "This is the secure link between CloudFront and your S3 bucket. It means only CloudFront can read your files — nobody can access S3 directly. This is a security best practice."

- **CloudFront Distribution:**
  - Default behavior: S3 origin (Vite build output)
  - Additional behavior: `/api/*` -> API Gateway origin
  - HTTPS only (redirect HTTP -> HTTPS)
  - Default root object: `index.html`
  - SPA routing: Custom error responses — explain: "React handles page navigation in the browser (client-side routing). If someone bookmarks `/dashboard` and visits it directly, S3 doesn't have a file called `/dashboard` — it would return a 404. We tell CloudFront to serve `index.html` instead, and React figures out which page to show. This is standard for all React apps."
  - Price class: PriceClass.PRICE_CLASS_100 — explain: "This serves your content from data centers in North America and Europe. It's the cheapest option. If your users are in Asia or other regions, you can upgrade later."
  - Enable compression (gzip/brotli)
  - Response headers policy with security headers

- **S3 Deployment:**
  - Use `BucketDeployment` to upload `frontend/dist/`
  - Cache control — explain: "Caching determines how long browsers and CloudFront remember your files before checking for updates:"
    - `assets/*` (hashed filenames): cached forever — "Vite adds a unique hash to each file name (like `app-a1b2c3.js`). When your code changes, the hash changes, so the browser knows to download the new version. This means assets can be cached indefinitely."
    - `index.html`: never cached — "This is the entry point that references your assets. It needs to always be fresh so it points to the latest asset hashes."
  - Invalidate CloudFront cache after deployment — "After uploading new files, we tell CloudFront to clear its cache so users see the latest version immediately."

- **Outputs:** CloudFront URL, distribution ID, S3 bucket name

#### Step 6: Add build step

Update the CDK stack or add a build step that:
1. Runs `cd frontend && npm run build` before deploying
2. Sets `VITE_API_URL` if needed (empty string for same-origin)
3. Uploads `frontend/dist/` to S3

#### Step 7: Verify local development

```bash
cd frontend && npm run dev
```
- Verify the app renders at http://localhost:5173
- Verify API proxy works (if Express is running on port 3000)

### Phase 3: Verify

1. Run `cd frontend && npm run build` to verify the Vite build succeeds
2. Run `cd infrastructure && npx cdk synth` to verify CDK compilation
3. Update `.migration/plan.md` to mark setup-frontend as complete

## Important Notes

### Security
- NEVER make the S3 bucket public — always use OAC
- Enforce HTTPS redirect on CloudFront
- Set security headers via CloudFront response headers policy:
  - `Content-Security-Policy`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- Never embed secrets in frontend code (visible in the browser)

### Vite Specifics
- Use `import.meta.env.VITE_*` for environment variables (not `process.env`)
- Run `npm run build` locally before deploying to catch build errors early

### Development Workflow
- `npm run dev` — Vite dev server with HMR
- `npm run build` — Production bundle to `dist/`
- `npm run preview` — Preview production build locally

### Cost
- S3 + CloudFront: free tier covers most development use
