/**
 * Error handling utility for API interactions
 * **Feature: frontend-backend-integration, Property 4: Error classification consistency**
 */

export type ErrorType = 'network' | 'client' | 'server';

export interface ApiError {
    type: ErrorType;
    message: string;
    statusCode?: number;
    details?: unknown;
    retryable: boolean;
}

export interface RecoveryAction {
    label: string;
    action: 'retry' | 'refresh' | 'contact-support' | 'check-input';
    description: string;
}

/**
 * Parses an unknown error into a structured ApiError object.
 * Classifies errors as 'network' (connection failures), 'client' (4xx), or 'server' (5xx).
 */
export function parseApiError(error: unknown): ApiError {
    // Network errors (fetch failures, connection issues)
    if (error instanceof TypeError) {
        return {
            type: 'network',
            message: 'Unable to connect to server. Please check your internet connection.',
            retryable: true,
        };
    }

    // Handle Response objects directly (for cases where response is thrown)
    if (error instanceof Response) {
        return classifyByStatusCode(error.status, error.statusText);
    }

    // Handle errors with status property (custom error objects)
    if (isErrorWithStatus(error)) {
        return classifyByStatusCode(error.status, error.message);
    }

    // Handle standard Error objects with HTTP status in message
    if (error instanceof Error) {
        const statusMatch = error.message.match(/HTTP (\d{3})/);
        if (statusMatch) {
            const statusCode = parseInt(statusMatch[ 1 ], 10);
            return classifyByStatusCode(statusCode, error.message);
        }

        // Check for network-related error messages
        if (
            error.message.includes('fetch') ||
            error.message.includes('network') ||
            error.message.includes('Failed to fetch') ||
            error.message.includes('NetworkError')
        ) {
            return {
                type: 'network',
                message: 'Unable to connect to server. Please check your internet connection.',
                retryable: true,
            };
        }

        // Default to server error for unknown Error instances
        return {
            type: 'server',
            message: error.message || 'An unexpected error occurred',
            retryable: true,
            details: error,
        };
    }

    // Fallback for completely unknown error types
    return {
        type: 'server',
        message: 'An unexpected error occurred',
        retryable: false,
        details: error,
    };
}

/**
 * Type guard to check if error has a status property
 */
function isErrorWithStatus(error: unknown): error is { status: number; message?: string } {
    return (
        typeof error === 'object' &&
        error !== null &&
        'status' in error &&
        typeof (error as { status: unknown }).status === 'number'
    );
}

/**
 * Classifies an error based on HTTP status code
 */
function classifyByStatusCode(statusCode: number, message?: string): ApiError {
    if (statusCode >= 400 && statusCode < 500) {
        return {
            type: 'client',
            message: message || getDefaultClientErrorMessage(statusCode),
            statusCode,
            retryable: false,
        };
    }

    if (statusCode >= 500) {
        return {
            type: 'server',
            message: 'A server error occurred. Please try again later.',
            statusCode,
            retryable: true,
        };
    }

    // For non-error status codes (shouldn't happen, but handle gracefully)
    return {
        type: 'server',
        message: message || 'An unexpected error occurred',
        statusCode,
        retryable: false,
    };
}

/**
 * Returns a default user-friendly message for common client error status codes
 */
function getDefaultClientErrorMessage(statusCode: number): string {
    switch (statusCode) {
        case 400:
            return 'Invalid request. Please check your input and try again.';
        case 401:
            return 'Authentication required. Please log in and try again.';
        case 403:
            return 'You do not have permission to perform this action.';
        case 404:
            return 'The requested resource was not found.';
        case 409:
            return 'A conflict occurred. The resource may have been modified.';
        case 422:
            return 'The provided data is invalid. Please check your input.';
        case 429:
            return 'Too many requests. Please wait a moment and try again.';
        default:
            return 'A request error occurred. Please check your input.';
    }
}

/**
 * Returns a user-friendly error message based on the ApiError type.
 */
export function getErrorMessage(error: ApiError): string {
    switch (error.type) {
        case 'network':
            return 'Unable to connect to the server. Please check your internet connection and try again.';
        case 'client':
            return error.message;
        case 'server':
            return 'A server error occurred. Our team has been notified. Please try again later.';
        default:
            return 'An unexpected error occurred. Please try again.';
    }
}

/**
 * Returns a contextual recovery action based on the error type.
 * Returns null if no recovery action is applicable.
 */
export function getRecoveryAction(error: ApiError): RecoveryAction | null {
    switch (error.type) {
        case 'network':
            return {
                label: 'Retry',
                action: 'retry',
                description: 'Check your connection and try again',
            };
        case 'client':
            // For client errors, suggest checking input for validation errors
            if (error.statusCode === 400 || error.statusCode === 422) {
                return {
                    label: 'Check Input',
                    action: 'check-input',
                    description: 'Review your input and correct any errors',
                };
            }
            // For 404, suggest refreshing
            if (error.statusCode === 404) {
                return {
                    label: 'Refresh',
                    action: 'refresh',
                    description: 'Refresh the page to see the latest data',
                };
            }
            // For rate limiting, suggest retry
            if (error.statusCode === 429) {
                return {
                    label: 'Retry',
                    action: 'retry',
                    description: 'Wait a moment and try again',
                };
            }
            return null;
        case 'server':
            return {
                label: 'Retry',
                action: 'retry',
                description: 'The server encountered an error. Try again.',
            };
        default:
            return null;
    }
}
