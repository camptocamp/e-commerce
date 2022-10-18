# Copyright 2022 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    # get min & max from url params for range widgets only
    def get_min_max_custom_filters(self):
        req = dict(request.httprequest.args)
        min_max_filter_vals = {}
        if req.get("min_cust_filter", False):
            for vals in req["min_cust_filter"].split(","):
                f_id, f_min_val = vals.split("_")
                f_min_val = int(f_min_val)
                if not min_max_filter_vals.get(f_id, False):
                    min_max_filter_vals[f_id] = {"min": f_min_val}
                else:
                    min_max_filter_vals[f_id]["min"] = f_min_val
        if req.get("max_cust_filter", False):
            for vals in req["max_cust_filter"].split(","):
                f_id, f_max_val = vals.split("_")
                f_max_val = int(f_max_val)
                if not min_max_filter_vals.get(f_id, False):
                    min_max_filter_vals[f_id] = {"max": f_max_val}
                else:
                    min_max_filter_vals[f_id]["max"] = f_max_val
        return min_max_filter_vals

    def get_custom_checkbox_filter_values(self):
        req = dict(request.httprequest.args)
        value_filter_data = {}
        if req.get("cust_filter"):
            filter_data = req["cust_filter"].split("&")
            for data in filter_data:
                f_id, val = data.split("-")
                if f_id in value_filter_data.keys():
                    value_filter_data[f_id].append(int(val))
                else:
                    value_filter_data[f_id] = [int(val)]
        return value_filter_data

    def get_custom_range_filter_values(self):
        cust_filter_min_max_vals = self.get_min_max_custom_filters()
        curr_website = request.env["website"].get_current_website()
        numerical_filters_available_on_website = request.env[
            "website.sale.custom.filter"
        ].search(
            [("website_ids", "=", curr_website.id), ("filter_type", "=", "numerical")]
        )
        range_filter_data = {}
        # get min max for numerical filters
        # how to handle if field from filter is related to another model?
        for num_filter in numerical_filters_available_on_website:
            col_name = num_filter.numerical_filter_field_id.name
            model_name = num_filter.numerical_filter_field_id.model
            if (
                model_name == "product.product"
            ):  # there are fields related to product.template sometimes
                model_name = "product.template"
            query = f"""
            SELECT MIN({col_name}), MAX({col_name}) FROM {model_name.replace('.','_')}"""
            request.env.cr.execute(query)
            available_min_value, available_max_value = request.env.cr.fetchone()

            curr_filter_id = str(num_filter.id)
            range_filter_data[curr_filter_id] = {}
            range_filter_data[curr_filter_id][
                "available_min_value"
            ] = available_min_value
            range_filter_data[curr_filter_id][
                "available_max_value"
            ] = available_max_value
            range_filter_data[curr_filter_id]["min_value"] = available_min_value
            range_filter_data[curr_filter_id]["max_value"] = available_max_value
            if cust_filter_min_max_vals and cust_filter_min_max_vals.get(
                curr_filter_id
            ):
                if cust_filter_min_max_vals[curr_filter_id].get("min"):
                    range_filter_data[curr_filter_id][
                        "min_value"
                    ] = cust_filter_min_max_vals[curr_filter_id]["min"]
                if cust_filter_min_max_vals[curr_filter_id].get("max"):
                    range_filter_data[curr_filter_id][
                        "max_value"
                    ] = cust_filter_min_max_vals[curr_filter_id]["max"]
        return range_filter_data

    def _get_additional_shop_values(self, values):
        custom_product_filters_enabled = request.website.is_view_active(
            "website_sale_custom_filter.products_filters"
        )
        if custom_product_filters_enabled:
            # get values from custom range filters
            values["filter_vals"] = self.get_custom_range_filter_values()
            # get values for custom checkbox filters
            values["custom_checkbox_filters"] = self.get_custom_checkbox_filter_values()
            # check if any custom filter changed so we use
            # it as condition to show "clean filter" btn
            values["custom_val_filter_changed"] = any(
                [
                    i in request.httprequest.args
                    for i in ["cust_filter", "min_cust_filter", "max_cust_filter"]
                ]
            )
        return super()._get_additional_shop_values(values)

    # override _get_search_options to include chosen filters values
    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        pricelist=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        res = super()._get_search_options(
            category,
            attrib_values,
            pricelist,
            min_price,
            max_price,
            conversion_rate,
            **post,
        )
        res["custom_checkbox_filters"] = self.get_custom_checkbox_filter_values()
        res["custom_value_filters"] = self.get_custom_range_filter_values()
        return res
