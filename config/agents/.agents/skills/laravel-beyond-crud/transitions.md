# Transitions

## Separation from States

- **States** read — they provide behavior based on current state
- **Transitions** write — they change state and perform side effects

## Base Transition

```php
abstract class BookingTransition
{
    abstract public function execute(Booking $booking): Booking;
    abstract protected function validate(Booking $booking): void;
    protected function afterTransition(Booking $booking): void {}
}
```

## Concrete Transition

```php
class ConfirmBookingTransition extends BookingTransition
{
    public function execute(Booking $booking): Booking
    {
        $this->validate($booking);

        $booking->status = BookingStatus::Confirmed;
        $booking->save();

        $this->afterTransition($booking);

        return $booking;
    }

    protected function validate(Booking $booking): void
    {
        if (! $booking->status->canBeConfirmed()) {
            throw new \DomainException(
                "Cannot confirm booking in {$booking->status->value} state"
            );
        }

        if ($booking->check_in->isPast()) {
            throw new \DomainException(
                "Cannot confirm booking with past check-in date"
            );
        }
    }

    protected function afterTransition(Booking $booking): void
    {
        Log::info('Booking confirmed', ['id' => $booking->id]);
    }
}
```

## Wrapping in an Action

Transitions are often wrapped by an Action for a cleaner public API:

```php
class ConfirmBookingAction
{
    public function __construct(
        private ConfirmBookingTransition $transition
    ) {}

    public function execute(Booking $booking): Booking
    {
        return $this->transition->execute($booking);
    }
}
```

## Usage in Controller

```php
public function confirm(Booking $booking, ConfirmBookingAction $action)
{
    try {
        $action->execute($booking);
        return back()->with('success', 'Booking confirmed!');
    } catch (\DomainException $e) {
        return back()->with('error', $e->getMessage());
    }
}
```
