import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { ComplianceReport } from '@/types';

export function useComplianceReport(sessionId: string) {
    return useQuery<ComplianceReport>({
        queryKey: [ 'compliance', sessionId ],
        queryFn: () => apiClient.getComplianceReport(sessionId),
        enabled: !!sessionId,
    });
}

export function useAllComplianceReports() {
    return useQuery<ComplianceReport[]>({
        queryKey: [ 'compliance', 'all' ],
        queryFn: () => apiClient.getAllComplianceReports(),
    });
}
