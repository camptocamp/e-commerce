On the eCommerce product page, the "Specifications" display added by
`website_sale_comparison` (shown as a table, an accordion item, or
both, depending on the theme's display options) lists every attribute
of the product, including non-variant-defining ("informative")
attributes whose values can be restricted to specific variant
combinations via the attribute value's "Exclude for" configuration.

Without this module, that display always lists every configured value
of such an attribute, and never updates when the customer changes the
selected variant. This module makes it show only the value(s) actually
compatible with the combination currently selected on the page, and
refreshes it when the customer changes variant.

The comparison page (`/shop/compare`) is covered too: for each compared
product, only the value(s) compatible with that product's own variant
are listed.
