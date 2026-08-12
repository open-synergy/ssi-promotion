# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PromotionCodeUsageRecognitionLine(models.Model):
    """
    Represents the debit/credit pair posted for one side (customer or
    referrer) of a usage's discount by a single Recognition document.

    One record is generated per side of the usage's discount being
    released: a usage whose promotion code has a referrer produces
    two Recognition Lines (customer and referrer); one without a
    referrer produces a single customer Line. Debit and credit
    creation is delegated to the inherited
    ``mixin.account_move_double_line``.
    """

    _name = "promotion_code_usage_recognition_line"
    _description = "Promotion Code Usage Recognition - Line"
    _inherit = [
        "mixin.account_move_double_line",
    ]
    _order = "recognition_id, id"

    # Accounting Move Double Line Mixin (``mixin.account_move_double_line``)
    _move_id_field_name = "move_id"
    _currency_id_field_name = "currency_id"
    _debit_account_id_field_name = "debit_account_id"
    _credit_account_id_field_name = "credit_account_id"
    _debit_amount_currency_field_name = "amount"
    _credit_amount_currency_field_name = "amount"
    _debit_currency_id_field_name = "currency_id"
    _credit_currency_id_field_name = "currency_id"
    _debit_company_currency_id_field_name = "company_currency_id"
    _credit_company_currency_id_field_name = "company_currency_id"
    _debit_date_field_name = "date"
    _credit_date_field_name = "date"
    _debit_company_id_field_name = "company_id"
    _credit_company_id_field_name = "company_id"

    recognition_id = fields.Many2one(
        string="# Recognition",
        comodel_name="promotion_code_usage_recognition",
        required=True,
        ondelete="cascade",
        help="Recognition document this line belongs to.",
    )
    line_type = fields.Selection(
        string="Line Type",
        selection=[
            ("customer", "Customer"),
            ("referrer", "Referrer"),
        ],
        required=True,
        help="Side of the usage's discount released by this line: "
        "the voucher user's own share, or the promotion code's "
        "referrer own share.",
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="company_currency_id",
        help="Portion of the Recognition document's own Amount "
        "released for this side of the discount, already rounded to "
        "the currency's own precision.",
    )
    debit_account_id = fields.Many2one(
        string="Debit Account",
        comodel_name="account.account",
        required=True,
        help="Final Account of this line's own side of the "
        "discount, debited by this Recognition Line. Resolved from "
        "the usage's own ``_get_final_account`` when this line is "
        "generated.",
    )
    credit_account_id = fields.Many2one(
        string="Credit Account",
        comodel_name="account.account",
        related="recognition_id.usage_id.deferred_account_id",
        help="Deferred Account of the parent Recognition's own "
        "usage, credited by this Recognition Line.",
    )
    move_id = fields.Many2one(
        string="Move",
        comodel_name="account.move",
        related="recognition_id.move_id",
        help="Journal entry of the parent Recognition document.",
    )
    date = fields.Date(
        string="Date",
        related="recognition_id.date",
        help="Accounting date inherited from the parent Recognition " "document.",
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        related="recognition_id.company_id",
        help="Company inherited from the parent Recognition document.",
    )
    company_currency_id = fields.Many2one(
        string="Company Currency",
        comodel_name="res.currency",
        related="recognition_id.company_currency_id",
        help="Company currency inherited from the parent Recognition " "document.",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="recognition_id.currency_id",
        help="Currency inherited from the parent Recognition " "document.",
    )

    def _get_standard_label(self, direction):
        """Return the move line label.

        Combines the parent Recognition document's own number with
        the usage's own promotion code voucher code.

        :param direction: ``'debit'`` or ``'credit'`` (unused, both
            sides share the same label)
        :return: the composed label string
        """
        self.ensure_one()
        return "%s - %s" % (
            self.recognition_id.name,
            self.recognition_id.usage_id.promotion_code_id.voucher_code,
        )
