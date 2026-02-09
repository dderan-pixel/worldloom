# Worldloom UI - React + Vite

A React frontend built with Vite for the Worldloom trading platform.

## Development

```bash
npm install
npm run dev
```

The app will run on http://localhost:5173 (Vite default port).

## Build

```bash
npm run build
```

Output directory: `dist/`

## Deploy on Vercel

### Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/dderan-pixel/worldloom)

### Method 1: Deploy from Subdirectory (Recommended)

**IMPORTANT**: The repository root contains Python backend files that should NOT be deployed to Vercel.

**In Vercel Project Settings:**

1. **Root Directory**: Set to `worldloom-ui` ⚠️ **CRITICAL**
2. **Framework Preset**: Vite
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`
5. **Install Command**: `npm install`

**Why this matters**: Setting the root directory to `worldloom-ui` ensures Vercel only sees the frontend files and ignores Python files at the repository root.

### Method 2: Using vercel.json Configuration

If you cannot set the root directory in settings, the repository includes:
- `.vercelignore` - Excludes Python files from deployment
- `vercel.json` (root) - Configures build to target worldloom-ui only
- `vercel.json` (worldloom-ui) - Frontend-specific configuration

### Environment Variables

No environment variables are required for the basic frontend deployment. If you need to connect to a backend API, add:

- `VITE_API_URL` - Your backend API endpoint (optional)

### Important Notes

⚠️ **Critical Configuration**: 
- **Root Directory MUST be set to `worldloom-ui`** in Vercel project settings
- Without this, Vercel will attempt to build the Python backend and fail
- The Python files (`main.py`, `requirements.txt`) are for backend deployment elsewhere (Railway, Render, etc.)

### Troubleshooting

**Error: "pandas-ta==0.3.14b0" not found**
- This means Vercel is trying to build Python instead of the frontend
- **Solution**: Ensure Root Directory is set to `worldloom-ui` in Vercel project settings
- Go to: Project Settings → General → Root Directory → Enter `worldloom-ui` → Save

**Error: Build fails with Python errors**
- Vercel should never be building Python
- Verify Root Directory setting in Vercel dashboard
- Check that `.vercelignore` file exists at repository root

## Technical Stack

This project uses:

- **React 19** - UI library
- **Vite 6** - Build tool and dev server
- **ESLint** - Code linting
- **Axios** - HTTP client

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript and enable type-aware lint rules. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
