 # Implementation Plan

- [x] 1. Set up configuration management





  - [x] 1.1 Create configuration module with API key loading


    - Update `src/utils/config.py` with APIConfig dataclass and ConfigManager class
    - Load OPENAI_API_KEY, ANTHROPIC_API_KEY, SEMANTIC_SCHOLAR_API_KEY from environment variables
    - Add validation to check for required keys and log warnings for missing optional keys
    - _Requirements: 3.1, 3.2_

  - [x] 1.2 Write property test for API key security

    - **Property 4: API key security**
    - **Validates: Requirements 3.3**

- [x] 2. Implement rate limiting utilities





  - [x] 2.1 Create rate limiter class


    - Add RateLimiter class to `src/tools/orchestrator.py` with configurable requests per period
    - Implement async acquire() method that waits if rate limit exceeded
    - Add get_wait_time() method for status reporting
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 2.2 Write property test for rate limiting

    - **Property 8: Rate limiting enforcement**
    - **Validates: Requirements 6.1**

- [x] 3. Implement arXiv API integration





  - [x] 3.1 Add arXiv search functionality


    - Add search_arxiv() method to AutonomousToolOrchestrator
    - Parse arXiv Atom feed response into Paper objects
    - Apply rate limiting (1 request per 3 seconds)
    - _Requirements: 1.1, 1.3, 6.1_

  - [x] 3.2 Write property test for paper normalization

    - **Property 1: Paper normalization completeness**
    - **Validates: Requirements 1.3**

- [x] 4. Implement Semantic Scholar API integration






  - [x] 4.1 Add Semantic Scholar search functionality

    - Add search_semantic_scholar() method to AutonomousToolOrchestrator
    - Parse JSON response into Paper objects with citation counts
    - Apply rate limiting (100 requests per 5 minutes)
    - _Requirements: 1.2, 1.3, 6.2_

- [x] 5. Implement retry logic and deduplication





  - [x] 5.1 Add retry decorator with exponential backoff


    - Create retry decorator that retries up to 3 times with exponential backoff (1s, 2s, 4s)
    - Apply to all external API calls
    - _Requirements: 1.4_

  - [x] 5.2 Add paper deduplication

    - Implement deduplicate_papers() method using DOI matching and title similarity
    - Use fuzzy string matching for title comparison (threshold 0.9)
    - _Requirements: 1.5_

  - [x] 5.3 Write property test for deduplication

    - **Property 2: Paper deduplication correctness**
    - **Validates: Requirements 1.5**
  - [x] 5.4 Write property test for retry behavior


    - **Property 3: Retry behavior on failure**
    - **Validates: Requirements 1.4**

- [x] 6. Checkpoint - Ensure tool orchestrator tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement LLM client abstraction






  - [x] 7.1 Create LLM client module

    - Create `src/agents/llm_client.py` with LLMClient class
    - Implement OpenAI provider using openai library
    - Implement Anthropic provider using anthropic library
    - Add generate() and generate_structured() methods
    - _Requirements: 3.4_

- [x] 8. Implement research agents





  - [x] 8.1 Implement LiteratureAgent


    - Create LiteratureAgent class that searches and summarizes papers
    - Use LLM to generate literature summary from paper abstracts
    - _Requirements: 2.1_

  - [x] 8.2 Implement GapAnalysisAgent

    - Create GapAnalysisAgent class that identifies research gaps
    - Use LLM to compare topic against literature and find gaps
    - _Requirements: 2.2_
  - [x] 8.3 Implement HypothesisAgent


    - Create HypothesisAgent class that generates research hypotheses
    - Use LLM to propose novel directions based on gaps
    - _Requirements: 2.3_


  - [x] 8.4 Implement MethodologyAgent

    - Create MethodologyAgent class that designs research methodology
    - Use LLM to generate methodology appropriate for domain and complexity

    - _Requirements: 2.4_
  - [x] 8.5 Implement WritingAgent

    - Create WritingAgent class that composes the research paper
    - Generate all sections: abstract, introduction, methodology, results, conclusion
    - _Requirements: 2.5_


  - [x] 8.6 Write property test for paper structure
    - **Property 5: Paper structure completeness**
    - **Validates: Requirements 2.5**

- [x] 9. Implement AgenticResearchSwarm pipeline






  - [x] 9.1 Create research pipeline orchestration

    - Update AgenticResearchSwarm to coordinate all agents
    - Implement execute_pipeline() method that runs agents in sequence
    - Add progress_callback for real-time updates
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 9.2 Write property test for task metrics

    - **Property 7: Task completion metrics**
    - **Validates: Requirements 5.3**

- [x] 10. Checkpoint - Ensure agent tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement background task processing





  - [x] 11.1 Create background task manager


    - Create `backend/tasks.py` with BackgroundTaskManager class
    - Implement start_research_task() that spawns asyncio task
    - Add callbacks for progress, completion, and error handling
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 11.2 Integrate background tasks with API endpoints


    - Update POST /api/sessions/{id}/start to use BackgroundTaskManager
    - Update session storage with progress from callbacks
    - Handle task cancellation on session stop
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 11.3 Write property test for stage progress


    - **Property 6: Stage progress consistency**
    - **Validates: Requirements 4.2, 4.3**
  - [x] 11.4 Write property test for failure handling


    - **Property 10: Session failure handling**
    - **Validates: Requirements 4.4**

- [x] 12. Implement paper generation with citations








  - [x] 12.1 Update paper builder for real content


    - Update `src/authorship/paper_builder.py` to compile agent outputs
    - Generate proper LaTeX document structure
    - Include BibTeX citations for all referenced papers
    - _Requirements: 7.1, 7.2_

  - [x] 12.2 Update download endpoint for real papers

    - Update GET /api/sessions/{id}/download to use paper builder output
    - Generate valid PDF using LaTeX compilation or reportlab
    - Return LaTeX source with BibTeX file
    - _Requirements: 7.3, 7.4_

  - [x] 12.3 Write property test for citation completeness

    - **Property 9: Citation completeness**
    - **Validates: Requirements 7.2**

- [x] 13. Checkpoint - Ensure paper generation tests pass





  - Ensure all tests pass, ask the user if questions arise.


- [x] 14. Create environment configuration





  - [x] 14.1 Add environment variable documentation

    - Create `.env.example` file with all required environment variables
    - Update README.md with setup instructions for API keys
    - _Requirements: 3.1, 3.2_


- [x] 15. Final Checkpoint - Ensure all tests pass




  - Ensure all tests pass, ask the user if questions arise.

