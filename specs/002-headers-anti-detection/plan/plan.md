# Implementation Plan: Système de Headers Anti-Détection

**Branch**: `002-headers-anti-detection` | **Date**: 2025-09-19 | **Spec**: `/specs/002-headers-anti-detection/spec.md`
**Input**: Feature specification from `/specs/002-headers-anti-detection/spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
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
Système de Headers Anti-Détection : Implémentation d'un système complet de gestion des headers HTTP pour éviter la détection par les sites distants lors du scraping. Le système inclut la rotation automatique des User-Agents, la randomisation des headers de navigation, la gestion des headers de sécurité modernes (Sec-Fetch-*), et l'intégration avec Playwright pour une discrétion maximale.

## Technical Context
**Language/Version**: Python 3.x  
**Primary Dependencies**: Playwright, Asyncio, Random, Time  
**Storage**: Configuration files, Header profiles, Rotation schedules  
**Testing**: Unit tests for header generation, Integration tests with real sites  
**Target Platform**: Linux VPS (Ubuntu)  
**Project Type**: single (backend scraping system enhancement)  
**Performance Goals**: Header rotation in <100ms, Zero detection rate, 99.9% request success  
**Constraints**: VPS-only development, backup before modification, user validation required  
**Scale/Scope**: Multiple workers, 24/7 operation, 1000+ requests per hour per worker  

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
- ✅ Dynamic header adaptation based on site responses
- ✅ Fallback system for blocked header combinations
- ✅ Intelligent rotation and error handling

## Project Structure

### Documentation (this feature)
```
specs/002-headers-anti-detection/
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
stealth_system.py                    # Système de stealth existant (à étendre)
parallel_config.py                   # Configuration parallèle (à étendre)
production_scraper_parallel.py       # Scraper principal (à intégrer)
api_client_refactored.py             # Client API (à intégrer)
global_bootstrap.py                  # Bootstrap global (à intégrer)

# Nouveaux modules à créer
header_manager.py                     # Gestionnaire principal des headers
header_profiles.py                    # Profils de headers prédéfinis
header_rotation.py                    # Logique de rotation des headers
header_validation.py                  # Validation et adaptation des headers
stealth_integration.py                # Intégration avec le système de stealth existant

# Configuration
header_config.py                      # Configuration des headers
header_constants.py                   # Constantes et pools de headers
```

**Structure Decision**: Extension du système existant - Intégration avec stealth_system.py et parallel_config.py existants

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Research Playwright header injection patterns
   - Research modern browser header signatures
   - Research anti-detection header strategies
   - Research header rotation timing patterns
   - Research site-specific header requirements

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Playwright header injection and browser context management"
   Task: "Research modern browser header signatures and Sec-Fetch-* headers"
   Task: "Research anti-detection strategies and header randomization patterns"
   Task: "Research header rotation timing and human behavior simulation"
   Task: "Research site-specific header requirements and validation patterns"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - HeaderProfile entity (User-Agent, Accept-Language, Sec-Fetch-*, etc.)
   - HeaderRotation entity (timing, intervals, patterns)
   - StealthIdentity entity (complete browser identity)
   - HeaderValidation entity (response analysis, adaptation)

2. **Generate API contracts** from functional requirements:
   - GET /headers/profiles - List available header profiles
   - POST /headers/rotate - Trigger manual header rotation
   - GET /headers/current - Get current header configuration
   - POST /headers/validate - Validate headers against site response
   - GET /headers/stats - Get header usage statistics
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Header rotation flow → integration test scenario
   - Anti-detection validation → integration test scenario
   - Multi-worker coordination → integration test scenario
   - Quickstart test = end-to-end header management validation

5. **Update agent file incrementally**:
   - Run `.specify/scripts/bash/update-agent-context.sh cursor` for Claude
   - Add Playwright, header management, anti-detection context
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
- Dependency order: Models before services before integration before API
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

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

