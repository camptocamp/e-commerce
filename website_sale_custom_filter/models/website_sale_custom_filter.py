# Copyright 2022 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


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

    def get_filters(self, category=False):
        self.ensure_one()
        filter_obj = self.env["website.sale.custom.filter"]
        domain = [("website_ids", "=", self.id)]
        if category:
            domain.append(("website_category_ids", "=", category.id))
        filters = filter_obj.search(domain)
        return filters


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        # modify base_domain to include selected filters
        domain = res["base_domain"][0]

        CustomFilterObj = self.env["website.sale.custom.filter"]
        CustomFilterValueObj = self.env["website.sale.custom.filter.value"]

        if options.get("custom_checkbox_filters", False):
            for _f_id, val_id in options["custom_checkbox_filters"].items():
                filter_value = CustomFilterValueObj.browse(val_id)
                selected_products = filter_value.selected_product_tmpl_ids.ids
                if selected_products:
                    domain.append(("id", "in", selected_products))
        if options.get("custom_value_filters", False):
            for f_id, val_id in options["custom_value_filters"].items():
                filter_id = CustomFilterObj.browse(int(f_id))
                filtering_field = filter_id.numerical_filter_field_id.name
                min_val = val_id.get("min_value", False)
                max_val = val_id.get("max_value", False)
                # build domain
                if min_val and min_val != val_id["available_min_value"]:
                    domain.append((filtering_field, ">=", min_val))
                if max_val and max_val != val_id["available_max_value"]:
                    domain.append((filtering_field, "<=", max_val))
        res["base_domain"][0] = domain
        return res
