# -*- coding: utf-8 -*-
# © 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import api, fields, models
from openerp.http import request


class ResPartner(models.Model):
    _inherit = "res.partner"

    skip_website_checkout_payment = fields.Boolean(default=True)
