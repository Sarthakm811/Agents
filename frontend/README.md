# Hybrid AI Research System - Frontend

A modern, interactive web interface for the Hybrid AI Research System built with React, TypeScript, and shadcn/ui.

## Features

- **Dashboard**: Real-time monitoring of research metrics, agent activities, and system performance
- **Research Configuration**: Intuitive form-based interface to configure new research projects
- **Session Management**: Track and manage active and completed research sessions
- **Results Viewer**: View, download, and analyze completed research papers
- **Ethics & Compliance**: Monitor ethical compliance and governance across all activities
- **Settings**: Customize system preferences and user profile

## Tech Stack

- **Framework**: Vite + React 19 + TypeScript
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS v4
- **Routing**: React Router v7
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/      # Dashboard-specific components
│   │   ├── layout/         # Layout components (Sidebar, Header)
│   │   └── ui/             # shadcn UI components
│   ├── pages/              # Page components
│   ├── store/              # Zustand stores
│   ├── types/              # TypeScript type definitions
│   ├── App.tsx             # Main app component with routing
│   └── main.tsx            # App entry point
├── public/                 # Static assets
└── index.html              # HTML template
```

## Key Features

### Modern Design
- Glassmorphism effects
- Smooth animations with Framer Motion
- Responsive layout with Tailwind CSS
- Professional color scheme optimized for research applications

### Real-time Monitoring
- Live metrics visualization with Recharts
- Agent status tracking
- Progress indicators for research stages

### User Experience
- Intuitive navigation with sidebar
- Form validation and error handling
- Loading states and transitions
- Accessible UI components

## Development

The frontend is designed to work with the Python backend API. Update the API endpoints in the data fetching hooks to connect to your backend server.

## License

Part of the Hybrid AI Research System project.