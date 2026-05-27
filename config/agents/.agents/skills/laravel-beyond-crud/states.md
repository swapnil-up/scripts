# State Pattern (with Native Enums)

## Two Approaches

Modern PHP 8.1+ offers two ways to handle states, chosen by complexity.

## Approach A: Simple Status — Native Backed Enum

Use for status fields that need simple behavior (colors, labels, basic permissions). PHP 8.1 native enums replace the old `spatie/enum` / `myclabs/php-enum` packages completely.

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
        return in_array($this, [self::Pending, self::Confirmed], true);
    }

    public function canBeConfirmed(): bool
    {
        return $this === self::Pending;
    }

    public function canBeModified(): bool
    {
        return $this === self::Pending;
    }

    public function availableActions(): array
    {
        return array_filter([
            $this->canBeCancelled() ? 'cancel' : null,
            $this->canBeConfirmed() ? 'confirm' : null,
            $this->canBeModified() ? 'modify' : null,
        ]);
    }
}
```

Laravel casts it automatically:

```php
protected function casts(): array
{
    return [
        'status' => BookingStatus::class,
    ];
}
```

Usage:

```php
$booking->status = BookingStatus::Confirmed;
$booking->status->color(); // 'blue'
$booking->status->value;   // 'confirmed'
```

**No packages, no reflection, no magic method hacks.**

## Approach B: Complex Polymorphic Behavior — Full State Pattern

Use when behavior differs significantly per state and involves the model's data.

```php
abstract class BookingState
{
    public function __construct(
        protected Booking $booking
    ) {}

    abstract public function color(): string;
    abstract public function canBeCancelled(): bool;
    abstract public function canBeConfirmed(): bool;
    abstract public function canBeModified(): bool;

    public function availableActions(): array
    {
        return array_filter([
            $this->canBeCancelled() ? 'cancel' : null,
            $this->canBeConfirmed() ? 'confirm' : null,
            $this->canBeModified() ? 'modify' : null,
        ]);
    }
}

class PendingBookingState extends BookingState
{
    public function color(): string { return 'orange'; }
    public function canBeCancelled(): bool { return true; }
    public function canBeConfirmed(): bool { return true; }
    public function canBeModified(): bool { return true; }
}

class ConfirmedBookingState extends BookingState
{
    public function color(): string { return 'blue'; }
    public function canBeCancelled(): bool { return true; }
    public function canBeConfirmed(): bool { return false; }
    public function canBeModified(): bool { return false; }
}

class ActiveBookingState extends BookingState
{
    public function color(): string { return 'green'; }
    public function canBeCancelled(): bool { return false; }
    public function canBeConfirmed(): bool { return false; }
    public function canBeModified(): bool { return false; }
}
```

### Wiring via Native Enum Bridge

Keep the DB column as a backed enum, and resolve the state class from it:

```php
enum BookingStatus: string
{
    case Pending = 'pending';
    case Confirmed = 'confirmed';
    case Active = 'active';
    // ...

    public function resolveState(Booking $booking): BookingState
    {
        return match ($this) {
            self::Pending => new PendingBookingState($booking),
            self::Confirmed => new ConfirmedBookingState($booking),
            self::Active => new ActiveBookingState($booking),
            // ...
        };
    }
}

// On the model:
public function state(): Attribute
{
    return Attribute::make(
        get: fn() => $this->status->resolveState($this)
    );
}
```

This gives you the best of both:
- Database stores `'pending'`, `'confirmed'` etc. via a backed enum (type-safe, queryable)
- Runtime behavior delegates to polymorphic state classes

## Decision Tree: Enum vs State Pattern

```
Is the behavior just colors/labels/permissions?
  ├── Yes → Use a backed enum with methods (Approach A)
  └── No → Does the behavior depend on the model's data?
       ├── No → Use a backed enum with methods
       └── Yes → Use the full state pattern (Approach B)
```

Rule of thumb: if you find yourself writing the same `if ($x->isFoo())` check in many places, those behaviors belong in state classes.

## States Without Transitions

An object can have a state that never changes. The state pattern still applies (e.g., invoice type: credit vs debit).

```php
enum InvoiceType: string
{
    case Debit = 'debit';
    case Credit = 'credit';

    public function mustBePaid(): bool
    {
        return match ($this) {
            self::Credit => false,
            self::Debit => true,
        };
    }
}
```

## What Changed from the Book

| Old (book) | New (modern) |
|------------|-------------|
| `spatie/enum` with `@method static self FOO()` DocBlocks | PHP 8.1 native `enum` keyword |
| `spatie/laravel-enum` for model casting | Laravel built-in `casts: ['status' => StatusEnum::class]` |
| `abstract static function value(): string` on state class | Backed enum's built-in `->value` |
| Magic `__callStatic` for enum instantiation | `EnumCase::Foo` syntax with IDE support |
