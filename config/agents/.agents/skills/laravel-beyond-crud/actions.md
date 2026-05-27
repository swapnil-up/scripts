# Actions

## Purpose

Encapsulate a single business operation as a first-class object. Actions are the "verbs" of your domain.

## Structure

```php
class CreateInvoiceAction
{
    public function __construct(
        private CreateInvoiceLineAction $createInvoiceLineAction,
        private GeneratePdfAction $generatePdfAction,
    ) {}

    public function execute(InvoiceData $invoiceData): Invoice
    {
        $invoice = Invoice::create($invoiceData->toArray());

        foreach ($invoiceData->lines as $lineData) {
            $this->createInvoiceLineAction->execute($invoice, $lineData);
        }

        $this->generatePdfAction->execute($invoice);

        return $invoice;
    }
}
```

## Conventions

| Aspect | Convention |
|--------|-----------|
| Public method | `execute()` — avoids collision with Laravel's `handle()` |
| Suffix | `Action` — prevents naming collisions with controllers, commands, jobs |
| Constructor DI | Framework-injected dependencies (other actions, services) |
| `execute()` params | Runtime data (DTOs, model IDs, etc.) |
| Return type | The result of the operation (model, bool, void, etc.) |

## Composition

Actions compose other actions via constructor injection:

```php
class CreateInvoiceAction
{
    public function __construct(
        private CreateInvoiceLineAction $createInvoiceLineAction,
        private VatCalculator $vatCalculator,
    ) {}
}
```

Keep the chain shallow — deep nesting is a code smell.

## Using Native Enums

Actions receive and return domain objects. When working with enums, use them directly:

```php
class CancelBookingAction
{
    public function execute(Booking $booking): Booking
    {
        $booking->status = BookingStatus::Cancelled;
        $booking->save();

        return $booking;
    }
}
```

## Testing

```
setup (factories + DTOs) → execute → assert (DB state, returned model)
```

Test the action's behavior, not its internals. Mock I/O-heavy sub-actions (PDF generation, mail sending) by replacing them in the container.

```php
/** @test */
public function it_creates_an_invoice()
{
    $invoiceData = InvoiceDataFactory::new()
        ->addLine(InvoiceLineDataFactory::new()->withPrice(10_00))
        ->create();

    $invoice = app(CreateInvoiceAction::class)->execute($invoiceData);

    $this->assertDatabaseHas('invoices', ['id' => $invoice->id]);
    $this->assertCount(1, $invoice->lines);
}
```

## When to Use

- Any non-trivial business operation (CRUD beyond a single `Model::create()`)
- Operations that coordinate multiple steps
- Operations that need to be reused from multiple entry points (controllers, commands, jobs)
