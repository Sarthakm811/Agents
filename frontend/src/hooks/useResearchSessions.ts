import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { ResearchConfig, ResearchSession } from '@/types';

export function useResearchSessions() {
  return useQuery({
    queryKey: [ 'sessions' ],
    queryFn: () => apiClient.listSessions(),
  });
}

// Default polling interval in milliseconds
const POLLING_INTERVAL = 3000;

// Terminal statuses that should stop polling
const TERMINAL_STATUSES: ResearchSession[ 'status' ][] = [ 'completed', 'failed' ];

/**
 * Determines if polling should be active based on session status.
 * Polling continues while status is "running" and stops on terminal statuses.
 */
export function shouldPoll(status: ResearchSession[ 'status' ] | undefined): boolean {
  if (!status) return false;
  return status === 'running';
}

/**
 * Determines if a session has reached a terminal status.
 */
export function isTerminalStatus(status: ResearchSession[ 'status' ] | undefined): boolean {
  if (!status) return false;
  return TERMINAL_STATUSES.includes(status);
}

/**
 * Calculates the refetch interval based on session status.
 * Returns the polling interval when running, false otherwise.
 */
export function getRefetchInterval(status: ResearchSession[ 'status' ] | undefined): number | false {
  return shouldPoll(status) ? POLLING_INTERVAL : false;
}

export function useResearchSession(sessionId: string) {
  const query = useQuery({
    queryKey: [ 'session', sessionId ],
    queryFn: () => apiClient.getSession(sessionId),
    enabled: !!sessionId,
    // Dynamic refetch interval based on session status
    refetchInterval: (query) => {
      const session = query.state.data;
      return getRefetchInterval(session?.status);
    },
  });

  return query;
}

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: ResearchConfig) => apiClient.createSession(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ 'sessions' ] });
    },
  });
}

export function useStartSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => apiClient.startSession(sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [ 'sessions' ] });
      queryClient.invalidateQueries({ queryKey: [ 'session', data.id ] });
    },
  });
}

export function usePauseSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => apiClient.pauseSession(sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [ 'sessions' ] });
      queryClient.invalidateQueries({ queryKey: [ 'session', data.id ] });
    },
  });
}

export function useStopSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => apiClient.stopSession(sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [ 'sessions' ] });
      queryClient.invalidateQueries({ queryKey: [ 'session', data.id ] });
    },
  });
}