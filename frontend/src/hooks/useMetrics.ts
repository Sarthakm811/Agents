import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { OverallMetrics, ResearchMetrics } from '@/types';

export function useOverallMetrics() {
    return useQuery<OverallMetrics>({
        queryKey: [ 'metrics', 'overall' ],
        queryFn: () => apiClient.getOverallMetrics(),
    });
}

export function useSessionMetrics(sessionId: string) {
    return useQuery<ResearchMetrics>({
        queryKey: [ 'metrics', 'session', sessionId ],
        queryFn: () => apiClient.getMetrics(sessionId),
        enabled: !!sessionId,
    });
}
