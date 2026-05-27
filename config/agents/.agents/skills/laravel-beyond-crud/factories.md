# Immutable Test Factories

## Why Custom Factories

Default Laravel factories lack:
- IDE autocompletion (string-based states, magic globals)
- Composability of nested factories
- Immutability (preventing unintended mutations when reusing a factory)

Custom immutable factories are **complementary** to Laravel's built-in factories — use them for the most important domain models in your tests.

## Basic Pattern

```php
class BookingFactory
{
    private static int $number = 0;

    public static function new(): self
    {
        return new self();
    }

    public function create(array $extra = []): Booking
    {
        self::$number++;

        return Booking::create(array_merge([
            'property_id' => PropertyFactory::new()->create()->id,
            'check_in' => now()->addDay(),
            'check_out' => now()->addDays(3),
            'status' => BookingStatus::Pending,
            'reference' => 'BK-' . self::$number,
        ], $extra));
    }

    public function confirmed(): self
    {
        $clone = clone $this;
        $clone->status = BookingStatus::Confirmed;
        return $clone;
    }

    public function forProperty(Property $property): self
    {
        $clone = clone $this;
        $clone->propertyId = $property->id;
        return $clone;
    }
}
```

Note the use of `BookingStatus::Pending` and `BookingStatus::Confirmed` — native enums make the factory type-safe.

## Key Rules

1. **Static `new()` constructor** — returns a fresh factory instance
2. **Immutable modifiers** — each modifier returns a `clone $this`, never mutates in place
3. **Auto-incrementing** — use a static counter for unique fields (reference numbers, etc.)
4. **`$extra` override** — `create(array $extra)` allows last-minute overrides for one-offs
5. **Nested factories** — factories call other factories to set up related models (PropertyFactory inside BookingFactory)

## Factory Composition

Factories can accept sub-factories for configuration:

```php
class InvoiceFactory
{
    public function paid(?PaymentFactory $paymentFactory = null): self
    {
        $clone = clone $this;
        $clone->status = InvoiceStatus::Paid;
        $clone->paymentFactory = $paymentFactory ?? PaymentFactory::new();
        return $clone;
    }

    public function create(array $extra = []): Invoice
    {
        $invoice = Invoice::create(/* … */);

        if ($this->paymentFactory) {
            $this->paymentFactory->forInvoice($invoice)->create();
        }

        return $invoice;
    }
}
```

Usage:

```php
$invoice = InvoiceFactory::new()
    ->paid(PaymentFactory::new()->type(PaymentType::Visa))
    ->create();
```

## Reusing Base Factories

Since factories are immutable, you can create a base and reuse:

```php
$factory = BookingFactory::new()->forProperty($property);

$confirmed = $factory->confirmed()->create();
$pending = $factory->create(); // Still pending — clone protects us
```

## Base Factory Class (optional)

```php
abstract class Factory
{
    abstract public function create(array $extra = []);

    public function times(int $count, array $extra = []): Collection
    {
        return collect()->times($count, fn() => $this->create($extra));
    }
}
```
