# Data Transfer Objects (DTOs)

## Why

PHP's dynamic type system means arrays are opaque. A DTO gives you:
- Static analysis / IDE autocompletion
- Guaranteed structure — you know exactly what fields exist and their types
- Self-documenting code

## Modern PHP 8.1+ Approach (preferred)

Use **`readonly` classes** (PHP 8.2+) or **`readonly` properties** (PHP 8.1). No packages needed.

```php
readonly class CustomerData
{
    public function __construct(
        public string $name,
        public string $email,
        public Carbon $birth_date,
    ) {}

    public static function fromRequest(CustomerRequest $request): self
    {
        return new self(
            name: $request->get('name'),
            email: $request->get('email'),
            birth_date: Carbon::make($request->get('birth_date')),
        );
    }

    public function toArray(): array
    {
        return get_object_vars($this);
    }
}
```

Key points:
- **`readonly class`** (PHP 8.2) makes all properties implicitly readonly
- **Constructor property promotion** eliminates boilerplate
- **`get_object_vars($this)`** handles serialization without reflection
- **Named arguments** make construction self-documenting
- **No inheritance from a base class** — plain PHP class is sufficient

## What was in the book (for context)

The book used `spatie/data-transfer-object` or a hand-rolled reflection-based base class:

```php
abstract class DataTransferObject
{
    public function __construct(array $data = []) { /* reflection */ }
    public function toArray(): array { /* reflection */ }
}
```

**This is no longer needed.** PHP 8.1+ gives you everything without reflection. The package has been archived.

## Where to Put the Factory

Two approaches:

| Approach | Pros | Cons |
|----------|------|------|
| Static `fromRequest()` on DTO | Simple, colocated | Mixes app-layer concern (Request) into domain |
| Separate `DataFactory` class | Clean separation | More files, boilerplate |

Stay pragmatic — the static `fromRequest()` approach is fine. PHP 8.0+ named arguments make the mapping explicit and type-safe.

## Naming Conventions

- Suffix with `Data`: `BookingData`, `InvoiceData`, `PropertyData`
- Place in `Domain/{Domain}/DataTransferObjects/`
- Keep them in the domain (they represent domain concepts)

## Serialization

For Eloquent `create()` / `update()`:

```php
public function toArray(): array
{
    return get_object_vars($this);
}
```

For JSON / API responses, implement `\JsonSerializable`:

```php
readonly class CustomerData implements \JsonSerializable
{
    public function jsonSerialize(): array
    {
        return get_object_vars($this);
    }
}
```

## What NOT to Put in DTOs

- Business logic
- Validation (beyond type enforcement)
- Default values that depend on runtime context
- Database interactions
