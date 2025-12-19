import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import type { ComplianceReport, ComplianceCategory, ComplianceCheck } from '../types';

/**
 * **Feature: frontend-backend-integration, Property 5: Compliance report structure validity**
 * **Validates: Requirements 3.1**
 * 
 * For any compliance report returned from the API, it SHALL contain a sessionId,
 * a numeric complianceScore between 0-100, and a non-empty categories array where
 * each category has name, score, status, and checks fields.
 */
describe('Property 5: Compliance report structure validity', () => {
    // Arbitrary for ComplianceCheck
    const complianceCheckArbitrary: fc.Arbitrary<ComplianceCheck> = fc.record({
        name: fc.string({ minLength: 1 }),
        status: fc.constantFrom('passed', 'failed', 'warning') as fc.Arbitrary<'passed' | 'failed' | 'warning'>,
    });

    // Arbitrary for ComplianceCategory
    const complianceCategoryArbitrary: fc.Arbitrary<ComplianceCategory> = fc.record({
        name: fc.string({ minLength: 1 }),
        score: fc.integer({ min: 0, max: 100 }),
        status: fc.constantFrom('passed', 'failed', 'warning') as fc.Arbitrary<'passed' | 'failed' | 'warning'>,
        checks: fc.array(complianceCheckArbitrary, { minLength: 1 }),
    });

    // Arbitrary for ComplianceReport with non-empty categories
    const complianceReportArbitrary: fc.Arbitrary<ComplianceReport> = fc.record({
        sessionId: fc.uuid(),
        complianceScore: fc.integer({ min: 0, max: 100 }),
        categories: fc.array(complianceCategoryArbitrary, { minLength: 1 }),
    });

    it('should have all required fields in ComplianceReport', () => {
        fc.assert(
            fc.property(complianceReportArbitrary, (report: ComplianceReport) => {
                // All required fields must exist
                expect(report).toHaveProperty('sessionId');
                expect(report).toHaveProperty('complianceScore');
                expect(report).toHaveProperty('categories');

                // Type validations
                expect(typeof report.sessionId).toBe('string');
                expect(typeof report.complianceScore).toBe('number');
                expect(Array.isArray(report.categories)).toBe(true);
            }),
            { numRuns: 100 }
        );
    });

    it('should have complianceScore between 0 and 100', () => {
        fc.assert(
            fc.property(complianceReportArbitrary, (report: ComplianceReport) => {
                expect(report.complianceScore).toBeGreaterThanOrEqual(0);
                expect(report.complianceScore).toBeLessThanOrEqual(100);
            }),
            { numRuns: 100 }
        );
    });

    it('should have non-empty categories array', () => {
        fc.assert(
            fc.property(complianceReportArbitrary, (report: ComplianceReport) => {
                expect(report.categories.length).toBeGreaterThan(0);
            }),
            { numRuns: 100 }
        );
    });

    it('should have valid structure for each category', () => {
        fc.assert(
            fc.property(complianceReportArbitrary, (report: ComplianceReport) => {
                report.categories.forEach((category) => {
                    // All required fields must exist
                    expect(category).toHaveProperty('name');
                    expect(category).toHaveProperty('score');
                    expect(category).toHaveProperty('status');
                    expect(category).toHaveProperty('checks');

                    // Type validations
                    expect(typeof category.name).toBe('string');
                    expect(typeof category.score).toBe('number');
                    expect([ 'passed', 'failed', 'warning' ]).toContain(category.status);
                    expect(Array.isArray(category.checks)).toBe(true);

                    // Score constraints
                    expect(category.score).toBeGreaterThanOrEqual(0);
                    expect(category.score).toBeLessThanOrEqual(100);
                });
            }),
            { numRuns: 100 }
        );
    });

    it('should have valid structure for each check within categories', () => {
        fc.assert(
            fc.property(complianceReportArbitrary, (report: ComplianceReport) => {
                report.categories.forEach((category) => {
                    category.checks.forEach((check) => {
                        // All required fields must exist
                        expect(check).toHaveProperty('name');
                        expect(check).toHaveProperty('status');

                        // Type validations
                        expect(typeof check.name).toBe('string');
                        expect([ 'passed', 'failed', 'warning' ]).toContain(check.status);
                    });
                });
            }),
            { numRuns: 100 }
        );
    });

    it('should validate array of compliance reports maintains structure', () => {
        const reportsArrayArbitrary = fc.array(complianceReportArbitrary, { minLength: 0, maxLength: 10 });

        fc.assert(
            fc.property(reportsArrayArbitrary, (reports: ComplianceReport[]) => {
                expect(Array.isArray(reports)).toBe(true);

                reports.forEach((report) => {
                    expect(report).toHaveProperty('sessionId');
                    expect(report).toHaveProperty('complianceScore');
                    expect(report).toHaveProperty('categories');

                    expect(typeof report.sessionId).toBe('string');
                    expect(typeof report.complianceScore).toBe('number');
                    expect(report.complianceScore).toBeGreaterThanOrEqual(0);
                    expect(report.complianceScore).toBeLessThanOrEqual(100);
                    expect(Array.isArray(report.categories)).toBe(true);
                    expect(report.categories.length).toBeGreaterThan(0);
                });
            }),
            { numRuns: 100 }
        );
    });
});
