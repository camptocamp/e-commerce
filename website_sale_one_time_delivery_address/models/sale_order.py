from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    one_time_delivery = fields.Boolean(
        string="One-Time Delivery Address",
        help=(
            "When enabled, the delivery address created during the website "
            "checkout is stored as a temporary contact with type "
            "'one_time_delivery' instead of the standard 'delivery' type. "
            "This keeps the recipient out of the customer's regular address "
            "book and is useful for reseller orders shipped to an end customer."
        ),
    )
