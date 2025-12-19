import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/sonner';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { NewResearch } from './pages/NewResearch';
import { Sessions } from './pages/Sessions';
import { Results } from './pages/Results';
import { Ethics } from './pages/Ethics';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="new" element={<NewResearch />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="results" element={<Results />} />
            <Route path="ethics" element={<Ethics />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;