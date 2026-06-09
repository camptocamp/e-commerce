from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon
from odoo.addons.website_sale_one_time_delivery_address.controllers.main import (
    WebsiteSaleOneTimeDeliveryAddress,
)


@tagged("post_install", "-at_install")
class TestWebsiteSaleOneTimeDeliveryAddress(WebsiteSaleCommon):
    """Business-flow tests for website_sale_one_time_delivery_address.

    All tests simulate the real checkout path:
      1. Create a sale order for a reseller.
      2. Optionally enable one-time delivery mode via the RPC endpoint.
      3. Submit a delivery address through shop_address_submit.
      4. Assert partner type, sale order shipping/invoice mapping, and parent link.

    Checkout requests are issued as a logged-in reseller portal user. This
    mirrors real usage and, crucially, keeps the cart bound to the reseller:
    ``website._get_and_cache_current_cart`` rebinds the cart to the request
    user's partner, so anonymous/superuser requests would otherwise move the
    cart onto an unrelated partner.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSaleOneTimeDeliveryAddress()
        cls.reseller_user = cls.env["res.users"].create(
            {
                "name": "Reseller",
                "login": "otd_reseller",
                "email": "reseller@example.com",
                "group_ids": [Command.link(cls.env.ref("base.group_portal").id)],
            }
        )
        cls.reseller = cls.reseller_user.partner_id
        cls.reseller_env = cls.env(user=cls.reseller_user)
        # The cart is rebound to ``request.website.env.user`` by
        # ``_get_and_cache_current_cart``; the website record must therefore run
        # in the reseller env, not the superuser one, for the cart to stay on
        # the reseller.
        cls.reseller_website = cls.website.with_env(cls.reseller_env)
        cls.address_form = {
            "name": "End Customer",
            "email": "end-customer@example.com",
            "street": "42 Nowhere Lane",
            "city": "Springfield",
            "zip": "12345",
            "country_id": cls.country_us.id,
            "state_id": cls.country_us_state_id,
            "phone": "+1 555-000-0000",
            "address_type": "delivery",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_reseller_so(self, **values):
        """Create a checkout cart owned by the reseller portal user."""
        return self._create_so(partner_id=self.reseller.id, **values)

    def _submit_delivery_address(self, sale_order, extra=None):
        """Call shop_address_submit inside a MockRequest and return the order."""
        form = dict(self.address_form, **(extra or {}))
        with MockRequest(
            self.reseller_env,
            website=self.reseller_website,
            sale_order_id=sale_order.id,
        ) as req:
            req.httprequest.method = "POST"
            self.controller.shop_address_submit(**form)
        return sale_order

    def _enable_one_time_delivery(self, sale_order):
        with MockRequest(
            self.reseller_env,
            website=self.reseller_website,
            sale_order_id=sale_order.id,
        ):
            self.controller.shop_update_one_time_delivery(one_time_delivery=True)

    # ------------------------------------------------------------------
    # Model sanity
    # ------------------------------------------------------------------

    def test_partner_type_selection_registered(self):
        """The one_time_delivery value is available on res.partner.type."""
        selection = dict(self.env["res.partner"]._fields["type"].selection)
        self.assertIn("one_time_delivery", selection)
        self.assertEqual(selection["one_time_delivery"], "One-Time Delivery Address")

    def test_sale_order_flag_field_exists(self):
        """sale.order has a one_time_delivery boolean field, defaulting to False."""
        so = self._create_so(partner_id=self.partner.id)
        self.assertFalse(so.one_time_delivery)
        so.one_time_delivery = True
        self.assertTrue(so.one_time_delivery)

    # ------------------------------------------------------------------
    # Mode OFF (default) – checkout creates a regular delivery address
    # ------------------------------------------------------------------

    def test_mode_off_creates_standard_delivery_type(self):
        """Default checkout delivery address has type='delivery' (mode is off)."""
        reseller = self.reseller
        so = self._create_reseller_so()

        self._submit_delivery_address(so)

        shipping = so.partner_shipping_id
        self.assertNotEqual(
            shipping, reseller, "A new shipping address should have been created"
        )
        self.assertEqual(shipping.type, "delivery")
        # Billing must remain unchanged
        self.assertEqual(so.partner_invoice_id, reseller)
        # New address is a child of the reseller's commercial partner
        self.assertEqual(shipping.parent_id, reseller.commercial_partner_id)

    # ------------------------------------------------------------------
    # Mode ON – checkout creates a one_time_delivery contact
    # ------------------------------------------------------------------

    def test_mode_on_creates_one_time_delivery_type(self):
        """When enabled, checkout creates a one_time_delivery shipping address."""
        reseller = self.reseller
        so = self._create_reseller_so()
        self._enable_one_time_delivery(so)

        self._submit_delivery_address(so)

        shipping = so.partner_shipping_id
        self.assertNotEqual(shipping, reseller)
        self.assertEqual(
            shipping.type,
            "one_time_delivery",
            f"Expected type='one_time_delivery', got type='{shipping.type}'",
        )
        # Billing MUST remain the reseller
        self.assertEqual(
            so.partner_invoice_id,
            reseller,
            "Invoice partner must remain the reseller when one_time_delivery is active",
        )
        # New address is a child of the reseller's commercial partner
        self.assertEqual(shipping.parent_id, reseller.commercial_partner_id)

    def test_mode_on_protects_billing_when_use_delivery_as_billing_submitted(self):
        """Billing stays on the reseller even if the browser submits it.

        This is the key protection: in a one-time delivery checkout, the end-customer
        address must NEVER become the billing address.
        """
        reseller = self.reseller
        so = self._create_reseller_so()
        self._enable_one_time_delivery(so)

        # Simulate the browser submitting use_delivery_as_billing,
        # for example from a checked checkbox.
        self._submit_delivery_address(so, extra={"use_delivery_as_billing": "true"})

        shipping = so.partner_shipping_id
        self.assertNotEqual(shipping, reseller)
        # Type must still be one_time_delivery, not 'other'
        self.assertEqual(
            shipping.type,
            "one_time_delivery",
            f"Expected type='one_time_delivery', got type='{shipping.type}' – "
            "use_delivery_as_billing should be ignored in one_time_delivery mode",
        )
        # Invoice MUST remain the reseller despite use_delivery_as_billing=True
        self.assertEqual(
            so.partner_invoice_id,
            reseller,
            (
                "Invoice partner changed to the one-time address "
                "and billing protection failed"
            ),
        )
        # Shipping and billing are DIFFERENT partners
        self.assertNotEqual(so.partner_shipping_id, so.partner_invoice_id)

    # ------------------------------------------------------------------
    # RPC endpoint
    # ------------------------------------------------------------------

    def test_rpc_endpoint_toggles_flag(self):
        """The /shop/update_one_time_delivery RPC correctly flips the cart flag."""
        so = self._create_reseller_so()
        self.assertFalse(so.one_time_delivery)

        with MockRequest(
            self.reseller_env, website=self.reseller_website, sale_order_id=so.id
        ):
            self.controller.shop_update_one_time_delivery(one_time_delivery=True)
        self.assertTrue(so.one_time_delivery)

        with MockRequest(
            self.reseller_env, website=self.reseller_website, sale_order_id=so.id
        ):
            self.controller.shop_update_one_time_delivery(one_time_delivery=False)
        self.assertFalse(so.one_time_delivery)

    # ------------------------------------------------------------------
    # Template context
    # ------------------------------------------------------------------

    def test_checkout_page_values_expose_flag(self):
        """Checkout values expose one_time_delivery to the template."""
        so = self._create_reseller_so()
        so.one_time_delivery = True

        with MockRequest(
            self.reseller_env, website=self.reseller_website, sale_order_id=so.id
        ):
            values = self.controller._prepare_checkout_page_values(so)

        self.assertTrue(
            values.get("one_time_delivery"),
            (
                "The one_time_delivery flag must be passed "
                "to the checkout template context"
            ),
        )

    def test_one_time_delivery_addresses_visible_in_checkout(self):
        """Created one_time_delivery addresses appear in the delivery_addresses list."""
        reseller = self.env.user.partner_id
        so = self._create_so(partner_id=reseller.id)
        self._enable_one_time_delivery(so)

        # Create a one_time_delivery address
        self._submit_delivery_address(so)
        one_time_addr = so.partner_shipping_id
        self.assertEqual(one_time_addr.type, "one_time_delivery")

        # Get the checkout page values to check what addresses are visible
        with MockRequest(self.env, website=self.website, sale_order_id=so.id):
            values = self.controller._prepare_checkout_page_values(so)

        delivery_addresses = values.get("delivery_addresses", [])
        self.assertIn(
            one_time_addr,
            delivery_addresses,
            (
                "one_time_delivery type addresses should be visible "
                "in delivery_addresses list"
            ),
        )

    # ------------------------------------------------------------------
    # Autovacuum – archive completed one-time delivery contacts
    # ------------------------------------------------------------------

    def _make_one_time_partner(self):
        return self.env["res.partner"].create(
            {
                "name": "One-Time Recipient",
                "parent_id": self.partner.commercial_partner_id.id,
                "type": "one_time_delivery",
            }
        )

    def _deliver(self, order):
        """Confirm the order and validate every generated picking as done."""
        order.action_confirm()
        for picking in order.picking_ids:
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True
            picking.button_validate()

    def test_gc_archives_partner_when_delivery_done(self):
        """A one_time_delivery partner is archived once its picking is done."""
        partner = self._make_one_time_partner()
        order = self._create_so(partner_shipping_id=partner.id)
        self._deliver(order)
        self.assertEqual(set(order.picking_ids.mapped("state")), {"done"})

        self.env["res.partner"]._gc_archive_one_time_delivery_partners()

        self.assertFalse(
            partner.active,
            "Partner should be archived when all related pickings are done",
        )

    def test_gc_archives_partner_when_delivery_cancelled(self):
        """A one_time_delivery partner is archived when all pickings are cancelled.

        A contact whose every delivery was cancelled will never receive anything,
        so it is dead weight and must be cleaned up just like a delivered one.
        """
        partner = self._make_one_time_partner()
        order = self._create_so(partner_shipping_id=partner.id)
        order.action_confirm()
        order.picking_ids.action_cancel()
        self.assertEqual(set(order.picking_ids.mapped("state")), {"cancel"})

        self.env["res.partner"]._gc_archive_one_time_delivery_partners()

        self.assertFalse(
            partner.active,
            "Partner should be archived when all related pickings are terminal",
        )

    def test_gc_keeps_partner_when_delivery_pending(self):
        """A one_time_delivery partner with a pending picking is not archived."""
        partner = self._make_one_time_partner()
        order = self._create_so(partner_shipping_id=partner.id)
        order.action_confirm()
        self.assertTrue(order.picking_ids)
        self.assertNotIn("done", order.picking_ids.mapped("state"))

        self.env["res.partner"]._gc_archive_one_time_delivery_partners()

        self.assertTrue(
            partner.active,
            "Partner must stay active while a related picking is not done",
        )

    def test_gc_keeps_partner_without_order(self):
        """A one_time_delivery partner not linked to any order is not archived."""
        partner = self._make_one_time_partner()

        self.env["res.partner"]._gc_archive_one_time_delivery_partners()

        self.assertTrue(
            partner.active,
            "Partner without any related order must not be archived",
        )

    def test_gc_ignores_regular_partners(self):
        """Standard delivery partners are never archived by this routine."""
        partner = self.env["res.partner"].create(
            {
                "name": "Regular Delivery",
                "parent_id": self.partner.commercial_partner_id.id,
                "type": "delivery",
            }
        )
        order = self._create_so(partner_shipping_id=partner.id)
        self._deliver(order)
        self.assertEqual(set(order.picking_ids.mapped("state")), {"done"})

        self.env["res.partner"]._gc_archive_one_time_delivery_partners()

        self.assertTrue(
            partner.active,
            "Only one_time_delivery partners may be archived by the routine",
        )

    # ------------------------------------------------------------------
    # Delivery address selection drives one-time mode
    # ------------------------------------------------------------------

    def test_update_address_to_one_time_enables_mode(self):
        """Selecting a one_time_delivery address enables one-time mode."""
        reseller = self.reseller
        so = self._create_reseller_so()
        one_time = self.env["res.partner"].create(
            {
                "name": "Saved One-Time",
                "parent_id": reseller.commercial_partner_id.id,
                "type": "one_time_delivery",
            }
        )

        with MockRequest(
            self.reseller_env, website=self.reseller_website, sale_order_id=so.id
        ):
            self.controller.shop_update_address(
                partner_id=one_time.id, address_type="delivery"
            )

        self.assertTrue(so.one_time_delivery)
        self.assertEqual(so.partner_shipping_id, one_time)

    def test_update_address_to_regular_disables_mode(self):
        """Selecting a regular delivery address leaves one-time mode."""
        reseller = self.reseller
        so = self._create_reseller_so()
        so.one_time_delivery = True
        regular = self.env["res.partner"].create(
            {
                "name": "Saved Delivery",
                "parent_id": reseller.commercial_partner_id.id,
                "type": "delivery",
            }
        )

        with MockRequest(
            self.reseller_env, website=self.reseller_website, sale_order_id=so.id
        ):
            self.controller.shop_update_address(
                partner_id=regular.id, address_type="delivery"
            )

        self.assertFalse(so.one_time_delivery)
        self.assertEqual(so.partner_shipping_id, regular)
