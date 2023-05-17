# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import SavepointCase


class TestProductTemplate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                # compatibility flag when you run tests on a db
                # where `product_variant_multi_link` is installed.
                _product_variant_link_bypass_check=True,
            )
        )
        cls.product_template = cls.env["product.template"].create(
            {"name": "PTL_name", "default_code": "PTL_default_code"}
        )

    def test_product_template_name_search_with_name(self):
        # As soon as the value is matching the name of the template, it's working,
        # with or without the domain on 'id'
        product = self.env["product.template"].name_search("PTL_name")
        self.assertTrue(product)
        product = self.env["product.template"].name_search(
            "PTL_name", args=[("id", "!=", 0)]
        )
        self.assertTrue(product)
        product = (
            self.env["product.template"]
            .with_context(name_search_default_code=True)
            .name_search("PTL_name", args=[("id", "!=", 0)])
        )
        self.assertTrue(product)

    def test_product_template_name_search_with_default_code(self):
        product = self.env["product.template"].name_search("PTL_default_code")
        self.assertTrue(product)
        # Searching with the default_code => the template is not found
        product = self.env["product.template"].name_search(
            "PTL_default_code", args=[("id", "!=", 0)]
        )
        self.assertFalse(product)
        # Same but enable the search on default_code => the template is now found
        product = (
            self.env["product.template"]
            .with_context(name_search_default_code=True)
            .name_search("PTL_default_code", args=[("id", "!=", 0)])
        )
        self.assertTrue(product)
