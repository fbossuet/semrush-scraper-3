# Implementation Plan: Scraper SEM Parallèle

**Branch**: `001-name-trendtrack-scraper` | **Date**: 2025-09-16 | **Spec**: `/specs/001-name-trendtrack-scraper/spec.md`
**Input**: Feature specification from `/specs/001-name-trendtrack-scraper/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Scraper SEM Parallèle : Système de scraping automatisé et optimisé pour récupérer les métriques de performance des sites web via MyToolsPlan. Le système utilise une approche hybride combinant APIs et DOM scraping pour une récupération maximale des données. Architecture Python avec Playwright, SQLite, et FastAPI. Système de workers parallèles avec validation adaptative des 8 métriques.

## Technical Context
**Language/Version**: Python 3.x  
**Primary Dependencies**: Playwright, SQLite, FastAPI, Asyncio  
**Storage**: Dual SQLite databases - /home/ubuntu/trendtrack-scraper-final/data/trendtrack.db (production) and /home/ubuntu/trendtrack-scraper-final/data/trendtrack_test.db (testing)  
**Testing**: pytest, contract tests, integration tests with dedicated test database  
**Target Platform**: Linux VPS (Ubuntu)  
**Project Type**: single (backend scraping system)  
**Performance Goals**: 1-2 minutes per website, 95%+ API success rate, 90%+ DOM scraping success  
**Constraints**: VPS-only development, backup before modification, user validation required, dual database management  
**Scale/Scope**: 799+ websites, 8 metrics per website, parallel workers (1-3), 24h re-scraping threshold  

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Documentation-First Compliance
- ✅ Feature specification exists and is complete
- ✅ All requirements are testable and unambiguous
- ✅ Technical context is well-defined from existing documentation

### VPS-Only Development Compliance
- ✅ Development workflow specified (backup → modify → upload → verify)
- ✅ No local development dependencies
- ✅ VPS deployment and testing approach defined

### Validation Utilisateur Compliance
- ✅ User validation required for each modification
- ✅ Rollback system in place for failed validations
- ✅ No auto-completion without user approval

### Logs Immutables Compliance
- ✅ Log preservation strategy defined
- ✅ No modification of existing log messages
- ✅ Log analysis for debugging purposes

### Approche Adaptative Compliance
- ✅ Dynamic metric validation (8 metrics counted dynamically)
- ✅ Fallback system (sam2.mytoolsplan.xyz)
- ✅ Intelligent timeout and error handling

## Project Structure

### Documentation (this feature)
```
specs/001-name-trendtrack-scraper/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Existing project structure (sem-scraper-final)
production_scraper_parallel.py          # Scraper principal en production
menu_workers.py                         # Menu interactif de lancement
api_server.py                          # Serveur API FastAPI
trendtrack_api_vps_adapted.py          # API de persistance
api_client.py                          # Client API MyToolsPlan
launch_workers_by_status.py            # Lanceur workers par statut
launch_parallel_workers.py             # Lanceur workers parallèles
config.py                              # Configuration système
parallel_config.py                     # Configuration workers parallèles

# Base de données (trendtrack-scraper-final)
data/
├── trendtrack.db                      # Base de données production
└── trendtrack_test.db                 # Base de données test

# Logs et résultats
logs/                                  # Logs de scraping
results/                               # Résultats des sessions
```

**Structure Decision**: Existing project structure - sem-scraper-final (scraping) + trendtrack-scraper-final (database)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Research Playwright best practices for MyToolsPlan scraping
   - Research SQLite optimization for high-volume metric storage
   - Research FastAPI patterns for scraping system APIs
   - Research asyncio patterns for parallel worker management

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Playwright authentication and session management for MyToolsPlan"
   Task: "Research SQLite schema design for website metrics storage"
   Task: "Research FastAPI async patterns for scraping endpoints"
   Task: "Research asyncio worker pool patterns for parallel processing"
   Task: "Research error handling patterns for hybrid API/DOM scraping"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Website entity (URL, status, metadata)
   - Metrics entity (8 metrics with validation rules)
   - ScrapingSession entity (workers, progress, status)
   - Worker entity (parallel processing unit)

2. **Generate API contracts** from functional requirements:
   - GET /websites - List websites with filtering by status
   - POST /websites - Add new website for scraping
   - GET /websites/{id}/metrics - Get metrics for specific website
   - POST /scraping/sessions - Start new scraping session
   - GET /scraping/sessions/{id}/status - Get session progress
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Website scraping flow → integration test scenario
   - Parallel worker management → integration test scenario
   - Metric validation → integration test scenario
   - Quickstart test = end-to-end scraping validation

5. **Update agent file incrementally**:
   - Run `.specify/scripts/bash/update-agent-context.sh cursor` for Claude
   - Add Playwright, SQLite, FastAPI, asyncio context
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before workers before API
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected - all constitutional requirements are met.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*
