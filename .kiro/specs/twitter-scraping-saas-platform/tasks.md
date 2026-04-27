# Implementation Tasks

## Overview

Este documento define o plano de implementação completo para a plataforma Twitter Scraping SaaS. As tasks estão organizadas em ordem lógica de dependências, priorizando infraestrutura, backend core, worker assíncrono, API, frontend e testes.

**Spec Path:** `.kiro/specs/twitter-scraping-saas-platform/`

**Stack Tecnológico:**
- Backend: Python 3.11+ + FastAPI
- Frontend: React 18+ + TypeScript + Vite + Tailwind CSS
- Banco: Supabase (PostgreSQL + Storage)
- Fila: Celery + Redis
- Testes: Hypothesis (PBT) + pytest

## Tasks

### Phase 1: Project Setup and Infrastructure

- [x] 1. Setup Backend Project Structure
  - [x] 1.1 Create Python project with Poetry/pip
  - [x] 1.2 Setup FastAPI application with basic structure
  - [x] 1.3 Create folder structure (app/, app/models/, app/services/, app/repositories/, app/api/, app/workers/, app/utils/, tests/)
  - [x] 1.4 Configure environment variables (.env.example, .env)
  - [x] 1.5 Setup logging configuration
  - [x] 1.6 Create requirements.txt or pyproject.toml with dependencies

- [-] 2. Setup Supabase Database
  - [ ] 2.1 Create Supabase project
  - [x] 2.2 Create `configurations` table with schema from design.md
  - [x] 2.3 Create `campaigns` table with schema from design.md
  - [x] 2.4 Create `campaign_results` table with schema from design.md
  - [x] 2.5 Create `campaign_analysis` table with schema from design.md
  - [x] 2.6 Create all indexes defined in design.md
  - [x] 2.7 Setup Supabase Storage bucket for campaign documents
  - [x] 2.8 Configure Supabase client in Python

- [-] 3. Setup Redis and Celery
  - [ ] 3.1 Install and configure Redis locally
  - [x] 3.2 Setup Celery application with Redis broker
  - [x] 3.3 Configure Celery worker settings (max retries, timeout)
  - [x] 3.4 Create Celery task base configuration
  - [x] 3.5 Setup Celery beat for scheduled tasks (future)

- [x] 4. Setup Frontend Project
  - [x] 4.1 Create React project with Vite and TypeScript
  - [x] 4.2 Install dependencies (React Router, Axios, TanStack Query, Tailwind CSS)
  - [x] 4.3 Configure Tailwind CSS
  - [x] 4.4 Setup folder structure (src/pages/, src/components/, src/services/, src/types/, src/utils/)
  - [x] 4.5 Configure API client (Axios with base URL)
  - [x] 4.6 Setup React Router with routes

### Phase 2: Backend Core - Data Models and Utilities

- [x] 5. Implement Pydantic Data Models
  - [x] 5.1 Create `ConfigurationDTO` and `ConfigurationResponseDTO`
  - [x] 5.2 Create `CampaignCreateDTO` with validators
  - [x] 5.3 Create `Campaign` and `CampaignConfig` models
  - [x] 5.4 Create `Tweet` model
  - [x] 5.5 Create `Analysis` model
  - [x] 5.6 Create `PaginatedResponse` generic model
  - [x] 5.7 Create `ValidationResult` model
  - [x] 5.8 Create `ScrapingConfig` model

- [x] 6. Implement Encryption Service
  - [x] 6.1 Create `Encryptor` class with AES-256-GCM
  - [x] 6.2 Implement `encrypt()` method
  - [x] 6.3 Implement `decrypt()` method
  - [x] 6.4 Load encryption key from environment variable
  - [x] 6.5 Generate unique IV for each encryption

- [x] 7. Implement Campaign Parser
  - [x] 7.1 Create `CampaignParser` class
  - [x] 7.2 Implement `parse_profiles()` - split by comma/newline, trim, remove @, remove empty
  - [x] 7.3 Implement `parse_keywords()` - split by comma/newline, trim, remove empty
  - [x] 7.4 Implement `format_profiles()` - add @ prefix for display
  - [x] 7.5 Implement `format_keywords()` - format for display
  - [x] 7.6 Implement `format_engagement_filters()` - format with labels

- [x] 8. Implement Campaign Validator
  - [x] 8.1 Create `CampaignValidator` class
  - [x] 8.2 Implement `validate_create()` - validate campaign name, search type, profiles/keywords
  - [x] 8.3 Implement `validate_search_config()` - validate based on search type
  - [x] 8.4 Implement `validate_engagement_filters()` - check non-negative
  - [x] 8.5 Return `ValidationResult` with specific error messages

### Phase 3: Backend Core - Repositories and Services

- [x] 9. Implement Configuration Repository
  - [x] 9.1 Create `ConfigurationRepository` class
  - [x] 9.2 Implement `create()` - insert configuration into Supabase
  - [x] 9.3 Implement `get()` - retrieve configuration from Supabase
  - [x] 9.4 Implement `update()` - update existing configuration
  - [x] 9.5 Implement `exists()` - check if configuration exists

- [x] 10. Implement Configuration Manager
  - [x] 10.1 Create `ConfigurationManager` class
  - [x] 10.2 Implement `save_configuration()` - encrypt tokens and save via repository
  - [x] 10.3 Implement `get_configuration()` - retrieve and decrypt tokens
  - [x] 10.4 Implement `mask_tokens()` - return masked version for API responses
  - [x] 10.5 Implement `validate_tokens()` - basic format validation

- [x] 11. Implement Campaign Repository
  - [x] 11.1 Create `CampaignRepository` class
  - [x] 11.2 Implement `create()` - insert campaign into Supabase
  - [x] 11.3 Implement `get_by_id()` - retrieve campaign by ID
  - [x] 11.4 Implement `list_all()` - list campaigns with pagination
  - [x] 11.5 Implement `update_status()` - update campaign status
  - [x] 11.6 Implement `save_results()` - insert campaign_results
  - [x] 11.7 Implement `save_analysis()` - insert campaign_analysis
  - [x] 11.8 Implement `get_results()` - retrieve campaign results

- [x] 12. Implement Campaign Service
  - [x] 12.1 Create `CampaignService` class
  - [x] 12.2 Implement `create_campaign()` - validate, parse, create, enqueue
  - [x] 12.3 Implement `get_campaign()` - retrieve campaign details
  - [x] 12.4 Implement `list_campaigns()` - list with pagination
  - [x] 12.5 Implement `get_campaign_results()` - retrieve results for a campaign

### Phase 4: Scraping Engine and External Services

- [x] 13. Implement Twitter Scraping Engine
  - [x] 13.1 Create `TwitterScrapingEngine` class implementing `ScrapingEngine` interface
  - [x] 13.2 Implement `build_query()` - construct Twitter query with operators (from:, lang:, min_faves:, min_replies:, since:)
  - [x] 13.3 Implement `scrape()` - invoke Apify actor "automation-lab/twitter-scraper"
  - [x] 13.4 Implement `apply_filters()` - filter tweets locally by engagement criteria
  - [x] 13.5 Implement `transform_results()` - transform Apify response to Tweet model
  - [x] 13.6 Handle Twitter cookies (auth_token, ct0) from configuration

- [x] 14. Implement Analysis Engine
  - [x] 14.1 Create `AnalysisEngine` class
  - [x] 14.2 Implement `prepare_prompt()` - create prompt for OpenAI with tweets
  - [x] 14.3 Implement `analyze()` - call OpenAI API with prompt
  - [x] 14.4 Implement `parse_response()` - parse OpenAI response into Analysis model
  - [x] 14.5 Handle OpenAI API errors and rate limits

- [ ] 15. Implement Document Generator
  - [x] 15.1 Create `DocumentGenerator` class
  - [x] 15.2 Implement `generate()` - create .doc file with python-docx
  - [x] 15.3 Add campaign header (name, date, status)
  - [x] 15.4 Add configuration section (formatted with CampaignParser)
  - [x] 15.5 Add tweets section (formatted list)
  - [x] 15.6 Add analysis section
  - [x] 15.7 Save file to temporary location and return path

- [x] 16. Implement Email Service
  - [x] 16.1 Create `EmailService` class
  - [x] 16.2 Implement `create_message()` - create email with HTML body
  - [x] 16.3 Implement `send_campaign_results()` - send email with .doc attachment via SMTP
  - [x] 16.4 Use Gmail SMTP with credentials from configuration
  - [x] 16.5 Handle SMTP errors and authentication failures

- [x] 17. Implement Storage Service
  - [x] 17.1 Create `StorageService` class
  - [x] 17.2 Implement `upload_document()` - upload .doc to Supabase Storage
  - [x] 17.3 Organize files in folder structure: campaigns/{campaign_id}/results.doc
  - [x] 17.4 Implement `get_signed_url()` - generate temporary signed URL
  - [x] 17.5 Implement `delete_document()` - remove file from storage
  - [x] 17.6 Handle storage errors and quota limits

### Phase 5: Celery Worker - Campaign Executor

- [x] 18. Implement Campaign Executor Task
  - [x] 18.1 Create `execute_campaign` Celery task
  - [x] 18.2 Update campaign status to "running"
  - [x] 18.3 Retrieve configuration from ConfigurationManager
  - [x] 18.4 Invoke ScrapingEngine with campaign config
  - [x] 18.5 Save scraped tweets to campaign_results table
  - [x] 18.6 Invoke AnalysisEngine with tweets
  - [x] 18.7 Save analysis to campaign_analysis table
  - [x] 18.8 Invoke DocumentGenerator to create .doc
  - [x] 18.9 Invoke EmailService to send email
  - [x] 18.10 Invoke StorageService to upload file
  - [x] 18.11 Update campaign status to "completed" with document URL
  - [x] 18.12 Handle errors at each step and update status to "failed" with error message
  - [x] 18.13 Implement retry logic with exponential backoff (max 3 retries)

### Phase 6: FastAPI REST API Endpoints

- [x] 19. Implement Configuration Endpoints
  - [x] 19.1 Create `GET /api/configuration` endpoint
  - [x] 19.2 Return masked configuration via ConfigurationManager
  - [x] 19.3 Create `POST /api/configuration` endpoint
  - [x] 19.4 Validate and save configuration via ConfigurationManager
  - [x] 19.5 Return success response

- [x] 20. Implement Campaign Endpoints
  - [x] 20.1 Create `POST /api/campaigns` endpoint
  - [x] 20.2 Validate request body with CampaignCreateDTO
  - [x] 20.3 Create campaign via CampaignService
  - [x] 20.4 Enqueue campaign execution task
  - [x] 20.5 Return campaign_id
  - [x] 20.6 Create `GET /api/campaigns` endpoint with pagination
  - [x] 20.7 List campaigns via CampaignService
  - [x] 20.8 Create `GET /api/campaigns/{id}` endpoint
  - [x] 20.9 Return campaign details with results
  - [x] 20.10 Create `GET /api/campaigns/{id}/download` endpoint
  - [x] 20.11 Generate signed URL via StorageService
  - [x] 20.12 Return download URL

- [x] 21. Implement Error Handling Middleware
  - [x] 21.1 Create global exception handler
  - [x] 21.2 Return consistent error response format (code, message, details)
  - [x] 21.3 Handle validation errors (HTTP 400)
  - [x] 21.4 Handle not found errors (HTTP 404)
  - [x] 21.5 Handle internal server errors (HTTP 500)
  - [x] 21.6 Log all errors with appropriate level

### Phase 7: Frontend - Pages and Components

- [x] 22. Implement Layout and Navigation
  - [x] 22.1 Create `Layout` component with sidebar/navbar
  - [x] 22.2 Add navigation links (Configurações, Nova Campanha, Histórico)
  - [x] 22.3 Style with Tailwind CSS
  - [x] 22.4 Add logo and branding

- [x] 23. Implement Configuration Page
  - [x] 23.1 Create `ConfigurationPage` component
  - [x] 23.2 Create form with fields: email, apify_token, openai_token, smtp_password
  - [x] 23.3 Load existing configuration on mount (GET /api/configuration)
  - [x] 23.4 Display masked tokens
  - [x] 23.5 Implement form validation
  - [x] 23.6 Handle form submission (POST /api/configuration)
  - [x] 23.7 Show loading state and success/error messages
  - [x] 23.8 Style with Tailwind CSS

- [x] 24. Implement Campaign Creation Page
  - [x] 24.1 Create `CampaignCreationPage` component
  - [x] 24.2 Create form with all fields (name, search_type, profiles/keywords, language, filters)
  - [x] 24.3 Implement conditional rendering (show profiles field if search_type=profile, keywords if keywords)
  - [x] 24.4 Add language dropdown (en, pt, es, etc)
  - [x] 24.5 Add numeric inputs for engagement filters (min_likes, min_retweets, min_replies)
  - [x] 24.6 Implement form validation
  - [x] 24.7 Handle form submission (POST /api/campaigns)
  - [x] 24.8 Show loading state during submission
  - [x] 24.9 Show success message and redirect to history after 3 seconds
  - [x] 24.10 Show error messages if submission fails
  - [x] 24.11 Implement "Cancelar" button to reset form
  - [x] 24.12 Style with Tailwind CSS

- [x] 25. Implement Campaign History Page
  - [x] 25.1 Create `CampaignHistoryPage` component
  - [x] 25.2 Fetch campaigns list on mount (GET /api/campaigns)
  - [x] 25.3 Display campaigns in table/card format
  - [x] 25.4 Show: name, date, status, results_count for each campaign
  - [x] 25.5 Implement status indicators (pending, running, completed, failed) with colors
  - [x] 25.6 Implement pagination controls
  - [x] 25.7 Implement auto-refresh every 10 seconds (polling)
  - [x] 25.8 Show loading indicator during refresh
  - [x] 25.9 Make campaigns clickable to navigate to details page
  - [x] 25.10 Style with Tailwind CSS

- [x] 26. Implement Campaign Detail Page
  - [x] 26.1 Create `CampaignDetailPage` component
  - [x] 26.2 Fetch campaign details on mount (GET /api/campaigns/{id})
  - [x] 26.3 Display campaign name, date, status
  - [x] 26.4 Display "Configuração Utilizada" section with formatted config
  - [x] 26.5 Display "Resultados" section with tweets list (if completed)
  - [x] 26.6 Show tweet author, text, likes, retweets, replies, timestamp
  - [x] 26.7 Add link to view tweet on Twitter
  - [x] 26.8 Display error message if status is "failed"
  - [x] 26.9 Add "Baixar Documento" button (if document exists)
  - [x] 26.10 Add "Visualizar Documento" button (if document exists)
  - [x] 26.11 Handle download button click (GET /api/campaigns/{id}/download)
  - [x] 26.12 Style with Tailwind CSS

- [x] 27. Implement Document Viewer Component
  - [x] 27.1 Create `DocumentViewer` component (modal/overlay)
  - [x] 27.2 Load document from Supabase Storage URL
  - [x] 27.3 Display document preview (use iframe or document viewer library)
  - [x] 27.4 Add close button
  - [x] 27.5 Show loading state while document loads
  - [x] 27.6 Show error message if document cannot be loaded
  - [x] 27.7 Offer download option if preview fails
  - [x] 27.8 Style with Tailwind CSS

### Phase 8: Property-Based Tests

- [x] 28. Implement Configuration Properties Tests
  - [x] 28.1 Test Property 1: Configuration Round-Trip Preserves Data
  - [x] 28.2 Test Property 2: Token Masking Never Exposes Complete Tokens
  - [x] 28.3 Test Property 3: Configuration Validation Rejects Incomplete Data
  - [x] 28.4 Test Property 22: Token Encryption Is Reversible

- [x] 29. Implement Campaign Validation Properties Tests
  - [x] 29.1 Test Property 4: Campaign Name Validation Rejects Empty Names
  - [x] 29.2 Test Property 5: Profile Search Requires Profiles
  - [x] 29.3 Test Property 6: Keyword Search Requires Keywords
  - [x] 29.4 Test Property 9: Engagement Filters Must Be Non-Negative

- [x] 30. Implement Parsing Properties Tests
  - [ ] 30.1 Test Property 7: Profile Parsing Removes @ Symbol
  - [ ] 30.2 Test Property 8: Keyword Preservation
  - [ ] 30.3 Test Property 10: List Parsing Handles Multiple Delimiters
  - [ ] 30.4 Test Property 11: Parsed List Is Never Empty After Valid Input
  - [ ] 30.5 Test Property 21: Configuration Formatting Is Reversible

- [x] 31. Implement Query Construction Properties Tests
  - [x] 31.1 Test Property 12: Profile Query Construction
  - [x] 31.2 Test Property 13: Keyword Query Construction
  - [x] 31.3 Test Property 14: Language Operator Always Present
  - [x] 31.4 Test Property 15: Conditional Min Faves Operator
  - [x] 31.5 Test Property 16: Conditional Min Replies Operator
  - [x] 31.6 Test Property 17: Since Operator Date Calculation

- [x] 32. Implement Transformation Properties Tests
  - [x] 32.1 Test Property 18: Local Filtering Enforces Engagement Criteria
  - [x] 32.2 Test Property 19: Tweet Transformation Includes All Required Fields
  - [x] 32.3 Test Property 20: Document Contains All Required Sections

- [x] 33. Implement Queue and Status Properties Tests
  - [x] 33.1 Test Property 23: FIFO Queue Processing Order
  - [x] 33.2 Test Property 24: Campaign Status Transitions Are Valid

### Phase 9: Unit Tests

- [x] 34. Unit Tests for Core Components
  - [x] 34.1 Test ConfigurationManager (save, get, mask, validate)
  - [x] 34.2 Test CampaignParser (parse_profiles, parse_keywords, format methods)
  - [x] 34.3 Test CampaignValidator (validate_create, validate_search_config)
  - [x] 34.4 Test Encryptor (encrypt, decrypt)
  - [x] 34.5 Test TwitterScrapingEngine (build_query, apply_filters, transform_results)
  - [x] 34.6 Test AnalysisEngine (prepare_prompt, parse_response)
  - [x] 34.7 Test DocumentGenerator (generate, format methods)
  - [x] 34.8 Test EmailService (create_message, send)
  - [x] 34.9 Test StorageService (upload, get_signed_url, delete)

### Phase 10: Integration Tests

- [x] 35. Integration Tests for External Services
  - [x] 35.1 Test Apify integration with mocked responses
  - [x] 35.2 Test OpenAI integration with mocked responses
  - [x] 35.3 Test Supabase database operations
  - [x] 35.4 Test Supabase Storage operations
  - [x] 35.5 Test SMTP email sending with test server
  - [x] 35.6 Test Celery task execution with test queue

### Phase 11: End-to-End Tests

- [x] 36. E2E Tests for Complete Workflows
  - [x] 36.1 Test: User configures credentials → creates campaign → views results
  - [x] 36.2 Test: User creates campaign with invalid data → sees error messages
  - [x] 36.3 Test: Campaign execution fails → user sees error in history
  - [x] 36.4 Test: User downloads document → file is correct
  - [x] 36.5 Test: Multiple campaigns execute in parallel → all complete successfully

### Phase 12: Docker and Deployment

- [x] 37. Create Docker Configuration
  - [x] 37.1 Create Dockerfile for backend (Python + FastAPI)
  - [x] 37.2 Create Dockerfile for frontend (Node + Vite build)
  - [x] 37.3 Create docker-compose.yml with services (backend, worker, redis, frontend)
  - [x] 37.4 Configure environment variables in docker-compose
  - [x] 37.5 Test local deployment with Docker Compose

- [x] 38. Setup CI/CD Pipeline
  - [x] 38.1 Create GitHub Actions workflow (or similar)
  - [x] 38.2 Run linters (flake8, black, mypy for Python; eslint for TypeScript)
  - [x] 38.3 Run unit tests
  - [x] 38.4 Run property-based tests
  - [x] 38.5 Run integration tests
  - [x] 38.6 Generate coverage report (fail if < 80%)
  - [x] 38.7 Build Docker images
  - [x] 38.8 Push images to registry

### Phase 13: Documentation and Polish

- [x] 39. Create Documentation
  - [x] 39.1 Write README.md with project overview
  - [x] 39.2 Document installation instructions
  - [x] 39.3 Document environment variables
  - [x] 39.4 Document API endpoints (OpenAPI/Swagger)
  - [x] 39.5 Document deployment process
  - [x] 39.6 Create user guide for frontend

- [x] 40. Final Polish and Testing
  - [x] 40.1 Test complete flow end-to-end manually
  - [x] 40.2 Fix any remaining bugs
  - [x] 40.3 Optimize performance (database queries, API response times)
  - [x] 40.4 Add loading states and error handling to all frontend components
  - [x] 40.5 Ensure responsive design works on mobile
  - [x] 40.6 Run security audit (check for exposed secrets, SQL injection, XSS)
  - [x] 40.7 Setup monitoring and logging for production

## Notes

- Tasks are organized by phase for logical progression
- Each task references specific requirements and design components
- Property-based tests validate the 24 correctness properties from design.md
- Frontend tasks focus on MVP functionality with clean UX
- All external service integrations include error handling and retry logic
- Security is built-in from the start (encryption, validation, HTTPS)

## Estimated Timeline

- Phase 1-3 (Setup + Core): 2-3 days
- Phase 4-5 (Scraping + Worker): 2-3 days
- Phase 6 (API): 1 day
- Phase 7 (Frontend): 3-4 days
- Phase 8-11 (Tests): 2-3 days
- Phase 12-13 (Deploy + Docs): 1-2 days

**Total: ~12-16 days** for full implementation with tests and documentation.
