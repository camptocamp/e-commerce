# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_sale_multiple_vals(self, product_or_template):
        # Get product variant if we got a single variant template
        product = product_or_template
        if product._name == "product.template":
            product = product.product_variant_id

        if multiple_uom := product.sale_multiple_uom_id:
            return {
                "is_multiple": 1,
                # We want to return an integer to the quantity
                # frontend input when page loads
                "sale_multiple_qty": int(multiple_uom.factor),
            }
        return {
            "is_multiple": 0,
            "sale_multiple_qty": 1,
        }

    @api.model
    def _get_additionnal_combination_info(
        self, product_or_template, quantity, uom, date, website
    ):
        # OVERRIDE: to update the combination info with the multiple related info.
        # If product has a sale multiple UoM, we return the "step" of the quantity
        # in the frontend and mark the product as being a multiple product.
        # We compute ``base_unit_price`` from the unrounded tax result
        # (round_base=False) to avoid currency rounding issues:
        #   incorrect: 0.712999 -> 0.71 would become 71.0 €/100
        #   correct: 0.712999 -> 0.713 would become 71.3 €/100
        # Most of the code here is copy-pasted from the ``website_sale`` module.
        combination_info = super()._get_additionnal_combination_info(
            product_or_template, quantity, uom, date, website
        )

        # START OVERRIDE: add sale multiple info in the combination info
        combination_info.update(self._get_sale_multiple_vals(product_or_template))
        # END OVERRIDE

        # START STANDARD
        if self.env["res.groups"]._is_feature_enabled(
            "website_sale.group_show_uom_price"
        ):
            pricelist = request.pricelist.with_context(**self.env.context)
            currency = website.currency_id.with_context(**self.env.context)
            pricelist_price, _pricelist_rule_id = pricelist._get_product_price_rule(
                product=product_or_template,
                quantity=quantity,
                uom=uom,
                currency=currency,
            )
            product_taxes = (
                product_or_template.sudo().taxes_id._filter_taxes_by_company(
                    self.env.company
                )
            )
            taxes = self.env["account.tax"]
            if product_taxes:
                taxes = request.fiscal_position.map_tax(product_taxes)
                show_tax = website.show_line_subtotals_tax_selection
                tax_display = (
                    "total_excluded" if show_tax == "tax_excluded" else "total_included"
                )
                price_tax_included = self.env[
                    "product.product"
                ]._get_tax_included_unit_price_from_price(
                    pricelist_price,
                    product_taxes,
                    product_taxes_after_fp=taxes,
                )

                # START OVERRIDE: disable rounding by ``round_base=False`` context key
                # inside ``compute_all`` only for ``base_unit_price`` computation
                res = taxes.with_context(round_base=False).compute_all(
                    price_tax_included,
                    currency,
                    1,
                    product_or_template,
                    self.env.user.partner_id,
                )
                tax_base_unit_price = res[tax_display]
            else:
                tax_base_unit_price = pricelist_price
                # END OVERRIDE

            # START STANDARD
            price_per_product_uom = uom._compute_price(
                price=tax_base_unit_price, to_unit=self.uom_id
            )
            combination_info.update(
                {
                    "base_unit_name": product_or_template.base_unit_name,
                    "base_unit_price": product_or_template._get_base_unit_price(
                        price_per_product_uom
                    ),
                }
            )
            # END STANDARD
        return combination_info
