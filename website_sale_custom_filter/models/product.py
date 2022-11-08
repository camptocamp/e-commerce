# Copyright 2022 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


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
            for _, val_id in options["custom_checkbox_filters"].items():
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
