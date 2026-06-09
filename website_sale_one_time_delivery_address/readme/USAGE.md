To use this module, you need to:

1.  Add products to the cart and go to the checkout.
2.  In the delivery section, enable *One-Time Delivery Address*.
3.  Enter the final recipient address.
4.  Submit the delivery address form.

Result:

- a child contact is created on the reseller with type
  `one_time_delivery`
- the sale order shipping partner points to that new contact
- the sale order invoice partner remains the reseller, even if the
  browser submits a delivery-as-billing value
- the *Same as delivery address* toggle is hidden while the option is
  enabled, so the temporary delivery address can never be reused as the
  billing address

If the shopper disables the option, the standard website sale delivery
address behavior is kept and a regular `delivery` address is created
instead.

## Automatic archiving

One-time delivery contacts are temporary by nature. A scheduled garbage
collection routine (`@api.autovacuum`, run by the daily *Base: Auto-vacuum
internal data* cron) automatically archives a `one_time_delivery` contact
once every sale order it ships to is finished: all related stock pickings
have reached a terminal state (`done` or `cancel`). This covers delivered
orders as well as fully cancelled ones. Contacts that are still awaiting a
delivery, or that are not linked to any order, are left untouched.
Archiving is reversible and preserves the order history.
