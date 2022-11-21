# Copyright 2022 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "eCommerce Product Filters",
    "category": "Website/Website",
    "sequence": 50,
    "summary": "Advanced website product filters",
    "website": "https://github.com/OCA/e-commerce",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "version": "15.0.0.1.0",
    "development_status": "Alpha",
    "depends": ["website", "sale", "mail", "website_sale", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/website_configuration.xml",
        "views/templates.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_frontend": [
            "website_sale_custom_filter/static/src/scss/website_sale.scss",
            "website_sale_custom_filter/static/src/js/website_sale_filters.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
