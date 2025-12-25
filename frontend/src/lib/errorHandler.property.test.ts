import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import {
    parseApiError,
    getErrorMessage,
    getRecoveryAction,
    type ErrorType,
} from './errorHandler';

/**
 * **Feature: frontend-backend-integration, Property 4: Error classification consistency**
 * **Validates: Requirements 1.4, 6.1, 6.2, 6.3, 6.4**
 *
 * For any API error, the error handler SHALL classify it as exactly one of:
 * 'network' (for connection failures), 'client' (for 4xx status codes),
 * or 'server' (for 5xx status codes), and SHALL return an appropriate
 * user-friendly message for each type.
 */
describe('Property 4: Error classification consistency', () => {
    // Arbitrary for 4xx client error status codes
    const clientStatusCodeArbitrary = fc.integer({ min: 400, max: 499 });

    // Arbitrary for 5xx server error status codes
    const serverStatusCodeArbitrary = fc.integer({ min: 500, max: 599 });

    // Arbitrary for network error messages
    const networkErrorMessageArbitrary = fc.constantFrom(
        'Failed to fetch',
        'NetworkError when attempting to fetch resource',
        'fetch failed',
        'network error'
    );

    // Arbitrary for error objects with status property
    const errorWithStatusArbitrary = (statusCode: fc.Arbitrary<number>) =>
        fc.record({
            status: statusCode,
            message: fc.string(),
        });

    it('should classify TypeError as network error', () => {
        fc.assert(
            fc.property(fc.string(), (message) => {
                const error = new TypeError(message);
                const result = parseApiError(error);

                expect(result.type).toBe('network');
                expect(result.retryable).toBe(true);
                expect(typeof result.message).toBe('string');
                expect(result.message.length).toBeGreaterThan(0);
            }),
            { numRuns: 100 }
        );
    });

    it('should classify errors with network-related messages as network errors', () => {
        fc.assert(
            fc.property(networkErrorMessageArbitrary, (message) => {
                const error = new Error(message);
                const result = parseApiError(error);

                expect(result.type).toBe('network');
                expect(result.retryable).toBe(true);
            }),
            { numRuns: 100 }
        );
    });

    it('should classify 4xx status codes as client errors', () => {
        fc.assert(
            fc.property(
                errorWithStatusArbitrary(clientStatusCodeArbitrary),
                (errorObj) => {
                    const result = parseApiError(errorObj);

                    expect(result.type).toBe('client');
                    expect(result.statusCode).toBe(errorObj.status);
                    expect(result.retryable).toBe(false);
                    expect(typeof result.message).toBe('string');
                    expect(result.message.length).toBeGreaterThan(0);
                }
            ),
            { numRuns: 100 }
        );
    });

    it('should classify 5xx status codes as server errors', () => {
        fc.assert(
            fc.property(
                errorWithStatusArbitrary(serverStatusCodeArbitrary),
                (errorObj) => {
                    const result = parseApiError(errorObj);

                    expect(result.type).toBe('server');
                    expect(result.statusCode).toBe(errorObj.status);
                    expect(result.retryable).toBe(true);
                    expect(typeof result.message).toBe('string');
                    expect(result.message.length).toBeGreaterThan(0);
                }
            ),
            { numRuns: 100 }
        );
    });

    it('should classify errors with HTTP status in message correctly', () => {
        fc.assert(
            fc.property(clientStatusCodeArbitrary, (statusCode) => {
                const error = new Error(`HTTP ${statusCode}: Bad Request`);
                const result = parseApiError(error);

                expect(result.type).toBe('client');
                expect(result.statusCode).toBe(statusCode);
                expect(result.retryable).toBe(false);
            }),
            { numRuns: 100 }
        );

        fc.assert(
            fc.property(serverStatusCodeArbitrary, (statusCode) => {
                const error = new Error(`HTTP ${statusCode}: Internal Server Error`);
                const result = parseApiError(error);

                expect(result.type).toBe('server');
                expect(result.statusCode).toBe(statusCode);
                expect(result.retryable).toBe(true);
            }),
            { numRuns: 100 }
        );
    });

    it('should always return exactly one error type', () => {
        const validErrorTypes: ErrorType[] = [ 'network', 'client', 'server' ];

        // Test with various error inputs
        const errorInputArbitrary = fc.oneof(
            // TypeError (network)
            fc.string().map((msg) => new TypeError(msg)),
            // Error with HTTP status
            fc.integer({ min: 400, max: 599 }).map((code) => new Error(`HTTP ${code}: Error`)),
            // Error object with status
            fc.integer({ min: 400, max: 599 }).map((status) => ({ status, message: 'Error' })),
            // Generic Error
            fc.string().map((msg) => new Error(msg))
        );

        fc.assert(
            fc.property(errorInputArbitrary, (error) => {
                const result = parseApiError(error);

                // Must be exactly one of the valid types
                expect(validErrorTypes).toContain(result.type);

                // Count how many types match (should be exactly 1)
                const matchCount = validErrorTypes.filter((t) => t === result.type).length;
                expect(matchCount).toBe(1);
            }),
            { numRuns: 100 }
        );
    });

    it('should always return a non-empty user-friendly message', () => {
        const errorInputArbitrary = fc.oneof(
            fc.string().map((msg) => new TypeError(msg)),
            fc.integer({ min: 400, max: 599 }).map((code) => new Error(`HTTP ${code}: Error`)),
            fc.integer({ min: 400, max: 599 }).map((status) => ({ status, message: 'Error' })),
            fc.string().map((msg) => new Error(msg))
        );

        fc.assert(
            fc.property(errorInputArbitrary, (error) => {
                const apiError = parseApiError(error);
                const message = getErrorMessage(apiError);

                expect(typeof message).toBe('string');
                expect(message.length).toBeGreaterThan(0);
            }),
            { numRuns: 100 }
        );
    });

    it('should provide recovery action for retryable errors', () => {
        // Network errors should always have retry action
        fc.assert(
            fc.property(fc.string(), (message) => {
                const error = new TypeError(message);
                const apiError = parseApiError(error);
                const recovery = getRecoveryAction(apiError);

                expect(apiError.retryable).toBe(true);
                expect(recovery).not.toBeNull();
                expect(recovery?.action).toBe('retry');
            }),
            { numRuns: 100 }
        );

        // Server errors should always have retry action
        fc.assert(
            fc.property(serverStatusCodeArbitrary, (statusCode) => {
                const error = { status: statusCode, message: 'Server Error' };
                const apiError = parseApiError(error);
                const recovery = getRecoveryAction(apiError);

                expect(apiError.retryable).toBe(true);
                expect(recovery).not.toBeNull();
                expect(recovery?.action).toBe('retry');
            }),
            { numRuns: 100 }
        );
    });

    it('should return appropriate recovery actions for client errors', () => {
        // 400 and 422 should suggest checking input
        fc.assert(
            fc.property(fc.constantFrom(400, 422), (statusCode) => {
                const error = { status: statusCode, message: 'Validation Error' };
                const apiError = parseApiError(error);
                const recovery = getRecoveryAction(apiError);

                expect(recovery).not.toBeNull();
                expect(recovery?.action).toBe('check-input');
            }),
            { numRuns: 100 }
        );

        // 404 should suggest refresh
        const error404 = { status: 404, message: 'Not Found' };
        const apiError404 = parseApiError(error404);
        const recovery404 = getRecoveryAction(apiError404);
        expect(recovery404?.action).toBe('refresh');

        // 429 should suggest retry
        const error429 = { status: 429, message: 'Too Many Requests' };
        const apiError429 = parseApiError(error429);
        const recovery429 = getRecoveryAction(apiError429);
        expect(recovery429?.action).toBe('retry');
    });

    it('should maintain consistency between error type and retryable flag', () => {
        const errorInputArbitrary = fc.oneof(
            fc.string().map((msg) => new TypeError(msg)),
            fc.integer({ min: 400, max: 599 }).map((code) => new Error(`HTTP ${code}: Error`)),
            fc.integer({ min: 400, max: 599 }).map((status) => ({ status, message: 'Error' }))
        );

        fc.assert(
            fc.property(errorInputArbitrary, (error) => {
                const result = parseApiError(error);

                // Network errors are always retryable
                if (result.type === 'network') {
                    expect(result.retryable).toBe(true);
                }

                // Client errors are never retryable
                if (result.type === 'client') {
                    expect(result.retryable).toBe(false);
                }

                // Server errors are always retryable
                if (result.type === 'server' && result.statusCode !== undefined) {
                    expect(result.retryable).toBe(true);
                }
            }),
            { numRuns: 100 }
        );
    });
});
