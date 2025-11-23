# Deployment Guide

This guide covers deploying both the backend (Railway) and frontend (Vercel) of the FranchisesGlobal application.

## Prerequisites

- Railway account and project set up
- Vercel account
- GitHub repository connected to both platforms
- All required API keys and credentials

## Backend Deployment (Railway)

### Environment Variables Required

Add these environment variables in your Railway project settings:

```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
OPENAI_API_KEY=your_openai_api_key
FRANSERVE_EMAIL=your_franserve_email (optional)
FRANSERVE_PASSWORD=your_franserve_password (optional)
ALLOWED_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app
```

**Note**: `ALLOWED_ORIGINS` should be a comma-separated list of allowed frontend URLs. Use `*` for development, but specify exact URLs for production security.

### Railway Configuration

- **Root Directory**: `/` (project root)
- **Build**: Uses `Dockerfile` automatically
- **Start Command**: `./start.sh` (handled by Dockerfile)

### Getting Your Railway URL

After deployment, Railway will provide a URL like:
```
https://your-app.up.railway.app
```

Save this URL - you'll need it for the frontend configuration.

## Frontend Deployment (Vercel)

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository

### Step 2: Configure Project Settings

- **Framework Preset**: Next.js (auto-detected)
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (auto-detected)
- **Output Directory**: `.next` (auto-detected)
- **Install Command**: `npm install --legacy-peer-deps` (configured in `vercel.json`)

**Note**: The `--legacy-peer-deps` flag is required because `react-simple-maps@3.0.0` doesn't officially support React 19 yet, but React 19 is backward compatible and works fine.

### Step 3: Add Environment Variables

In Vercel project settings → Environment Variables, add:

```
NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app
```

**Important**: 
- The `NEXT_PUBLIC_` prefix is required for Next.js to expose the variable to the browser
- Replace `https://your-railway-app.up.railway.app` with your actual Railway backend URL
- Add this variable for **Production**, **Preview**, and **Development** environments

### Step 4: Update Backend CORS

After you get your Vercel URL (e.g., `https://your-app.vercel.app`), update the Railway environment variable:

```
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

This ensures your Vercel frontend can communicate with the Railway backend.

### Step 5: Deploy

1. Click "Deploy"
2. Vercel will automatically build and deploy your frontend
3. Your app will be available at `https://your-app.vercel.app`

## Post-Deployment Checklist

- [ ] Backend health check passes (`https://your-railway-app.up.railway.app/`)
- [ ] Frontend loads successfully
- [ ] API calls from frontend to backend work (check browser console)
- [ ] CORS errors are resolved
- [ ] Environment variables are set correctly in both platforms
- [ ] Custom domain configured (if applicable)

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:
1. Check that `ALLOWED_ORIGINS` in Railway includes your Vercel URL
2. Ensure the URL matches exactly (including `https://`)
3. Redeploy the backend after updating CORS settings

### API Connection Errors

If the frontend can't reach the backend:
1. Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
2. Check that the Railway backend is running and accessible
3. Test the backend URL directly in your browser: `https://your-railway-app.up.railway.app/`

### Build Failures

- **Frontend**: Check Vercel build logs for TypeScript or build errors
- **Backend**: Check Railway logs for Python import or dependency errors

## Environment Variable Reference

### Railway (Backend)
- `GEMINI_API_KEY` - Google Gemini API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `OPENAI_API_KEY` - OpenAI API key
- `ALLOWED_ORIGINS` - Comma-separated list of allowed frontend URLs

### Vercel (Frontend)
- `NEXT_PUBLIC_API_URL` - Railway backend URL

