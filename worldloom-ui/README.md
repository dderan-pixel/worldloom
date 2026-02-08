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

### Manual Configuration

1. **Root Directory**: Set to `worldloom-ui` in Vercel project settings
2. **Framework Preset**: Vite
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`
5. **Install Command**: `npm install`

### Environment Variables

No environment variables are required for the basic frontend deployment. If you need to connect to a backend API, add:

- `VITE_API_URL` - Your backend API endpoint (optional)

### Important Notes

- The project root contains Python backend files (`main.py`, `requirements.txt`) which should **NOT** be deployed to Vercel
- A `vercel.json` file at the repository root ensures only the frontend (`worldloom-ui`) is built and deployed
- Python version is pinned to 3.11 in `.python-version` to prevent Vercel from attempting Python builds

## Technical Stack

This project uses:

- **React 19** - UI library
- **Vite 6** - Build tool and dev server
- **ESLint** - Code linting
- **Axios** - HTTP client

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript and enable type-aware lint rules. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
