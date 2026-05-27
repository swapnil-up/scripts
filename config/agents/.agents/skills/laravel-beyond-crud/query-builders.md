# Custom Query Builders

## Domain-Level (Eloquent)

Move query scopes from models into dedicated builder classes.

```php
class BookingQueryBuilder extends Builder
{
    public function whereConfirmed(): self
    {
        return $this->where('status', BookingStatus::Confirmed);
    }

    public function whereActive(): self
    {
        return $this->where('status', BookingStatus::Active);
    }

    public function whereOverlaps(Carbon $checkIn, Carbon $checkOut): self
    {
        return $this->where(function ($query) use ($checkIn, $checkOut) {
            $query->whereBetween('check_in', [$checkIn, $checkOut])
                ->orWhereBetween('check_out', [$checkIn, $checkOut])
                ->orWhere(function ($q) use ($checkIn, $checkOut) {
                    $q->where('check_in', '<=', $checkIn)
                      ->where('check_out', '>=', $checkOut);
                });
        });
    }

    public function forProperty(int $propertyId): self
    {
        return $this->where('property_id', $propertyId);
    }
}
```

Wire on model:

```php
public function newEloquentBuilder($query): BookingQueryBuilder
{
    return new BookingQueryBuilder($query);
}
```

Querying by native enum works naturally — Laravel casts the enum to its `value` for the DB:

```php
Booking::query()->whereConfirmed()->get();
```

## Application-Level (HTTP Queries)

Separate concerns: these classes parse HTTP query parameters and apply filters/sorts. Use `spatie/laravel-query-builder`.

```php
class BookingIndexQuery extends \Spatie\QueryBuilder\QueryBuilder
{
    public function __construct(Request $request)
    {
        $query = Booking::query()->with('property');

        parent::__construct($query, $request);

        $this
            ->allowedFilters([
                AllowedFilter::exact('status'),
                AllowedFilter::scope('date_between'),
            ])
            ->allowedSorts('check_in', 'check_out');
    }
}
```

Inject into controller:

```php
public function index(BookingIndexQuery $query)
{
    $bookings = $query->paginate(15);
    // …
}
```
