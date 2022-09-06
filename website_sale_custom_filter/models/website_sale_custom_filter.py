# Copyright 2022 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class WebsiteSaleCustomFilter(models.Model):
    _name = "website.sale.custom.filter"
    _description = "website.sale.custom.filter"
    _inherit = "mail.thread"

    def _default_website(self):
        return self.env["website"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )

    name = fields.Char(required=True, string="Filter name")
    sequence = fields.Integer(default=10)
    website_category_ids = fields.Many2many(
        "product.public.category", required=True, string="Website category"
    )
    filter_collapsed = fields.Boolean()
    filter_type = fields.Selection(
        [("numerical", "Numerical"), ("value", "Value based")],
        default="numerical",
        string="Display type",
    )
    product_model_id = fields.Many2one(
        "ir.model",
        readonly=True,
        default=lambda self: self.env.ref("product.model_product_product"),
    )
    numerical_filter_field_id = fields.Many2one(
        "ir.model.fields",
        string="Numerical filter",
        domain="[('ttype','in',('float','integer')),('model_id','=','product.product')]",
    )
    custom_filter_value_ids = fields.One2many(
        "website.sale.custom.filter.value",
        "custom_filter_id",
        string="Custom filter values",
        store=True,
    )
    website_ids = fields.Many2many(
        "website",
        relation="filter_website_rel",
        string="website",
        default=_default_website,
        ondelete="cascade",
    )
    min_value = fields.Float()
    max_value = fields.Float()


class Website(models.Model):
    _inherit = "website"

    def get_filters(self):
        self.ensure_one()
        filter_obj = self.env["website.sale.custom.filter"]
        # not used ATM, filter by category if specified
        # -> find a way to use (search_categories_ids) in controller vals
        return filter_obj.search([("website_ids", "=", self.id)])
