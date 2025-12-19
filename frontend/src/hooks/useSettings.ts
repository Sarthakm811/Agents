import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { UserSettings } from '@/types';

export function useSettings() {
    return useQuery<UserSettings>({
        queryKey: [ 'settings' ],
        queryFn: () => apiClient.getSettings(),
    });
}

export function useUpdateSettings() {
    const queryClient = useQueryClient();

    return useMutation<UserSettings, Error, UserSettings>({
        mutationFn: (settings: UserSettings) => apiClient.updateSettings(settings),
        onSuccess: (data) => {
            queryClient.setQueryData([ 'settings' ], data);
        },
    });
}
