# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    # OVERRIDE: make the tax display dynamic so the current website partner can
    # specify a value that takes precedence over the standard website behavior.
    show_line_subtotals_tax_selection = fields.Selection(
        store=False,
    )

    @api.depends("company_id.account_fiscal_country_id")
    @api.depends_context("uid")
    def _compute_show_line_subtotals_tax_selection(self):
        # OVERRIDE: apply the current website partner tax display preference,
        # when set, on top of the standard website behavior.
        if partner_tax_selection := self._get_current_partner_tax_selection():
            for website in self:
                website.show_line_subtotals_tax_selection = partner_tax_selection
        else:
            return super()._compute_show_line_subtotals_tax_selection()

    def _get_current_website_tax_selection_partner(self):
        """Return the partner used to resolve website tax display preference.

        :return: Current HTTP request user partner, or environment user partner
            when running outside an HTTP request.
        :rtype: res.partner
        """
        try:
            return request.env.user.partner_id
        except RuntimeError:
            return self.env.user.partner_id

    def _get_current_partner_tax_selection(self) -> str | bool:
        """Return the current partner explicit website tax display preference.

        The contact value takes precedence over the commercial entity value.

        :return: Preferred tax display value, or False when none is set.
        """
        partner = self._get_current_website_tax_selection_partner()
        if not partner:
            return False
        if partner.website_show_line_subtotals_tax_selection:
            return partner.website_show_line_subtotals_tax_selection
        commercial_partner = partner.commercial_partner_id
        if commercial_partner != partner:
            return commercial_partner.website_show_line_subtotals_tax_selection
        return False
