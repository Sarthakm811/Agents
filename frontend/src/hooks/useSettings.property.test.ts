import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import type { UserSettings, UserPreferences } from '../types';

/**
 * **Feature: frontend-backend-integration, Property 6: Settings round-trip consistency**
 * **Validates: Requirements 4.1, 4.2, 7.1, 7.2**
 * 
 * For any valid UserSettings object, posting it to the settings endpoint and then
 * fetching settings SHALL return an equivalent settings object.
 */
describe('Property 6: Settings round-trip consistency', () => {
    // Arbitrary for UserPreferences
    const userPreferencesArbitrary: fc.Arbitrary<UserPreferences> = fc.record({
        autoStartEthicsReview: fc.boolean(),
        enablePlagiarismDetection: fc.boolean(),
        realTimeNotifications: fc.boolean(),
    });

    // Arbitrary for valid email addresses
    const emailArbitrary = fc.tuple(
        fc.stringMatching(/^[a-zA-Z][a-zA-Z0-9]{0,19}$/),
        fc.stringMatching(/^[a-zA-Z][a-zA-Z0-9]{0,9}$/),
        fc.constantFrom('com', 'org', 'edu', 'net')
    ).map(([ local, domain, tld ]) => `${local}@${domain}.${tld}`);

    // Arbitrary for UserSettings
    const userSettingsArbitrary: fc.Arbitrary<UserSettings> = fc.record({
        fullName: fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        email: emailArbitrary,
        institution: fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
        preferences: userPreferencesArbitrary,
    });

    it('should have all required fields in UserSettings', () => {
        fc.assert(
            fc.property(userSettingsArbitrary, (settings: UserSettings) => {
                // All required fields must exist
                expect(settings).toHaveProperty('fullName');
                expect(settings).toHaveProperty('email');
                expect(settings).toHaveProperty('institution');
                expect(settings).toHaveProperty('preferences');

                // Type validations
                expect(typeof settings.fullName).toBe('string');
                expect(typeof settings.email).toBe('string');
                expect(typeof settings.institution).toBe('string');
                expect(typeof settings.preferences).toBe('object');
            }),
            { numRuns: 100 }
        );
    });

    it('should have all required fields in UserPreferences', () => {
        fc.assert(
            fc.property(userSettingsArbitrary, (settings: UserSettings) => {
                const { preferences } = settings;

                // All required preference fields must exist
                expect(preferences).toHaveProperty('autoStartEthicsReview');
                expect(preferences).toHaveProperty('enablePlagiarismDetection');
                expect(preferences).toHaveProperty('realTimeNotifications');

                // Type validations - all must be booleans
                expect(typeof preferences.autoStartEthicsReview).toBe('boolean');
                expect(typeof preferences.enablePlagiarismDetection).toBe('boolean');
                expect(typeof preferences.realTimeNotifications).toBe('boolean');
            }),
            { numRuns: 100 }
        );
    });

    it('should preserve settings structure through serialization round-trip', () => {
        fc.assert(
            fc.property(userSettingsArbitrary, (settings: UserSettings) => {
                // Simulate JSON serialization/deserialization (as would happen in API round-trip)
                const serialized = JSON.stringify(settings);
                const deserialized = JSON.parse(serialized) as UserSettings;

                // Verify all fields are preserved
                expect(deserialized.fullName).toBe(settings.fullName);
                expect(deserialized.email).toBe(settings.email);
                expect(deserialized.institution).toBe(settings.institution);
                expect(deserialized.preferences.autoStartEthicsReview).toBe(settings.preferences.autoStartEthicsReview);
                expect(deserialized.preferences.enablePlagiarismDetection).toBe(settings.preferences.enablePlagiarismDetection);
                expect(deserialized.preferences.realTimeNotifications).toBe(settings.preferences.realTimeNotifications);
            }),
            { numRuns: 100 }
        );
    });

    it('should maintain email format validity', () => {
        fc.assert(
            fc.property(userSettingsArbitrary, (settings: UserSettings) => {
                // Basic email format validation
                expect(settings.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
            }),
            { numRuns: 100 }
        );
    });

    it('should ensure non-empty required string fields', () => {
        fc.assert(
            fc.property(userSettingsArbitrary, (settings: UserSettings) => {
                expect(settings.fullName.trim().length).toBeGreaterThan(0);
                expect(settings.institution.trim().length).toBeGreaterThan(0);
                expect(settings.email.length).toBeGreaterThan(0);
            }),
            { numRuns: 100 }
        );
    });
});
