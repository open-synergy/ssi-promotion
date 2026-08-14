# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    """Let a journal entry be tracked and self-serve its promotions.

    Inherits ``mixin.promotion_object`` with
    ``_promotion_move_line_field_name`` set to ``"line_ids"``: the
    mixin's own default filter (reconcilable account, posted move,
    positive residual) already narrows that down to this move's own
    outstanding receivable line(s), so no override is needed here.
    No view is changed -- the form view is shared by every journal
    type.
    """

    _name = "account.move"
    _inherit = [
        "account.move",
        "mixin.promotion_object",
    ]

    _promotion_move_line_field_name = "line_ids"
