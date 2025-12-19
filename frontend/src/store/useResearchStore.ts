import { create } from 'zustand';
import type { ResearchSession, ResearchConfig } from '../types';

interface ResearchStore {
  currentSession: ResearchSession | null;
  sessions: ResearchSession[];
  isLoading: boolean;
  error: string | null;
  
  createSession: (config: ResearchConfig) => void;
  updateSession: (session: ResearchSession) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useResearchStore = create<ResearchStore>((set) => ({
  currentSession: null,
  sessions: [],
  isLoading: false,
  error: null,
  
  createSession: (config) => {
    const newSession: ResearchSession = {
      id: `session-${Date.now()}`,
      config,
      status: 'configuring',
      stages: [
        { id: 'stage-1', name: 'Literature Review', status: 'pending', progress: 0 },
        { id: 'stage-2', name: 'Hypothesis Generation', status: 'pending', progress: 0 },
        { id: 'stage-3', name: 'Methodology Design', status: 'pending', progress: 0 },
        { id: 'stage-4', name: 'Data Analysis', status: 'pending', progress: 0 },
        { id: 'stage-5', name: 'Paper Composition', status: 'pending', progress: 0 },
        { id: 'stage-6', name: 'Ethics Review', status: 'pending', progress: 0 },
      ],
      metrics: {
        originalityScore: 0,
        noveltyScore: 0,
        plagiarismScore: 0,
        ethicsScore: 0,
        totalAgents: 5,
        activeAgents: 0,
        tasksCompleted: 0,
        apiCalls: 0,
      },
      agents: [
        { id: 'agent-1', name: 'Literature Agent', type: 'research', status: 'idle', tasksCompleted: 0 },
        { id: 'agent-2', name: 'Hypothesis Agent', type: 'analysis', status: 'idle', tasksCompleted: 0 },
        { id: 'agent-3', name: 'Methodology Agent', type: 'design', status: 'idle', tasksCompleted: 0 },
        { id: 'agent-4', name: 'Data Agent', type: 'processing', status: 'idle', tasksCompleted: 0 },
        { id: 'agent-5', name: 'Ethics Agent', type: 'governance', status: 'idle', tasksCompleted: 0 },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    set((state) => ({
      currentSession: newSession,
      sessions: [...state.sessions, newSession],
    }));
  },
  
  updateSession: (session) => {
    set((state) => ({
      currentSession: session,
      sessions: state.sessions.map((s) => (s.id === session.id ? session : s)),
    }));
  },
  
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));