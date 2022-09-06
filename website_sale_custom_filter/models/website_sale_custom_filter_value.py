# Copyright 2022 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class WebsiteSaleCustomFilterValue(models.Model):
    _name = "website.sale.custom.filter.value"
    _description = "website.sale.custom.filter.value"

    name = fields.Char(required=True, string="Value name")
    sequence = fields.Integer(required=True, default=10)
    custom_filter_id = fields.Many2one(
        "website.sale.custom.filter",
        ondelete="cascade",
        required=True,
        string="Filter ID",
    )
    display = fields.Selection(
        [("checkbox", "Checkbox"), ("color", "Color")],
        default="checkbox",
        string="Display type",
    )
    value_filter_id = fields.Many2one("ir.filters", string="Value filter ID")
    selected_product_tmpl_ids = fields.Many2many(
        "product.template", string="Selected product template"
    )
