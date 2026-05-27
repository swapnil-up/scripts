# Domain-Oriented Structure

## The Core Idea

Group code by **business concept** (what it means) rather than **technical property** (what it is). A client doesn't ask you to "work on the controllers" — they ask you to "work on invoicing" or "fix the booking flow".

## Namespace Setup

In `composer.json`:

```json
{
  "autoload": {
    "psr-4": {
      "App\\": "app/App/",
      "Domain\\": "app/Domain/",
      "Support\\": "app/Support/"
    }
  }
}
```

## Directory Layout

```
app/
  Domain/Properties/         ← One directory per domain
    Actions/                 ← Business operations
    Collections/             ← Custom Eloquent collections
    DataTransferObjects/     ← Typed data (readonly classes)
    Events/                  ← Domain events
    Exceptions/              ← Domain-specific exceptions
    Models/                  ← Eloquent models (slim)
    QueryBuilders/           ← Custom Eloquent builders
    Rules/                   ← Validation rules
    States/                  ← State classes (or native enums)
    Transitions/             ← State transitions
  App/Admin/                 ← HTTP application, grouped by module
    Properties/
      Controllers/
      Requests/
    Bookings/
      Controllers/
    Support/                 ← Shared app-level code
      Middleware/
      Requests/
  Support/                   ← Project-wide utilities
```

## Laravel 11+ Bootstrap

With Laravel 11+, the `bootstrap/app.php` uses a fluent API. No need to extend `Illuminate\Foundation\Application`:

```php
// bootstrap/app.php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: $_ENV['APP_BASE_PATH'] ?? dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        // $middleware->web(append: [/* ... */]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        //
    })->create();
```

The `App\\` namespace root is read from `composer.json` autoload, so no custom `Application` class is needed for namespace overrides.

### If You Need a Custom App Path

If you must keep a custom `Application` class (e.g., for overriding `path()`), register it in `bootstrap/app.php`:

```php
use App\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: $_ENV['APP_BASE_PATH'] ?? dirname(__DIR__))
    ->withRouting(/* ... */)
    ->withMiddleware(/* ... */)
    ->withExceptions(/* ... */)
    ->create();
```

Where `Application` extends `Illuminate\Foundation\Application` only to override `path()`.

## Key Rules

- **Domain has no framework coupling** beyond Laravel's Eloquent/helpers
- **Domain never imports from App** — domains are consumed by applications, not the reverse
- **Applications import from Domain** — controllers call actions, use DTOs, etc.
- **Modules within App are optional** but recommended once an app grows beyond ~20 files in a flat directory
- **Support is the dumping ground** for code that doesn't belong to any domain (base classes, calculators, etc.)

## What Changed from the Book

| Old | New |
|-----|-----|
| Custom `Application` class extending `Illuminate\Foundation\Application` to set `$namespace` and override `path()` | Unnecessary in Laravel 11+ — `composer.json` autoload determines root namespace |
| `$app = new Application(...)` in bootstrap | `return Application::configure(...)->create()` fluent API |
