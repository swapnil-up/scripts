# Custom Collections

Extend Eloquent's Collection to encapsulate iteration logic.

```php
class BookingCollection extends Collection
{
    public function confirmed(): self
    {
        return $this->filter(fn (Booking $booking) =>
            $booking->status === BookingStatus::Confirmed
        );
    }

    public function cancellable(): self
    {
        return $this->filter(fn (Booking $booking) =>
            $booking->status->canBeCancelled()
        );
    }

    public function upcoming(): self
    {
        return $this->filter(fn (Booking $booking) =>
            $booking->check_in->isFuture()
        );
    }

    public function totalNights(): int
    {
        return $this->sum(fn (Booking $booking) =>
            $booking->check_in->diffInDays($booking->check_out)
        );
    }
}
```

Wire on model:

```php
public function newCollection(array $models = []): BookingCollection
{
    return new BookingCollection($models);
}
```

Now all relationship collections automatically use your custom class:

```php
$property->bookings->confirmed()->totalNights();
```
