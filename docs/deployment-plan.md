# Deployment Plan

We are moving away from Streamlit and deploying the application as a decoupled system:
1. **Backend** (FastAPI) deployed on Render.
2. **Frontend** (Vite + React/VanillaJS) deployed on Vercel.

## 1. Backend Deployment (Render)

The backend is built with FastAPI and will run as a Web Service on Render.

### Option A: Deploy on Render (via Blueprint - Recommended)
We have included a `render.yaml` Infrastructure-as-Code file in the repository root which automates the backend setup.

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New** -> **Blueprint**.
2. Connect your GitHub repository.
3. Render will automatically detect the `render.yaml` file and configure the FastAPI web service (including build and start commands).
4. -During the setup or after creation, securely set the `GROQ_API_KEY` environment variable in the Render dashboard.
   -CORS_ORIGINS: yes (after Vercel deploy); Comma-separated list of allowed browser origins. See §3.
5. Click **Apply** or **Create**. Render will automatically build and deploy your API.

### Option B: Deploy on Render (Manual Setup)
1. Go to [Render Dashboard](https://dashboard.render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Configure the service manually:
   - **Name**: `zomato-ai-backend` (or your preferred name)
   - **Language**: `Python 3`
   - **Branch**: `main`
   - **Root Directory**: Leave blank (root of the repo)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `PYTHONPATH=src python -m uvicorn phase6.api.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
4. Set Environment Variables:
   - `GROQ_API_KEY`: Your Groq API key
   - Any other required keys.
   - CORS_ORIGINS: yes (after Vercel deploy); Comma-separated list of allowed browser origins. See §3.
5. Click **Create Web Service**. Render will automatically build and deploy your API.

### Verify
- After the first deploy, hit:
   -https://<service>.onrender.com/health → {"status":"ok","groq_configured":true}
   -https://<service>.onrender.com/api/v1/meta?cities_cap=20 → JSON with a cities array
   -https://<service>.onrender.com/docs → Swagger UI
-Note the service URL — it goes into the Vercel build env next.

### Cold starts
-Render free-tier services sleep after ~15 minutes of inactivity. The first request after sleep can take 30–60 s. The Phase 6 prewarm thread reduces post-startup latency but does not eliminate the dyno boot itself. If demos need snappy first hits, upgrade the plan or hit /health from an uptime pinger (Better Stack / cron-job.org).


## 2. Frontend Deployment (Vercel)

The frontend is a Vite application located in the `frontend` directory. Vercel provides excellent out-of-the-box support for Vite projects.

### Steps to Deploy on Vercel
1. Go to [Vercel Dashboard](https://vercel.com/) and click **Add New Project**.
2. Import your GitHub repository.
3. Configure the project:
   - **Project Name**: `zomato-ai-frontend`
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
4. Build & Development Settings (Vercel should auto-detect these based on the preset):
   - **Build Command**: `npm run build` or `vite build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
5. Set Environment Variables:
   - `VITE_API_BASE_URL`: The URL of your Render backend service (e.g., `https://zomato-ai-backend.onrender.com`).
   -Vite inlines VITE_* vars at build time, so a redeploy is needed to pick up changes (Vercel does this automatically on env-var save).
   -Never put GROQ_API_KEY in any VITE_* var — frontend/src/lib/api.ts only ever calls ${VITE_API_BASE_URL}/..., and that boundary is what keeps provider keys server-side.
6. Click **Deploy**. Vercel will build your frontend and provide a live URL.

### Verify
-After deploy:
  -https://<project>.vercel.app/ loads the SPA.
  -DevTools → Network → submit the form → request goes to https://<render>.onrender.com/api/v1/recommendations and returns 200.
  -If the request is blocked by the browser with a CORS error, you have not yet completed §3.

### Wire CORS on Render to the Vercel origin
src/phase6/api/main.py reads CORS_ORIGINS (comma-separated). Set it on Render to the exact origins the browser will use:
CORS_ORIGINS=https://<project>.vercel.app,https://<project>-git-main-<team>.vercel.app

### Common gotchas:
- No trailing slash, no path. Origin only: https://foo.vercel.app, not https://foo.vercel.app/.
- Custom domain? Add it too: CORS_ORIGINS=https://app.example.com,https://<project>.vercel.app.
- Preview deploys get unique subdomains. Either disable preview-env builds, point them at a separate staging Render service, or temporarily widen CORS_ORIGINS while testing — never to * for a credentialed app.
- After saving the env var, Render restarts the service. Re-test the SPA call from the browser.

### Smoke-test checklist
- Run these in order from the deployed Vercel URL:
- Page loads, hero + form render, no console errors.
- GET /api/v1/meta populates the city dropdown (visible on first paint, served by Render).
- Submit form with a valid city → status badge shows source: llm and ranked cards render.
- Submit with an obviously empty filter combo (e.g. min rating 5 + a quiet city) → renders the no candidates empty state copy from Phase 5.
- Tail Render logs (Logs tab) — request lines appear with 200, telemetry JSON is logged on stderr.
- If any step fails, see §5.

### Troubleshooting
-Symptom                                  
Browser shows CORS error
-Likely cause / fix
CORS_ORIGINS on Render does not include the exact Vercel origin. Update env var, wait for restart.
-Symptom  
Failed to fetch from frontend
-Likely cause / fix
VITE_API_BASE_URL missing or wrong. Confirm value, then redeploy on Vercel.
-Symptom   
groq_configured: false from /health
-Likely cause / fix
GROQ_API_KEY not set on Render, or has whitespace. Re-paste, redeploy.
-Symptom   
First request hangs ~30 s
-Likely cause / fix
Render free-tier cold start. Ping /health first, or upgrade plan.
-Symptom   
/api/v1/meta 500s with HF errors  
-Likely cause / fix
Hugging Face throttle. Set HF_TOKEN on Render, or lower load_limit.
-Symptom   
Vercel build fails on tsc --noEmit
-Likely cause / fix
Same TS error you would see locally — fix in frontend/, push, Vercel rebuilds.
-Symptom   
Render build fails on pip install -e .
-Likely cause / fix
Confirm runtime.txt is python-3.11.x; Render's default Python may be too old.

### Rollback
-Backend: Render keeps a deploy history; Manual Deploy → Rollback to a previous build.
-Frontend: Vercel’s Deployments tab → Promote to Production on a known-good build.
-Both platforms support instant rollback without rebuilding.

### Cost shape (free-tier)
Resource                   Free tier                Notes
---------------------------  ------------------------   -------------
Render web service     750 hrs/month     Sleeps when idle (cold starts).
Vercel hobby          100 GB bandwidth,   Static SPA is essentially free
                      6k build min/month  at this scale.
Groq                  Free dev quota      Keep candidate_cap modest 
                                          in the API request body.
Hugging Face Hub       Anonymous          Add HF_TOKEN if you hit rate 
                                          limits.

-For demos and coursework, the free tiers are sufficient. For a graded review, hit /health once before the demo to wake the Render dyno.


## Summary of Changes Made
- Removed `.streamlit` directory, `streamlit_app.py`, and `requirements-streamlit.txt`.
- Removed final Streamlit leftover code located in `src/phase8/`.
- Cleaned up `requirements.txt` to remove Streamlit dependency.
- Created `render.yaml` for automated Render backend deployment.
- Prepared this deployment plan for the new decoupled architecture.
