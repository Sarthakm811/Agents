# Requirements Document

## Introduction

This document specifies the requirements for completing the integration between the React/TypeScript frontend and the FastAPI Python backend of the Hybrid AI Research System. The system enables users to create, manage, and monitor AI-powered research sessions that generate academic papers. Currently, the frontend has an API client and hooks infrastructure, but several pages use static mock data instead of live backend data. This integration will connect all frontend components to the backend API, implement real-time updates, add proper error handling, and ensure data consistency across the application.

## Glossary

- **Research Session**: A complete research workflow instance containing configuration, stages, metrics, and agent activities
- **API Client**: The TypeScript class (`apiClient`) that handles HTTP communication with the backend
- **React Query**: The data fetching library (`@tanstack/react-query`) used for server state management
- **Research Stage**: A discrete phase in the research pipeline (e.g., Literature Review, Hypothesis Generation)
- **Agent**: An AI component that performs specific research tasks within a session
- **Metrics**: Quantitative measurements of research quality (originality, novelty, ethics scores)
- **Compliance Report**: An ethics and governance assessment for a research session

## Requirements

### Requirement 1

**User Story:** As a user, I want the Dashboard to display real-time metrics from the backend, so that I can monitor the actual state of my research system.

#### Acceptance Criteria

1. WHEN the Dashboard page loads THEN the System SHALL fetch overall metrics from the `/api/metrics` endpoint and display them in the stats cards
2. WHEN the Dashboard page loads THEN the System SHALL fetch recent sessions from the `/api/sessions` endpoint and display them in the Recent Activity section
3. WHEN backend data is being fetched THEN the System SHALL display loading indicators in place of the data
4. IF the backend request fails THEN the System SHALL display an error message and provide a retry option

### Requirement 2

**User Story:** As a user, I want the Results page to display actual completed research results from the backend, so that I can view and download my generated papers.

#### Acceptance Criteria

1. WHEN the Results page loads THEN the System SHALL fetch completed sessions from the `/api/sessions` endpoint filtered by status
2. WHEN a user clicks Download PDF THEN the System SHALL request the paper from `/api/sessions/{id}/download?format=pdf` and initiate a file download
3. WHEN a user clicks Download LaTeX THEN the System SHALL request the paper from `/api/sessions/{id}/download?format=latex` and initiate a file download
4. WHEN a user clicks View Full Report THEN the System SHALL fetch detailed results from `/api/sessions/{id}/results` and display them
5. IF no completed sessions exist THEN the System SHALL display an empty state message with guidance

### Requirement 3

**User Story:** As a user, I want the Ethics page to display real compliance data from the backend, so that I can review actual ethics assessments for my research.

#### Acceptance Criteria

1. WHEN the Ethics page loads THEN the System SHALL fetch compliance reports from completed sessions via `/api/sessions/{id}/compliance`
2. WHEN displaying compliance data THEN the System SHALL show category scores, individual check statuses, and overall compliance score
3. WHEN backend data is being fetched THEN the System SHALL display skeleton loaders for compliance cards
4. IF no compliance data exists THEN the System SHALL display an empty state indicating no ethics audits are available

### Requirement 4

**User Story:** As a user, I want the Settings page to persist my preferences to the backend, so that my configuration is saved across sessions.

#### Acceptance Criteria

1. WHEN the Settings page loads THEN the System SHALL fetch user preferences from the backend
2. WHEN a user clicks Save Changes THEN the System SHALL send updated preferences to the backend via a POST request
3. WHEN preferences are saved successfully THEN the System SHALL display a success notification
4. IF saving preferences fails THEN the System SHALL display an error notification and preserve the form state

### Requirement 5

**User Story:** As a user, I want to see real-time progress updates for running research sessions, so that I can monitor ongoing research without refreshing the page.

#### Acceptance Criteria

1. WHILE a research session has status "running" THEN the System SHALL poll the session endpoint at regular intervals to fetch updated progress
2. WHEN session progress changes THEN the System SHALL update the UI to reflect new stage status and metrics
3. WHEN a session transitions to "completed" status THEN the System SHALL stop polling and display completion notification
4. WHEN a session transitions to "failed" status THEN the System SHALL stop polling and display error details

### Requirement 6

**User Story:** As a user, I want consistent error handling across all API interactions, so that I understand when something goes wrong and can take appropriate action.

#### Acceptance Criteria

1. WHEN any API request fails with a network error THEN the System SHALL display a user-friendly error message indicating connectivity issues
2. WHEN any API request fails with a 4xx status THEN the System SHALL display the error message from the backend response
3. WHEN any API request fails with a 5xx status THEN the System SHALL display a generic server error message and log details for debugging
4. WHEN an error occurs THEN the System SHALL provide contextual recovery options where applicable

### Requirement 7

**User Story:** As a user, I want the backend to support user settings persistence, so that my preferences are stored and retrieved correctly.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/settings` THEN the Backend SHALL return the current user settings object
2. WHEN a POST request is made to `/api/settings` with valid settings data THEN the Backend SHALL persist the settings and return the updated object
3. IF invalid settings data is provided THEN the Backend SHALL return a 400 status with validation error details

### Requirement 8

**User Story:** As a user, I want the backend to support paper download functionality, so that I can retrieve generated papers in different formats.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/sessions/{id}/download?format=pdf` THEN the Backend SHALL return the paper as a PDF file with appropriate content-type headers
2. WHEN a GET request is made to `/api/sessions/{id}/download?format=latex` THEN the Backend SHALL return the paper as a LaTeX file with appropriate content-type headers
3. IF the requested session does not exist THEN the Backend SHALL return a 404 status with an error message
4. IF the session has not completed THEN the Backend SHALL return a 400 status indicating the paper is not yet available
