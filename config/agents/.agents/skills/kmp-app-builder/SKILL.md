---
name: kmp-app-builder
description: Agent specialized in building Kotlin Multiplatform apps, especially Android-first with optional iOS support. Follows best practices for module structure, code sharing, and platform-specific boundaries.
---

## What to optimize for

- Keep shared code small, boring, and testable.
- Put app entry points in separate platform modules.
- Share business logic, networking, persistence, and state; do not blindly share UI.
- Use the default Kotlin Multiplatform hierarchy before inventing custom source-set wiring.
- Prefer official, current KMP APIs and samples over old blog-post patterns.

## Architecture decision rule

Choose the smallest architecture that still keeps dependencies pointed inward.

### Default structure

Use this shape unless the repo already has a clear alternative:

```text
androidApp/
iosApp/

shared/
  commonMain/
  commonTest/
  androidMain/
  iosMain/

core/
  network/
  database/
  analytics/
  designsystem/

features/
  home/
  auth/
  settings/
```

Guidelines:

- App modules contain only platform entry points and wiring.
- `shared` or `core` modules contain reusable logic.
- Feature modules should not depend on each other directly.
- Keep platform code at the edge and shared code in the middle.

## Layering rule inside a feature

Each feature should follow a simple three-layer split:

```text
feature/
  domain/
  data/
  presentation/
```

### Domain

Contains:

- models
- repository interfaces
- use cases
- business rules

Domain must not depend on UI, Ktor, Room, SQLDelight, Android APIs, or platform-specific code.

### Data

Contains:

- repository implementations
- DTOs
- database entities
- remote/local data sources
- mapping code

Data must not leak DTOs or entities upward.

### Presentation

Contains:

- ViewModels
- UI state
- events/actions
- mappers to UI models

Presentation must not talk to HTTP clients or databases directly.

## Source-set rule

Use the Kotlin Multiplatform source-set hierarchy the way the compiler expects it:

- `commonMain` for code shared across all targets.
- `androidMain` and `iosMain` for platform-specific code.
- intermediate source sets only when multiple targets genuinely share code.
- `expect`/`actual` only at boundaries where platform APIs are unavoidable.

Do not invent custom `dependsOn` chains unless there is a clear target-sharing reason.

## Sharing rule

Share these aggressively:

- domain logic
- validation
- serialization models that are platform-neutral
- networking abstractions
- persistence abstractions
- state machines
- error mapping
- formatting that is not platform-specific

Do not share these unless there is a strong reason:

- Activities, Fragments, and Android navigation glue
- permissions
- notifications
- deep links
- platform-specific UI wrappers
- OS-specific services

## UI rule

### If the repo uses shared UI

Use Compose Multiplatform for shared UI when the project is intentionally cross-platform UI sharing.

Keep composables:

- stateless where possible
- driven by immutable state
- free of business logic
- free of direct data fetching

### If the repo uses native UI

Use Jetpack Compose on Android and native UI on iOS.

In this case, share only the logic layer, not the screen layer.

## State management rule

Every screen should follow unidirectional data flow:

```text
UI -> Action/Event -> ViewModel -> Use Case -> Repository -> Data Source
```

Preferred state types:

- `StateFlow` for observable screen state
- `Flow` for streams
- immutable `data class` state objects
- sealed `Action` / `Event` types

Do not allow UI to mutate shared state directly.

## Coroutines rule

Use coroutines everywhere asynchronous work happens.

- Prefer `suspend` functions for one-shot work.
- Prefer `Flow` or `StateFlow` for streams and UI state.
- Never use `GlobalScope`.
- Never launch long-running work from composables.
- Scope work to ViewModels, repositories, or explicit lifecycle owners.

## Networking rule

Default networking stack:

- Ktor client
- `kotlinx.serialization`
- coroutines

Repository pattern is required.

Flow:

```text
API response -> DTO -> mapper -> domain model
```

Rules:

- DTOs stay inside data layers.
- Mappers convert DTOs into domain models.
- Handle exceptions at the repository boundary.
- Do not throw raw network exceptions into UI.

## Persistence rule

For Android-first KMP, default to the current Room KMP path when the team already knows Room and the queries are not unusually complex.

Choose SQLDelight when:

- queries are complex
- SQL ownership matters
- the schema is central to the app’s design
- you want explicit SQL control

General rules:

- persistence code stays in data layers
- database entities do not escape to presentation
- migrations must be explicit and tested

## Dependency injection rule

Prefer constructor injection.

Good options:

- Kotlin Inject
- Koin if the project already uses it

Avoid:

- service locators
- hidden globals
- manually wiring everything in UI code

Dependencies should be passed in, not looked up.

## Android rule

Android code should stay thin.

Android modules may contain:

- Compose UI
- navigation
- platform permissions
- Android-specific services
- platform adapters

Android modules should not contain:

- business rules
- database logic
- network clients
- cross-platform models that belong in shared code

## iOS rule

When exposing Kotlin code to Swift:

- keep APIs simple
- avoid deep nesting in exported types
- prefer small, stable boundaries
- expose use-case style entry points rather than internals

If integration friction appears, fix the boundary instead of spreading platform code into shared logic.

## Testing rule

Test at the same layer where the logic lives.

### Minimum expectation

- unit tests for domain and data logic
- mapper tests for DTO/entity conversions
- ViewModel tests for state transitions
- UI tests for critical flows when practical

### Test priorities

1. business rules
2. repository behavior
3. state transitions
4. serialization and mapping
5. integration edges

## Build and tooling rule

- Prefer current official templates and wizard-generated structure over archived templates.
- Keep Gradle configuration simple and centralized.
- Add platform-specific dependencies only to the source set that needs them.
- Use KSP where the library requires it.
- Keep the shared module free of accidental Android-only or JVM-only dependencies.

## Library selection rule

Prefer the stack that appears repeatedly in official and high-quality KMP samples:

- Compose Multiplatform for shared UI
- Ktor for networking
- kotlinx.serialization for JSON
- coroutines/Flow for async and state
- Room KMP or SQLDelight for persistence
- Koin or another KMP-friendly DI approach that is already in the repo

Do not introduce a new library unless it clearly solves a real problem in the current codebase.

## What the agent should do first when asked to add a feature

1. Find the correct module and source set.
2. Identify whether the code belongs in domain, data, or presentation.
3. Reuse existing types before creating new ones.
4. Add tests for the new behavior.
5. Keep platform code at the edge.
6. Only use `expect`/`actual` if an API truly needs platform specialization.

## What the agent should avoid

- giant shared modules
- business logic in composables
- platform APIs in `commonMain`
- DTOs escaping into UI
- feature-to-feature coupling
- unchecked dependency additions
- overusing `expect`/`actual`
- premature abstraction
- rewriting the architecture for a small task

## Red flags that usually mean the design is wrong

- a ViewModel that knows about HTTP or SQL details
- a composable that fetches from the network
- a repository that returns DTOs directly
- a shared module that contains everything
- custom source-set wiring without a clear target-sharing need
- platform-specific code leaking into common code

## Default agent prompt

When implementing a KMP change, the agent should behave as follows:

- respect existing module boundaries
- keep common code platform-neutral
- prefer the simplest working architecture
- use official multiplatform-compatible libraries
- add tests for new business logic
- keep UI declarative and state-driven
- keep platform-specific code isolated

## Sources that informed this guide

- Kotlin Multiplatform project structure and common code rules
- Kotlin hierarchical source sets and `expect`/`actual`
- Kotlin Multiplatform recommended structure and sharing guidance
- Android’s Room KMP documentation
- Android’s Kotlin Multiplatform overview
- Kotlin Multiplatform samples and KaMPKit
- Compose Multiplatform repository and docs
- Kotlin multiplatform library template