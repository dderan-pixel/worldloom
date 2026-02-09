# How to Fix Vercel Deployment - Preventing Python Build Attempts

## Problem
Vercel is attempting to build Python backend instead of the frontend, resulting in errors like:
```
Failed to run "uv add --active -r /vercel/path0/requirements.txt"
× No solution found when resolving dependencies:
╰─▶ Because there is no version of pandas-ta==0.3.14b0...
```

## Root Cause
The repository has both:
- **Python backend** at root (`main.py`, `requirements.txt`)
- **React frontend** in `worldloom-ui/` subdirectory

Vercel auto-detects the Python files and tries to build them, which fails.

## Solution

### ✅ Files Added/Updated (Already Done)

1. **`.vercelignore`** (root)
   - Tells Vercel to ignore Python files during deployment
   - Prevents Python auto-detection

2. **`vercel.json`** (root)
   - Configures build to target `worldloom-ui` subdirectory
   - Includes `ignoreCommand: "exit 0"` to skip auto-detection

3. **`vercel.json`** (worldloom-ui/)
   - Frontend-specific Vercel configuration
   - Used when Root Directory is set to `worldloom-ui`

4. **`worldloom-ui/README.md`**
   - Updated with clear deployment instructions
   - Includes troubleshooting section

### 🔧 Critical Configuration in Vercel Dashboard

**THIS IS THE KEY STEP** - Without this, Vercel will still try to build Python:

1. Go to your Vercel project dashboard
2. Navigate to: **Settings** → **General**
3. Scroll to: **Root Directory**
4. Enter: `worldloom-ui`
5. Click: **Save**

**Why this is critical**: Setting the Root Directory tells Vercel to treat `worldloom-ui/` as the project root, completely ignoring all Python files outside this directory.

### 📋 Complete Deployment Checklist

#### Option A: New Deployment
```
1. Import GitHub repository to Vercel
2. During import, set:
   - Framework Preset: Vite
   - Root Directory: worldloom-ui
   - Build Command: npm run build
   - Output Directory: dist
3. Deploy
```

#### Option B: Existing Deployment
```
1. Go to Project Settings
2. General → Root Directory
3. Set to: worldloom-ui
4. Save
5. Trigger new deployment (Settings → Deployments → Redeploy)
```

## Verification

### How to Verify Configuration is Correct

1. **Check Vercel Build Logs**
   - Should show: "Building in /vercel/path0/worldloom-ui"
   - Should NOT mention: Python, pip, requirements.txt

2. **Check Build Commands**
   - Install: `npm install`
   - Build: `npm run build`
   - NO Python commands should appear

3. **Check Detection**
   - Framework detected: Vite
   - NOT: Python, Flask, FastAPI

### Example: Correct Build Log
```
✓ Detected framework: Vite
✓ Installing dependencies...
✓ npm install
✓ Building...
✓ npm run build
✓ Build completed
```

### Example: Incorrect Build Log (Python detected)
```
❌ Detected Python 3.12
❌ Installing from requirements.txt
❌ Failed: pandas-ta==0.3.14b0 not found
```

## File Structure

```
worldloom/
├── .vercelignore           # NEW - Ignore Python files
├── vercel.json             # UPDATED - Build from subdirectory
├── requirements.txt        # Python (ignored by Vercel)
├── main.py                 # Python (ignored by Vercel)
│
└── worldloom-ui/           # ← Vercel builds THIS directory
    ├── vercel.json         # NEW - Frontend config
    ├── package.json
    ├── vite.config.js
    ├── src/
    └── dist/               # Build output
```

## Common Issues & Solutions

### Issue 1: "pandas-ta version not found"
**Cause**: Vercel is building Python instead of frontend
**Solution**: Set Root Directory to `worldloom-ui` in Vercel settings

### Issue 2: "No package.json found"
**Cause**: Vercel is looking at repository root instead of worldloom-ui
**Solution**: Set Root Directory to `worldloom-ui` in Vercel settings

### Issue 3: "Python version not specified"
**Cause**: Vercel detecting Python files
**Solution**: 
- Set Root Directory to `worldloom-ui`
- Ensure `.vercelignore` exists at root

### Issue 4: Build succeeds but site doesn't work
**Cause**: Incorrect output directory
**Solution**: Ensure Output Directory is set to `dist` (not `worldloom-ui/dist`)

## Testing Locally

Before deploying to Vercel, test the build locally:

```bash
# Navigate to frontend directory
cd worldloom-ui

# Install dependencies
npm install

# Build
npm run build

# Verify output
ls -la dist/
# Should see: index.html, assets/, etc.

# Test production build
npm run preview
```

## Architecture Notes

### Separation of Frontend and Backend

- **Frontend (worldloom-ui)** → Deploy to Vercel
  - Static site (React + Vite)
  - Fast global CDN
  - Free tier available

- **Backend (root)** → Deploy elsewhere
  - Python FastAPI application
  - Deploy to: Railway, Render, Fly.io, etc.
  - Requires Python runtime

### Why Not Deploy Both to Vercel?

Vercel is optimized for static frontends and serverless functions. The Python backend:
- Requires full Python environment
- Has complex dependencies (pandas, numpy)
- Better suited for dedicated Python hosting

## Additional Resources

- [Vercel Root Directory Documentation](https://vercel.com/docs/projects/project-configuration#root-directory)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#vercel)
- [Frontend README](./worldloom-ui/README.md)

## Quick Fix Summary

**If Vercel is trying to build Python:**

1. ✅ Go to Vercel Project Settings
2. ✅ Set Root Directory to `worldloom-ui`
3. ✅ Save and redeploy
4. ✅ Verify build logs show Vite, not Python

**That's it! The key is the Root Directory setting.**

---

Last updated: 2026-02-09
