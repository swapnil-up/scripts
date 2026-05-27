---
name: laravel-beyond-crud
description: Domain-oriented Laravel patterns from Brent Roose's book — DTOs, Actions, State pattern, Transitions, slim Models, custom QueryBuilders/Collections, immutable test Factories, and App/Domain separation. Updated for PHP 8.2+, Laravel 12, and Inertia.
---

# Laravel Beyond CRUD

Patterns for building larger-than-average Laravel applications, based on Brent Roose's book. The core philosophy: group code by **business concept** (domain) rather than by **technical property** (controllers, models, etc.).

This skill is updated from the original book (2020) to reflect **PHP 8.1+ native enums**, **readonly classes**, **Laravel 11+ bootstrap**, and **Inertia-based frontends**.

## Project Structure

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

```
app/
  App/Admin/          ← HTTP application(s), grouped by module
    Properties/
      Controllers/
      Requests/
    Bookings/
      Controllers/
  Domain/             ← Business logic, grouped by domain
    Properties/
      Actions/
      DataTransferObjects/
      Models/
      States/
    Bookings/
      Actions/
      Collections/
      DataTransferObjects/
      Models/
      QueryBuilders/
      States/
      Transitions/
  Support/            ← Shared utilities
```

## Core Patterns

### 1. Domain-Oriented Structure

Separate **domain** (business logic) from **application** (HTTP, console, API). Domains are self-contained — each has its own Models, Actions, States, etc. Applications consume domains. Multiple applications can share one domain.

See [domain-structure.md](domain-structure.md).

### 2. Data Transfer Objects (DTOs)

Typed, structured data objects. Every piece of data entering the domain from outside should be a DTO. Use **`readonly` classes** (PHP 8.1+) with constructor property promotion — no package needed.

```php
readonly class PropertyData
{
    public function __construct(
        public string $name,
        public string $type,
        public int $monthly_rent,
    ) {}

    public static function fromRequest(array $data): self
    {
        return new self(
            name: $data['name'],
            monthly_rent: (int) ($data['monthly_rent'] * 100),
        );
    }

    public function toArray(): array
    {
        return get_object_vars($this);
    }
}
```

No reflection, no package, no mutable properties. PHP 8.2+ `readonly class` makes every property implicitly `readonly`.

See [dto.md](dto.md).

### 3. Actions

Single-responsibility classes encapsulating one business operation. One public method (`execute`). Dependencies injected via constructor, runtime data via `execute` parameters.

```php
class CreatePropertyAction
{
    public function __construct(
        private CalculateTotalMonthlyCostAction $calculateTotalMonthlyCostAction
    ) {}

    public function execute(PropertyData $propertyData): Property
    {
        $property = Property::create($propertyData->toArray());
        $property->total_monthly_cost = $this->calculateTotalMonthlyCostAction->execute($property);
        $property->save();
        return $property;
    }
}
```

Actions can compose other actions. Suffix with `Action` to avoid naming collisions with controllers, commands, jobs, etc.

See [actions.md](actions.md).

### 4. Slim Models

Models should **not** contain business logic. Keep them to:
- Relationships
- Casts (including native **PHP 8.1 enum casting**)
- `$fillable` / `$guarded`
- Custom collection/query builder wiring

Move scopes → custom QueryBuilders. Move collection logic → custom Collections. Move calculations → Actions.

```php
class Booking extends Model
{
    protected function casts(): array
    {
        return [
            'check_in' => 'date',
            'check_out' => 'date',
            'status' => BookingStatus::class, // native backed enum
        ];
    }

    public function newEloquentBuilder($query): BookingQueryBuilder
    {
        return new BookingQueryBuilder($query);
    }

    public function newCollection(array $models = []): BookingCollection
    {
        return new BookingCollection($models);
    }
}
```

See [models.md](models.md).

### 5. State Pattern (with Native Enums)

Two approaches, chosen by complexity:

**A. Simple status — use a PHP 8.1 native backed enum:**

```php
enum BookingStatus: string
{
    case Pending = 'pending';
    case Confirmed = 'confirmed';
    case Active = 'active';
    case Completed = 'completed';
    case Cancelled = 'cancelled';

    public function color(): string
    {
        return match ($this) {
            self::Pending => 'orange',
            self::Confirmed => 'blue',
            self::Active => 'green',
            self::Completed => 'gray',
            self::Cancelled => 'red',
        };
    }

    public function canBeCancelled(): bool
    {
        return in_array($this, [self::Pending, self::Confirmed]);
    }
}
```

Laravel casts it automatically: `'status' => BookingStatus::class`.

**B. Complex polymorphic behavior — use the full State pattern:**

```php
abstract class BookingState
{
    public function __construct(protected Booking $booking) {}

    abstract public function color(): string;
    abstract public function canBeCancelled(): bool;
    abstract public function canBeConfirmed(): bool;

    public function availableActions(): array { /* ... */ }
}

class PendingBookingState extends BookingState
{
    public function color(): string { return 'orange'; }
    public function canBeCancelled(): bool { return true; }
    public function canBeConfirmed(): bool { return true; }
}
```

The booking stores a `BookingStatus` enum in DB, and the state class is resolved from it:

```php
use Attribute;

public function state(): Attribute
{
    return Attribute::make(
        get: fn() => $this->status->resolveState($this)
    );
}
```

Where `BookingStatus::resolveState()` returns the appropriate state class. See [states.md](states.md).

### 6. Transitions

Separate from states. A Transition validates, executes the state change, and performs side effects (logging, notifications). States are for reading data; Transitions are for changing it.

```php
abstract class BookingTransition
{
    abstract public function execute(Booking $booking): Booking;
    abstract protected function validate(Booking $booking): void;
    protected function afterTransition(Booking $booking): void {}
}
```

See [transitions.md](transitions.md).

### 7. Custom Query Builders & Collections

Extend Eloquent's Builder/Collection to encapsulate query logic:

```php
class BookingQueryBuilder extends Builder
{
    public function whereConfirmed(): self { return $this->where('status', 'confirmed'); }
    public function whereOverlaps(Carbon $checkIn, Carbon $checkOut): self { /* … */ }
}

class BookingCollection extends Collection
{
    public function confirmed(): self { return $this->filter(fn($b) => $b->status === 'confirmed'); }
    public function totalNights(): int { /* … */ }
}
```

See [query-builders.md](query-builders.md) and [collections.md](collections.md).

### 8. Immutable Test Factories

Composable, immutable factory classes with a static `new()` constructor and fluent modifiers that return a clone.

```php
class BookingFactory
{
    public static function new(): self { return new self(); }

    public function create(array $extra = []): Booking
    {
        return Booking::create(array_merge([
            'property_id' => PropertyFactory::new()->create()->id,
            'check_in' => now()->addDay(),
            'check_out' => now()->addDays(3),
            'status' => BookingStatus::Pending,
        ], $extra));
    }

    public function confirmed(): self
    {
        $clone = clone $this;
        $clone->status = BookingStatus::Confirmed;
        return $clone;
    }
}
```

See [factories.md](factories.md).

### 9. View Models (Inertia-friendly)

View models encapsulate data preparation. With Inertia, they transform domain data into props:

```php
class BookingIndexViewModel
{
    public function __construct(
        private User $user,
        private ?BookingStatus $status = null,
    ) {}

    public function toProps(): array
    {
        return [
            'bookings' => $this->getBookings(),
            'filters' => ['statuses' => BookingStatus::cases()],
        ];
    }

    private function getBookings(): array
    {
        return Booking::query()
            ->when($this->status, fn($q) => $q->where('status', $this->status))
            ->latest()
            ->paginate(15)
            ->through(fn (Booking $b) => [
                'id' => $b->id,
                'status' => $b->status->value,
                'status_color' => $b->status->color(),
                'can_cancel' => $b->status->canBeCancelled(),
            ])
            ->toArray();
    }
}
```

See [view-models.md](view-models.md).

### 10. Application-Layer HTTP Query Builders

Dedicated classes for parsing HTTP query parameters and applying filters/sorts:

```php
class PropertyIndexQuery extends \Spatie\QueryBuilder\QueryBuilder
{
    public function __construct(Request $request)
    {
        $query = Property::query()->with('bookings');
        parent::__construct($query, $request);
        $this->allowedFilters(['city', 'status', 'bedrooms'])
             ->allowedSorts('name', 'monthly_rent');
    }
}
```

### 11. Jobs as Application Code

Jobs belong in the application layer. They orchestrate queue configuration and delegate to domain Actions:

```php
class SendInvoiceJob implements ShouldQueue
{
    public function handle(SendInvoiceMailAction $action): void
    {
        $action->execute($this->invoice);
    }
}
```

For simple cases, `spatie/laravel-queueable-action`:
```php
$someAction->onQueue()->execute($data);
```

## Testing Strategy

| What | How | Notes |
|------|-----|-------|
| DTOs | Minimal — test mapping from request data if using static constructors | `readonly` + types handle the rest |
| Actions | Integration-style — setup DTOs with factories, execute, assert DB/state | Mock I/O side effects (PDF, mail) |
| States | Unit tests per state class | Use native enums directly for simple cases |
| Transitions | Test validation + execution + side effects | |
| Collections | Unit tests — create models, call collection methods, assert | |
| Query Builders | Integration — create models in various states, query, assert | |
| View Models | Unit tests — construct with mock data, assert `toProps()` output | |

## Guiding Principles

1. **Group by meaning, not by technology** — domain groups > technical layers
2. **Embrace the framework, don't fight it** — use Laravel's native enum casting, auto-discovery, etc.
3. **Pragmatism over purity** — a `fromRequest()` method on a DTO is acceptable pragmatism
4. **Reduce cognitive load** — make it obvious where to find code for a feature
5. **Prefer polymorphism over conditionals** — the state pattern exists to eliminate if/else
6. **Separate state from transition** — states read, transitions write
7. **Actions for behavior, models for data** — keep models slim
8. **Immutable factories** — modifiers clone, don't mutate
9. **Test behavior, not implementation** — integration-style tests for actions

## PHP Version Requirements

All code in this skill targets **PHP 8.1 minimum** (native enums, readonly properties). PHP 8.2+ allows `readonly class`. Features used:

| Feature | PHP Version |
|---------|-------------|
| Constructor property promotion | 8.0 |
| Named arguments | 8.0 |
| `match` expression | 8.0 |
| `readonly` properties | 8.1 |
| Native enums | 8.1 |
| `readonly class` | 8.2 |

## References

- [Spatie packages](https://spatie.be/open-source): `spatie/laravel-query-builder` (active), `spatie/laravel-queueable-action` (active)
- Tim MacDonald on [Dedicated Query Builders](https://timacdonald.me/dedicated-eloquent-model-query-builders) and [Custom Collections](https://timacdonald.me/giving-collections-a-voice/)
- PHP 8.1 [native enums](https://www.php.net/manual/en/language.enumerations.php)
- PHP 8.1 [readonly properties](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties)
