# Implementation Plan

- [x] 1. Extend frontend types and API client





  - [x] 1.1 Add new TypeScript types for metrics, settings, compliance, and results


    - Add OverallMetrics, UserSettings, UserPreferences, ComplianceReport, ComplianceCategory, ComplianceCheck, ResearchResults, PaperDetails interfaces to `frontend/src/types/index.ts`
    - _Requirements: 1.1, 3.1, 4.1, 7.1_

  - [x] 1.2 Extend API client with new methods

    - Add getOverallMetrics(), getSettings(), updateSettings(), getAllComplianceReports() methods to `frontend/src/lib/api.ts`
    - _Requirements: 1.1, 3.1, 4.1, 4.2, 7.1, 7.2_
  - [x] 1.3 Write property test for API response structure validation


    - **Property 1: Metrics API returns valid structure**
    - **Property 2: Sessions API returns valid session objects**
    - **Validates: Requirements 1.1, 1.2**

- [x] 2. Implement error handling utility





  - [x] 2.1 Create error handler module


    - Create `frontend/src/lib/errorHandler.ts` with parseApiError(), getErrorMessage(), getRecoveryAction() functions
    - Implement error classification logic for network, client (4xx), and server (5xx) errors
    - _Requirements: 1.4, 6.1, 6.2, 6.3, 6.4_
  - [x] 2.2 Write property test for error classification


    - **Property 4: Error classification consistency**
    - **Validates: Requirements 1.4, 6.1, 6.2, 6.3, 6.4**


- [x] 3. Create new React Query hooks





  - [x] 3.1 Create useMetrics hook

    - Create `frontend/src/hooks/useMetrics.ts` with useOverallMetrics() and useSessionMetrics() hooks
    - _Requirements: 1.1_

  - [x] 3.2 Create useResults hook

    - Create `frontend/src/hooks/useResults.ts` with useCompletedSessions(), useSessionResults(), useDownloadPaper() hooks
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 3.3 Create useCompliance hook


    - Create `frontend/src/hooks/useCompliance.ts` with useComplianceReport() and useAllComplianceReports() hooks
    - _Requirements: 3.1_

  - [x] 3.4 Create useSettings hook

    - Create `frontend/src/hooks/useSettings.ts` with useSettings() and useUpdateSettings() hooks
    - _Requirements: 4.1, 4.2_

  - [x] 3.5 Write property test for settings round-trip

    - **Property 6: Settings round-trip consistency**
    - **Validates: Requirements 4.1, 4.2, 7.1, 7.2**

- [x] 4. Implement polling mechanism for real-time updates






  - [x] 4.1 Add polling support to useResearchSession hook

    - Modify `frontend/src/hooks/useResearchSessions.ts` to enable refetchInterval when session status is "running"
    - Implement logic to stop polling when status becomes "completed" or "failed"
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 4.2 Write property test for polling termination

    - **Property 7: Polling termination on terminal status**
    - **Validates: Requirements 5.1, 5.3, 5.4**

- [x] 5. Checkpoint - Ensure all frontend tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement backend settings endpoints





  - [x] 6.1 Add settings Pydantic models and storage


    - Add UserSettings and SettingsPreferences models to `backend/main.py`
    - Add in-memory settings storage
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 6.2 Implement GET /api/settings endpoint
    - Create endpoint to return current user settings

    - _Requirements: 7.1_
  - [x] 6.3 Implement POST /api/settings endpoint
    - Create endpoint to update and persist user settings
    - Add validation for required fields and email format
    - _Requirements: 7.2, 7.3_
  - [x] 6.4 Write property test for settings validation


    - **Property 8: Invalid settings rejection**
    - **Validates: Requirements 7.3**

- [x] 7. Implement backend download endpoint






  - [x] 7.1 Implement GET /api/sessions/{id}/download endpoint

    - Create endpoint that returns paper in PDF or LaTeX format
    - Set appropriate content-type headers (application/pdf, application/x-latex)
    - Return 404 for non-existent sessions
    - Return 400 for incomplete sessions
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 7.2 Write property tests for download endpoint


    - **Property 9: Non-existent session returns 404**
    - **Property 10: Incomplete session download rejection**
    - **Validates: Requirements 8.3, 8.4**

- [x] 8. Checkpoint - Ensure all backend tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integrate Dashboard page with backend





  - [x] 9.1 Update Dashboard to use real metrics data


    - Replace static stats array with useOverallMetrics() hook data
    - Add loading states using Skeleton components
    - Add error handling with retry option
    - _Requirements: 1.1, 1.3, 1.4_
  - [x] 9.2 Update Dashboard recent activity with real sessions

    - Replace static recentActivity array with useResearchSessions() hook data
    - Transform session data to activity format
    - _Requirements: 1.2_


- [x] 10. Integrate Results page with backend




  - [x] 10.1 Update Results page to fetch completed sessions


    - Replace static results array with useCompletedSessions() hook
    - Add loading and empty states
    - _Requirements: 2.1, 2.5_

  - [x] 10.2 Implement download functionality
    - Wire Download PDF button to useDownloadPaper() with format='pdf'
    - Wire Download LaTeX button to useDownloadPaper() with format='latex'
    - Add download progress indicator and error handling

    - _Requirements: 2.2, 2.3_
  - [x] 10.3 Implement View Full Report functionality
    - Wire View Full Report button to useSessionResults()
    - Display results in a dialog or navigate to detail page
    - _Requirements: 2.4_
  - [x] 10.4 Write property test for session filtering


    - **Property 3: Session filtering by status**
    - **Validates: Requirements 2.1**

- [x] 11. Integrate Ethics page with backend






  - [x] 11.1 Update Ethics page to fetch compliance data

    - Replace static complianceChecks array with useAllComplianceReports() hook
    - Add skeleton loaders during fetch
    - Add empty state when no compliance data exists
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 11.2 Write property test for compliance report structure

    - **Property 5: Compliance report structure validity**
    - **Validates: Requirements 3.1**

- [x] 12. Integrate Settings page with backend






  - [x] 12.1 Update Settings page to load and save preferences

    - Use useSettings() hook to populate form fields
    - Use useUpdateSettings() mutation for Save Changes button
    - Add success/error toast notifications
    - Preserve form state on error
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 13. Final Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
