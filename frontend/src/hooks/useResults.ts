import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { ResearchSession, ResearchResults } from '@/types';

/**
 * Filters sessions by status.
 * Pure function for testability.
 */
export function filterSessionsByStatus(
    sessions: ResearchSession[],
    status: ResearchSession[ 'status' ]
): ResearchSession[] {
    return sessions.filter((session) => session.status === status);
}

export function useCompletedSessions() {
    return useQuery<ResearchSession[]>({
        queryKey: [ 'sessions', 'completed' ],
        queryFn: async () => {
            const sessions = await apiClient.listSessions();
            return filterSessionsByStatus(sessions, 'completed');
        },
    });
}

export function useSessionResults(sessionId: string) {
    return useQuery<ResearchResults>({
        queryKey: [ 'results', sessionId ],
        queryFn: () => apiClient.getResults(sessionId) as Promise<ResearchResults>,
        enabled: !!sessionId,
    });
}

export function useDownloadPaper() {
    return useMutation<Blob, Error, { sessionId: string; format: 'pdf' | 'latex' }>({
        mutationFn: ({ sessionId, format }) => apiClient.downloadPaper(sessionId, format),
        onSuccess: (blob, { sessionId, format }) => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `paper-${sessionId}.${format === 'pdf' ? 'pdf' : 'tex'}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        },
    });
}
