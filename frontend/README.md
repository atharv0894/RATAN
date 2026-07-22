# RATAN Frontend (Developed by COEP)

This directory contains the presentation layer of the RATAN platform, built using modern web technologies to deliver a premium, responsive, and enterprise-grade user experience.

## 🛠️ Technology Stack
- **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Custom CSS Variables (Design System)
- **State Management & Data Fetching**: React Query (@tanstack/react-query)
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Visualizations**: react-force-graph (for Knowledge Graphs)

## 🎨 Enterprise Design System
The frontend implements a unified design system that supports instant switching between Light and Dark themes.

### CSS Theme Tokens (`globals.css`)
We abandoned hardcoded Tailwind utility classes (e.g., `bg-[#0B1220]`) in favor of dynamic CSS variables (`--background`, `--surface`, `--primary`, `--border-default`, etc.). This approach ensures:
1. **Instant Theme Switching**: Changing the `data-theme` attribute on the `html` tag instantly updates all colors across the app without a page reload.
2. **Consistency**: All components draw from the same semantic palette.
3. **Maintainability**: Global changes only require updating the `globals.css` file.

### Key Layouts & Components
- **DashboardLayout**: A responsive layout with a collapsible sidebar and a top navigation bar. Includes mobile overlays and fluid transitions.
- **Chat Interface**: A ChatGPT-style UI with a toggleable chat history sidebar, streaming message animations, and contextual citations.
- **Card Premium**: A reusable styling class (`card-premium`) that applies standardized background blending, borders, and shadows for dashboard widgets.

## 📁 Directory Structure
- `/app`: Next.js App Router pages and layouts.
  - `/auth`: Login and registration flows.
  - `/dashboard`: Main application interface, including Chat, Documents, Users, Search, and Graph.
- `/components`: Reusable React components (Sidebar, TopBar, ThemeProvider, ForceGraph).
- `/lib`: Utility functions and the central API client instance (`api.ts`).
- `/public`: Static assets.

## 🚀 Running Locally
1. Install dependencies:
   ```bash
   npm install
   ```
2. Set environment variables (create a `.env.local` file):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
The application will be available at `http://localhost:3000`.
