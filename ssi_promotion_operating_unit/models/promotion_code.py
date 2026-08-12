# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PromotionCode(models.Model):  # pylint: disable=too-few-public-methods
    """
    Ties each promotion code to a single operating unit.

    Adds ``mixin.single_operating_unit`` so every ``promotion_code``
    record carries an ``operating_unit_id``. As a result, the list of
    promotion codes a user sees is filtered by operating unit through
    this module's record rule.
    """

    _name = "promotion_code"
    _inherit = [
        "promotion_code",
        "mixin.single_operating_unit",
    ]
