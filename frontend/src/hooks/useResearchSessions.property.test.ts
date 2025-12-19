import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { shouldPoll, isTerminalStatus, getRefetchInterval } from './useResearchSessions';
import type { ResearchSession } from '../types';

/**
 * **Feature: frontend-backend-integration, Property 7: Polling termination on terminal status**
 * **Validates: Requirements 5.1, 5.3, 5.4**
 * 
 * For any research session, the polling mechanism SHALL continue while status is "running"
 * and SHALL stop when status transitions to either "completed" or "failed".
 */
describe('Property 7: Polling termination on terminal status', () => {
    // Arbitrary for session status
    const sessionStatusArbitrary = fc.constantFrom(
        'configuring',
        'running',
        'completed',
        'failed'
    ) as fc.Arbitrary<ResearchSession[ 'status' ]>;

    // Terminal statuses that should stop polling
    const terminalStatusArbitrary = fc.constantFrom(
        'completed',
        'failed'
    ) as fc.Arbitrary<ResearchSession[ 'status' ]>;

    // Non-terminal statuses
    const nonTerminalStatusArbitrary = fc.constantFrom(
        'configuring',
        'running'
    ) as fc.Arbitrary<ResearchSession[ 'status' ]>;

    // Running status only
    const runningStatusArbitrary = fc.constant('running') as fc.Arbitrary<ResearchSession[ 'status' ]>;

    it('should enable polling only when status is "running"', () => {
        fc.assert(
            fc.property(sessionStatusArbitrary, (status) => {
                const shouldPollResult = shouldPoll(status);

                if (status === 'running') {
                    expect(shouldPollResult).toBe(true);
                } else {
                    expect(shouldPollResult).toBe(false);
                }
            }),
            { numRuns: 100 }
        );
    });

    it('should stop polling when status is "completed"', () => {
        fc.assert(
            fc.property(fc.constant('completed'), (status: ResearchSession[ 'status' ]) => {
                expect(shouldPoll(status)).toBe(false);
                expect(isTerminalStatus(status)).toBe(true);
                expect(getRefetchInterval(status)).toBe(false);
            }),
            { numRuns: 100 }
        );
    });

    it('should stop polling when status is "failed"', () => {
        fc.assert(
            fc.property(fc.constant('failed'), (status: ResearchSession[ 'status' ]) => {
                expect(shouldPoll(status)).toBe(false);
                expect(isTerminalStatus(status)).toBe(true);
                expect(getRefetchInterval(status)).toBe(false);
            }),
            { numRuns: 100 }
        );
    });

    it('should correctly identify terminal statuses', () => {
        fc.assert(
            fc.property(terminalStatusArbitrary, (status) => {
                expect(isTerminalStatus(status)).toBe(true);
            }),
            { numRuns: 100 }
        );
    });

    it('should correctly identify non-terminal statuses', () => {
        fc.assert(
            fc.property(nonTerminalStatusArbitrary, (status) => {
                expect(isTerminalStatus(status)).toBe(false);
            }),
            { numRuns: 100 }
        );
    });

    it('should return polling interval only for running status', () => {
        fc.assert(
            fc.property(runningStatusArbitrary, (status) => {
                const interval = getRefetchInterval(status);
                expect(typeof interval).toBe('number');
                expect(interval).toBeGreaterThan(0);
            }),
            { numRuns: 100 }
        );
    });

    it('should return false for refetch interval on terminal statuses', () => {
        fc.assert(
            fc.property(terminalStatusArbitrary, (status) => {
                expect(getRefetchInterval(status)).toBe(false);
            }),
            { numRuns: 100 }
        );
    });

    it('should handle undefined status gracefully', () => {
        expect(shouldPoll(undefined)).toBe(false);
        expect(isTerminalStatus(undefined)).toBe(false);
        expect(getRefetchInterval(undefined)).toBe(false);
    });

    it('should maintain consistency: running status enables polling, terminal statuses disable it', () => {
        fc.assert(
            fc.property(sessionStatusArbitrary, (status) => {
                const polls = shouldPoll(status);
                const isTerminal = isTerminalStatus(status);
                const interval = getRefetchInterval(status);

                // If terminal, should not poll
                if (isTerminal) {
                    expect(polls).toBe(false);
                    expect(interval).toBe(false);
                }

                // If polling, should not be terminal
                if (polls) {
                    expect(isTerminal).toBe(false);
                    expect(typeof interval).toBe('number');
                }

                // Running is the only status that enables polling
                if (status === 'running') {
                    expect(polls).toBe(true);
                }
            }),
            { numRuns: 100 }
        );
    });
});
