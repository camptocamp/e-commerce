# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = "product.brand"
    _inherit = [
        "product.brand",
        "image.mixin",
        "website.published.mixin",
    ]

    cover_image = fields.Image(max_width=2560, max_height=2560)
    website_description = fields.Html(translate=True)
    website_footer = fields.Html(translate=True)
    show_brand_name = fields.Boolean(default=True)
    show_brand_description = fields.Boolean(default=True)
    align_brand_content = fields.Selection(
        selection=[
            ("left", "Left"),
            ("center", "Center"),
        ],
        default="left",
        required=True,
    )
    published_products_count = fields.Integer(
        compute="_compute_published_products_count",
    )

    @api.depends("name")
    def _compute_website_url(self):
        res = super()._compute_website_url()
        for brand in self:
            brand.website_url = f"/shop/brand/{self.env['ir.http']._slug(brand)}"
        return res

    def _compute_published_products_count(self):
        for brand in self:
            brand.published_products_count = self.env["product.template"].search_count(
                [
                    ("product_brand_id", "=", brand.id),
                    ("website_published", "=", True),
                ]
            )
