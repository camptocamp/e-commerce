# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_show_line_subtotals_tax_selection = fields.Selection(
        selection=[
            ("tax_excluded", "Tax Excluded"),
            ("tax_included", "Tax Included"),
        ],
        string="Website Tax Display",
        help=(
            "Specify how product prices are displayed on the website for this "
            "partner. Leave empty to use the website setting. Contacts without "
            "a value inherit the setting from their commercial entity."
        ),
    )
