# View Models (Inertia-friendly)

## Why

View models extract view-specific data logic from controllers. They answer: "what props does this page need?" With Inertia, they transform domain data into the exact shape the Vue/React page expects.

## Basic Pattern

```php
class BookingIndexViewModel
{
    public function __construct(
        private User $user,
        private ?BookingStatus $status = null,
        private ?string $search = null,
    ) {}

    public function toProps(): array
    {
        return [
            'bookings' => $this->getBookings(),
            'filters' => [
                'statuses' => BookingStatus::cases(),
                'current_status' => $this->status?->value,
                'search' => $this->search,
            ],
        ];
    }

    private function getBookings(): array
    {
        return Booking::query()
            ->with('property')
            ->when($this->status, fn($q) => $q->where('status', $this->status))
            ->when($this->search, fn($q) => $q->where('reference', 'like', "%{$this->search}%"))
            ->latest()
            ->paginate(15)
            ->through(fn (Booking $booking): array => [
                'id' => $booking->id,
                'reference' => $booking->reference,
                'property_name' => $booking->property->name,
                'check_in' => $booking->check_in->format('M d, Y'),
                'check_out' => $booking->check_out->format('M d, Y'),
                'status' => $booking->status->value,
                'status_color' => $booking->status->color(),
                'available_actions' => $booking->status->availableActions(),
            ])
            ->toArray();
    }
}
```

## In Controller

```php
public function index(Request $request): Response
{
    $viewModel = new BookingIndexViewModel(
        user: $request->user(),
        status: BookingStatus::tryFrom($request->get('status')),
        search: $request->get('search'),
    );

    return Inertia::render('Admin/Bookings/Index', $viewModel->toProps());
}
```

## Inertia-specific Considerations

### Props are JSON — serialize everything
Inertia sends props as JSON to the frontend. Models, Carbon dates, and enums must be serialized (strings, arrays, numbers) before they reach the Vue component. The ViewModel is the right place to do this.

### Reusable prop transformers
For complex serialization, extract a dedicated transformer:

```php
class BookingPropTransformer
{
    public static function forList(Booking $booking): array
    {
        return [
            'id' => $booking->id,
            'property_name' => $booking->property->name,
            'status' => $booking->status->value,
            'status_color' => $booking->status->color(),
            'check_in' => $booking->check_in->format('M d, Y'),
        ];
    }

    public static function forShow(Booking $booking): array
    {
        // More detailed serialization
    }
}
```

### Shared ViewModel data as a service
If the same grouping logic is needed in multiple controllers, extract a service:

```php
class BookingFilterService
{
    public function availableFilters(): array
    {
        return [
            'statuses' => collect(BookingStatus::cases())->map(fn($s) => [
                'value' => $s->value,
                'label' => $s->label(),
                'color' => $s->color(),
            ]),
        ];
    }
}
```

## Relationship to Laravel Resources

Laravel API Resources are for one-to-one model → array mapping. ViewModels are broader — they coordinate multiple resources, filters, pagination, and page-specific metadata. In a pure Inertia app without a separate API, ViewModels naturally replace many resource use cases.

## What Changed from the Book

| Old (Blade) | New (Inertia) |
|-------------|---------------|
| ViewModel implements `Arrayable` / `Responsable` | ViewModel exposes `toProps(): array` |
| Passed to Blade: `view('blog.form', $viewModel)` | Passed to Inertia: `Inertia::render('Page', $viewModel->toProps())` |
| Methods return Collections / Models | Methods return serialized arrays (JSON-safe) |
| View composers for global data | Shared Inertia props or middleware |
