import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import type { OverallMetrics, ResearchSession } from '../types';

/**
 * **Feature: frontend-backend-integration, Property 1: Metrics API returns valid structure**
 * **Validates: Requirements 1.1**
 * 
 * For any call to the metrics endpoint, the response SHALL contain all required fields
 * (totalSessions, activeSessions, completedSessions, avgOriginalityScore, totalAgents, activeAgents)
 * with numeric values.
 */
describe('Property 1: Metrics API returns valid structure', () => {
    // Arbitrary for generating valid OverallMetrics objects
    const overallMetricsArbitrary = fc.record({
        totalSessions: fc.nat(),
        activeSessions: fc.nat(),
        completedSessions: fc.nat(),
        avgOriginalityScore: fc.float({ min: 0, max: 100, noNaN: true }),
        totalAgents: fc.nat(),
        activeAgents: fc.nat(),
    });

    it('should have all required numeric fields in OverallMetrics', () => {
        fc.assert(
            fc.property(overallMetricsArbitrary, (metrics: OverallMetrics) => {
                // All required fields must exist
                expect(metrics).toHaveProperty('totalSessions');
                expect(metrics).toHaveProperty('activeSessions');
                expect(metrics).toHaveProperty('completedSessions');
                expect(metrics).toHaveProperty('avgOriginalityScore');
                expect(metrics).toHaveProperty('totalAgents');
                expect(metrics).toHaveProperty('activeAgents');

                // All fields must be numeric
                expect(typeof metrics.totalSessions).toBe('number');
                expect(typeof metrics.activeSessions).toBe('number');
                expect(typeof metrics.completedSessions).toBe('number');
                expect(typeof metrics.avgOriginalityScore).toBe('number');
                expect(typeof metrics.totalAgents).toBe('number');
                expect(typeof metrics.activeAgents).toBe('number');

                // Non-negative constraints
                expect(metrics.totalSessions).toBeGreaterThanOrEqual(0);
                expect(metrics.activeSessions).toBeGreaterThanOrEqual(0);
                expect(metrics.completedSessions).toBeGreaterThanOrEqual(0);
                expect(metrics.totalAgents).toBeGreaterThanOrEqual(0);
                expect(metrics.activeAgents).toBeGreaterThanOrEqual(0);
            }),
            { numRuns: 100 }
        );
    });

    it('should maintain logical consistency: activeSessions <= totalSessions', () => {
        const consistentMetricsArbitrary = fc.nat().chain((total) =>
            fc.record({
                totalSessions: fc.constant(total),
                activeSessions: fc.nat({ max: total }),
                completedSessions: fc.nat({ max: total }),
                avgOriginalityScore: fc.float({ min: 0, max: 100, noNaN: true }),
                totalAgents: fc.nat(),
                activeAgents: fc.nat(),
            })
        );

        fc.assert(
            fc.property(consistentMetricsArbitrary, (metrics: OverallMetrics) => {
                expect(metrics.activeSessions).toBeLessThanOrEqual(metrics.totalSessions);
                expect(metrics.completedSessions).toBeLessThanOrEqual(metrics.totalSessions);
            }),
            { numRuns: 100 }
        );
    });
});

/**
 * **Feature: frontend-backend-integration, Property 2: Sessions API returns valid session objects**
 * **Validates: Requirements 1.2**
 * 
 * For any call to the sessions endpoint, each session in the response SHALL contain all required fields
 * (id, config, status, stages, metrics, agents, createdAt, updatedAt) matching the ResearchSession type.
 */
describe('Property 2: Sessions API returns valid session objects', () => {
    // Arbitrary for ResearchTopic
    const researchTopicArbitrary = fc.record({
        title: fc.string({ minLength: 1 }),
        domain: fc.string({ minLength: 1 }),
        keywords: fc.array(fc.string(), { minLength: 1 }),
        complexity: fc.constantFrom('basic', 'intermediate', 'advanced') as fc.Arbitrary<'basic' | 'intermediate' | 'advanced'>,
    });

    // Arbitrary for ResearchConfig
    const researchConfigArbitrary = fc.record({
        topic: researchTopicArbitrary,
        authorName: fc.string({ minLength: 1 }),
        authorInstitution: fc.string({ minLength: 1 }),
    });

    // Arbitrary for ResearchMetrics
    const researchMetricsArbitrary = fc.record({
        originalityScore: fc.float({ min: 0, max: 100, noNaN: true }),
        noveltyScore: fc.float({ min: 0, max: 100, noNaN: true }),
        plagiarismScore: fc.float({ min: 0, max: 100, noNaN: true }),
        ethicsScore: fc.float({ min: 0, max: 100, noNaN: true }),
        totalAgents: fc.nat(),
        activeAgents: fc.nat(),
        tasksCompleted: fc.nat(),
        apiCalls: fc.nat(),
    });

    // Arbitrary for ResearchStage
    const researchStageArbitrary = fc.record({
        id: fc.uuid(),
        name: fc.string({ minLength: 1 }),
        status: fc.constantFrom('pending', 'running', 'completed', 'failed') as fc.Arbitrary<'pending' | 'running' | 'completed' | 'failed'>,
        progress: fc.float({ min: 0, max: 100, noNaN: true }),
    });

    // Arbitrary for AgentActivity
    const agentActivityArbitrary = fc.record({
        id: fc.uuid(),
        name: fc.string({ minLength: 1 }),
        type: fc.string({ minLength: 1 }),
        status: fc.constantFrom('idle', 'working', 'completed') as fc.Arbitrary<'idle' | 'working' | 'completed'>,
        tasksCompleted: fc.nat(),
    });

    // Arbitrary for valid ISO date strings (using timestamp range to avoid invalid dates)
    const validIsoDateArbitrary = fc.integer({
        min: new Date('2020-01-01').getTime(),
        max: new Date('2030-12-31').getTime()
    }).map((timestamp) => new Date(timestamp).toISOString());

    // Arbitrary for ResearchSession
    const researchSessionArbitrary = fc.record({
        id: fc.uuid(),
        config: researchConfigArbitrary,
        status: fc.constantFrom('configuring', 'running', 'completed', 'failed') as fc.Arbitrary<'configuring' | 'running' | 'completed' | 'failed'>,
        stages: fc.array(researchStageArbitrary),
        metrics: researchMetricsArbitrary,
        agents: fc.array(agentActivityArbitrary),
        createdAt: validIsoDateArbitrary,
        updatedAt: validIsoDateArbitrary,
    });

    it('should have all required fields in ResearchSession', () => {
        fc.assert(
            fc.property(researchSessionArbitrary, (session: ResearchSession) => {
                // All required fields must exist
                expect(session).toHaveProperty('id');
                expect(session).toHaveProperty('config');
                expect(session).toHaveProperty('status');
                expect(session).toHaveProperty('stages');
                expect(session).toHaveProperty('metrics');
                expect(session).toHaveProperty('agents');
                expect(session).toHaveProperty('createdAt');
                expect(session).toHaveProperty('updatedAt');

                // Type validations
                expect(typeof session.id).toBe('string');
                expect(typeof session.config).toBe('object');
                expect([ 'configuring', 'running', 'completed', 'failed' ]).toContain(session.status);
                expect(Array.isArray(session.stages)).toBe(true);
                expect(typeof session.metrics).toBe('object');
                expect(Array.isArray(session.agents)).toBe(true);
                expect(typeof session.createdAt).toBe('string');
                expect(typeof session.updatedAt).toBe('string');
            }),
            { numRuns: 100 }
        );
    });

    it('should have valid config structure in ResearchSession', () => {
        fc.assert(
            fc.property(researchSessionArbitrary, (session: ResearchSession) => {
                const { config } = session;

                expect(config).toHaveProperty('topic');
                expect(config).toHaveProperty('authorName');
                expect(config).toHaveProperty('authorInstitution');

                expect(config.topic).toHaveProperty('title');
                expect(config.topic).toHaveProperty('domain');
                expect(config.topic).toHaveProperty('keywords');
                expect(config.topic).toHaveProperty('complexity');

                expect([ 'basic', 'intermediate', 'advanced' ]).toContain(config.topic.complexity);
                expect(Array.isArray(config.topic.keywords)).toBe(true);
            }),
            { numRuns: 100 }
        );
    });

    it('should have valid metrics structure in ResearchSession', () => {
        fc.assert(
            fc.property(researchSessionArbitrary, (session: ResearchSession) => {
                const { metrics } = session;

                expect(metrics).toHaveProperty('originalityScore');
                expect(metrics).toHaveProperty('noveltyScore');
                expect(metrics).toHaveProperty('plagiarismScore');
                expect(metrics).toHaveProperty('ethicsScore');
                expect(metrics).toHaveProperty('totalAgents');
                expect(metrics).toHaveProperty('activeAgents');
                expect(metrics).toHaveProperty('tasksCompleted');
                expect(metrics).toHaveProperty('apiCalls');

                // All numeric
                expect(typeof metrics.originalityScore).toBe('number');
                expect(typeof metrics.noveltyScore).toBe('number');
                expect(typeof metrics.plagiarismScore).toBe('number');
                expect(typeof metrics.ethicsScore).toBe('number');
                expect(typeof metrics.totalAgents).toBe('number');
                expect(typeof metrics.activeAgents).toBe('number');
                expect(typeof metrics.tasksCompleted).toBe('number');
                expect(typeof metrics.apiCalls).toBe('number');
            }),
            { numRuns: 100 }
        );
    });

    it('should validate array of sessions maintains structure', () => {
        const sessionsArrayArbitrary = fc.array(researchSessionArbitrary, { minLength: 0, maxLength: 10 });

        fc.assert(
            fc.property(sessionsArrayArbitrary, (sessions: ResearchSession[]) => {
                expect(Array.isArray(sessions)).toBe(true);

                sessions.forEach((session) => {
                    expect(session).toHaveProperty('id');
                    expect(session).toHaveProperty('config');
                    expect(session).toHaveProperty('status');
                    expect(session).toHaveProperty('stages');
                    expect(session).toHaveProperty('metrics');
                    expect(session).toHaveProperty('agents');
                    expect(session).toHaveProperty('createdAt');
                    expect(session).toHaveProperty('updatedAt');
                });
            }),
            { numRuns: 100 }
        );
    });
});
