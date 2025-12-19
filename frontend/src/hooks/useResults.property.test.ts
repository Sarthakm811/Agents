import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { filterSessionsByStatus } from './useResults';
import type { ResearchSession } from '../types';

/**
 * **Feature: frontend-backend-integration, Property 3: Session filtering by status**
 * **Validates: Requirements 2.1**
 * 
 * For any collection of sessions with mixed statuses, filtering by "completed" status
 * SHALL return only sessions where status equals "completed" and no sessions with other statuses.
 */
describe('Property 3: Session filtering by status', () => {
    // Arbitrary for session status
    const sessionStatusArbitrary = fc.constantFrom(
        'configuring',
        'running',
        'completed',
        'failed'
    ) as fc.Arbitrary<ResearchSession[ 'status' ]>;

    // Arbitrary for a minimal valid ResearchSession
    const researchSessionArbitrary = (status?: ResearchSession[ 'status' ]): fc.Arbitrary<ResearchSession> =>
        fc.record({
            id: fc.uuid(),
            config: fc.record({
                topic: fc.record({
                    title: fc.string({ minLength: 1 }),
                    domain: fc.string({ minLength: 1 }),
                    keywords: fc.array(fc.string(), { minLength: 1, maxLength: 5 }),
                    complexity: fc.constantFrom('basic', 'intermediate', 'advanced'),
                }),
                authorName: fc.string({ minLength: 1 }),
                authorInstitution: fc.string({ minLength: 1 }),
            }),
            status: status ? fc.constant(status) : sessionStatusArbitrary,
            stages: fc.array(
                fc.record({
                    id: fc.uuid(),
                    name: fc.string({ minLength: 1 }),
                    status: fc.constantFrom('pending', 'running', 'completed', 'failed'),
                    progress: fc.integer({ min: 0, max: 100 }),
                }),
                { minLength: 0, maxLength: 3 }
            ),
            metrics: fc.record({
                originalityScore: fc.integer({ min: 0, max: 100 }),
                noveltyScore: fc.integer({ min: 0, max: 100 }),
                plagiarismScore: fc.integer({ min: 0, max: 100 }),
                ethicsScore: fc.integer({ min: 0, max: 100 }),
                totalAgents: fc.integer({ min: 0, max: 10 }),
                activeAgents: fc.integer({ min: 0, max: 10 }),
                tasksCompleted: fc.integer({ min: 0, max: 100 }),
                apiCalls: fc.integer({ min: 0, max: 1000 }),
            }),
            agents: fc.array(
                fc.record({
                    id: fc.uuid(),
                    name: fc.string({ minLength: 1 }),
                    type: fc.string({ minLength: 1 }),
                    status: fc.constantFrom('idle', 'working', 'completed'),
                    tasksCompleted: fc.integer({ min: 0, max: 50 }),
                }),
                { minLength: 0, maxLength: 3 }
            ),
            createdAt: fc.integer({ min: 1577836800000, max: 1893456000000 }).map(ts => new Date(ts).toISOString()),
            updatedAt: fc.integer({ min: 1577836800000, max: 1893456000000 }).map(ts => new Date(ts).toISOString()),
        }) as fc.Arbitrary<ResearchSession>;

    // Arbitrary for array of sessions with mixed statuses
    const mixedSessionsArbitrary = fc.array(researchSessionArbitrary(), { minLength: 0, maxLength: 20 });

    it('should return only sessions with the specified status', () => {
        fc.assert(
            fc.property(mixedSessionsArbitrary, sessionStatusArbitrary, (sessions, targetStatus) => {
                const filtered = filterSessionsByStatus(sessions, targetStatus);

                // All returned sessions should have the target status
                for (const session of filtered) {
                    expect(session.status).toBe(targetStatus);
                }
            }),
            { numRuns: 100 }
        );
    });

    it('should not include sessions with different statuses', () => {
        fc.assert(
            fc.property(mixedSessionsArbitrary, sessionStatusArbitrary, (sessions, targetStatus) => {
                const filtered = filterSessionsByStatus(sessions, targetStatus);

                // No session in the result should have a different status
                const hasWrongStatus = filtered.some(session => session.status !== targetStatus);
                expect(hasWrongStatus).toBe(false);
            }),
            { numRuns: 100 }
        );
    });

    it('should return all sessions that match the target status', () => {
        fc.assert(
            fc.property(mixedSessionsArbitrary, sessionStatusArbitrary, (sessions, targetStatus) => {
                const filtered = filterSessionsByStatus(sessions, targetStatus);
                const expectedCount = sessions.filter(s => s.status === targetStatus).length;

                expect(filtered.length).toBe(expectedCount);
            }),
            { numRuns: 100 }
        );
    });

    it('should return empty array when no sessions match', () => {
        fc.assert(
            fc.property(
                fc.array(researchSessionArbitrary('running'), { minLength: 1, maxLength: 10 }),
                (runningSessions) => {
                    // Filter for 'completed' when all sessions are 'running'
                    const filtered = filterSessionsByStatus(runningSessions, 'completed');
                    expect(filtered.length).toBe(0);
                }
            ),
            { numRuns: 100 }
        );
    });

    it('should return all sessions when all match the target status', () => {
        fc.assert(
            fc.property(
                fc.array(researchSessionArbitrary('completed'), { minLength: 1, maxLength: 10 }),
                (completedSessions) => {
                    const filtered = filterSessionsByStatus(completedSessions, 'completed');
                    expect(filtered.length).toBe(completedSessions.length);
                }
            ),
            { numRuns: 100 }
        );
    });

    it('should handle empty session array', () => {
        const filtered = filterSessionsByStatus([], 'completed');
        expect(filtered).toEqual([]);
    });

    it('should preserve session data integrity after filtering', () => {
        fc.assert(
            fc.property(mixedSessionsArbitrary, (sessions) => {
                const filtered = filterSessionsByStatus(sessions, 'completed');

                // Each filtered session should be identical to its original
                for (const filteredSession of filtered) {
                    const original = sessions.find(s => s.id === filteredSession.id);
                    expect(original).toBeDefined();
                    expect(filteredSession).toEqual(original);
                }
            }),
            { numRuns: 100 }
        );
    });

    it('should filter completed sessions correctly for Results page use case', () => {
        fc.assert(
            fc.property(mixedSessionsArbitrary, (sessions) => {
                const completedSessions = filterSessionsByStatus(sessions, 'completed');

                // Verify the specific use case: filtering for completed sessions
                // should only return sessions that are ready for viewing/downloading
                for (const session of completedSessions) {
                    expect(session.status).toBe('completed');
                }

                // Verify no running, failed, or configuring sessions are included
                const hasNonCompleted = completedSessions.some(
                    s => s.status === 'running' || s.status === 'failed' || s.status === 'configuring'
                );
                expect(hasNonCompleted).toBe(false);
            }),
            { numRuns: 100 }
        );
    });
});
