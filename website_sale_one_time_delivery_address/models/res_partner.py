import logging

from odoo import api, fields, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        selection_add=[("one_time_delivery", "One-Time Delivery Address")],
        ondelete={"one_time_delivery": "set default"},
    )

    def _get_delivery_address_domain(self):
        """Extend the delivery address domain to also list one_time_delivery
        contacts alongside the standard 'delivery'/'other' addresses."""
        return super()._get_delivery_address_domain() | Domain(
            [
                ("id", "child_of", self.ids),
                ("type", "=", "one_time_delivery"),
            ]
        )

    @api.autovacuum
    def _gc_archive_one_time_delivery_partners(self, limit=100):
        """Archive one-time delivery contacts whose deliveries are complete.

        A one_time_delivery partner is a temporary recipient created on the
        reseller during checkout and referenced as the shipping partner of one
        or more sale orders. Once every related delivery is finished it is safe
        to archive the contact so it stops cluttering the address book while
        preserving the order history (archive, not delete).

        A partner is archived when it has at least one related picking and every
        related picking has reached a terminal state ('done' or 'cancel'). This
        covers delivered orders as well as fully cancelled ones, since a contact
        whose deliveries were all cancelled is equally dead weight. Partners with
        no related order, no picking, or any still-pending picking are kept.
        """
        candidates = self.search([("type", "=", "one_time_delivery")], limit=limit)
        if not candidates:
            return

        orders = self.env["sale.order"].search(
            [("partner_shipping_id", "in", candidates.ids)]
        )
        orders_by_partner = orders.grouped("partner_shipping_id")

        empty_orders = self.env["sale.order"]
        terminal_states = {"done", "cancel"}
        to_archive_ids = []
        for partner in candidates:
            pickings = orders_by_partner.get(partner, empty_orders).picking_ids
            if not pickings:
                continue
            states = set(pickings.mapped("state"))
            # Archive once every delivery is finished: nothing is left in a
            # draft/waiting/confirmed/assigned state.
            if states <= terminal_states:
                to_archive_ids.append(partner.id)

        if to_archive_ids:
            to_archive = self.browse(to_archive_ids)
            to_archive.action_archive()
            _logger.info(
                "Archived %d completed one-time delivery contact(s): %s",
                len(to_archive),
                to_archive.ids,
            )
