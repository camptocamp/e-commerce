This module extends the website checkout delivery flow for
reseller-driven orders.

When the shopper enables the one-time delivery option during checkout,
the delivery address entered on the website is stored as a child contact
of the reseller with type `one_time_delivery`.

This allows downstream processes such as EDI to keep a dedicated
recipient contact on the sale order while preserving the reseller as the
billing partner.

Main behavior:

- adds a one-time delivery toggle to the checkout page
- creates checkout delivery contacts with type `one_time_delivery`
- keeps the invoice address on the reseller
- keeps the shipping address on the temporary end-customer contact
- makes one-time delivery contacts available in the checkout delivery
  address list
