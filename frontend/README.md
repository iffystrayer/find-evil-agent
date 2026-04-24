# Find Evil Agent - React UI

Modern glassmorphism UI for the Find Evil Agent forensic analysis platform.

## Features

### 🎨 Visual Design
- **Glassmorphism Shell**: Frosted glass effect with backdrop blur
- **BentoGrid Layout**: Adaptive tile system (1x1, 1x2, 2x1, 2x2)
- **Framer Motion**: Smooth animations and transitions
- **Tailwind CSS**: Utility-first styling

### 🔒 Security Indicators
- **Sandbox Status**: Glowing green indicator showing isolated analysis environment
- **Audit Trail**: Sequential check visualization (Static → AST → Entropy → Tool Selection → Execution)
- **Obfuscation Alert**: Flashing amber alert when high entropy detected

### 📊 Components
- **Dashboard**: Main view with stats, analysis form, audit trail
- **Nav Rail**: Left sidebar navigation with icons
- **Analysis Form**: Single analysis and investigative mode inputs
- **Real-time Updates**: Live status during analysis

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons

## Development

```bash
# Install dependencies
npm install

# Start dev server (port 15173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Running Now

✅ **Dev server**: http://localhost:15173/

## Port Configuration

- **Frontend**: `15173` (Vite dev server)
- **Backend API**: `18000` (FastAPI)

All ports use 5-digit numbers as required by project standards.

## Environment Variables

Create `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:18000
```

## Architecture

```
src/
├── components/
│   ├── layout/
│   │   ├── GlassShell.tsx      # Main glass container
│   │   ├── NavRail.tsx         # Left sidebar nav
│   │   └── BentoGrid.tsx       # Adaptive grid system
│   ├── analysis/
│   │   ├── Dashboard.tsx       # Main dashboard
│   │   ├── AnalysisForm.tsx    # Input form
│   │   ├── AuditTrail.tsx      # Sequential checks
│   │   └── ObfuscationAlert.tsx # High-alert warnings
│   └── shared/
│       └── SandboxStatus.tsx   # Isolation indicator
├── api/
│   └── client.ts               # Backend API client
├── App.tsx                     # Root component
├── main.tsx                    # Entry point
└── index.css                   # Tailwind setup
```

## Design System

### Colors
- **Purple Gradient**: Primary brand (header text)
- **Green**: Sandbox status, success states
- **Amber**: Obfuscation alerts, warnings
- **Glass**: `rgba(255,255,255,0.1)` - frosted glass effect

### Animations
- **pulse-glow**: Green dot animation (2s ease-in-out infinite)
- **flash-amber**: Obfuscation alert (1s ease-in-out infinite)
- **hover/tap**: Scale transforms on interactive elements

### Layout
- **BentoGrid**: 2-4 column responsive grid
- **Tiles**: Auto-height with min 200px
- **Spacing**: 4-unit gap (16px)

## API Integration

The UI connects to the FastAPI backend:

```typescript
// Single analysis
await api.analyze({
  incident: "Ransomware detected",
  goal: "Find IOCs",
  format: "html"
});

// Investigative mode
await api.investigate({
  incident: "PowerShell attack",
  goal: "Reconstruct chain",
  max_iterations: 3,
  format: "html"
});
```

## Replacing Gradio

This modern UI replaces the Gradio interface with:
- ✅ Professional glassmorphism design
- ✅ Smooth Framer Motion animations
- ✅ Security-focused visual indicators
- ✅ Real-time audit trail
- ✅ Obfuscation detection alerts
- ✅ Responsive BentoGrid layout

## Next Steps

- [ ] Connect to backend API endpoints
- [ ] Add real-time status updates via WebSocket
- [ ] Implement report viewer with D3.js graph
- [ ] Add dark/light theme toggle
- [ ] Mobile responsive optimizations
- [ ] Add authentication UI
