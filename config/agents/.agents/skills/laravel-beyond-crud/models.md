# Models

## Philosophy

Models are **data oriented**, not **behavior oriented**. They provide structured access to persisted data. Business logic lives in Actions.

## What Models SHOULD Have

- **Relationships** — `belongsTo`, `hasMany`, etc.
- **Casts** — including native **PHP 8.1 enum casting** (Laravel 10+)
- **`$fillable` / `$guarded`** — mass assignment protection
- **Custom query builder wiring** — `newEloquentBuilder()`
- **Custom collection wiring** — `newCollection()`
- **Simple accessors** — for derived data that can't be precomputed

```php
class Property extends Model
{
    protected $fillable = ['name', 'type', 'address', /* ... */];

    protected function casts(): array
    {
        return [
            'monthly_rent' => 'integer',
            'bedrooms' => 'integer',
            'status' => PropertyStatus::class, // native backed enum
        ];
    }

    public function bookings(): HasMany
    {
        return $this->hasMany(Booking::class);
    }

    public function newEloquentBuilder($query): PropertyQueryBuilder
    {
        return new PropertyQueryBuilder($query);
    }
}
```

## Native Enum Casting (Laravel 10+)

Laravel can automatically cast model attributes to and from PHP 8.1 backed enums:

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
$booking->status = BookingStatus::Confirmed;        // sets 'confirmed' in DB
$booking->status->value;                             // 'confirmed'
$booking->status->name;                              // 'Confirmed'
$booking->status->color();                           // custom enum method
$booking->status === BookingStatus::Confirmed;       // true
```

Querying by enum:

```php
Booking::where('status', BookingStatus::Confirmed)->get();
// or with whereEnum scope on some Laravel versions:
Booking::where('status', BookingStatus::Confirmed)->get();
```

**Note:** The `$casts` property (array) is deprecated in Laravel 10+ in favor of the `casts()` method.

## What Models Should NOT Have

- **Business logic / calculations** → move to Actions
- **Long query scopes** → move to custom QueryBuilder
- **Collection logic** (filtering, summing) → move to custom Collection
- **Side effects** (sending mail, generating PDFs) → move to Actions/Transitions

## What Changed from the Book

| Old | New |
|-----|-----|
| `protected $casts = ['status' => 'string']` with manual `match` | `protected function casts(): array` with `'status' => BookingStatus::class` |
| `spatie/laravel-enum` for enum casting | Laravel built-in backed enum casting |
| `getXAttribute()` style accessors | `Attribute::make(get: ...)` or computed columns from Actions |
