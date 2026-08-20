# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PromotionCodeUsageRecognitionLine(models.Model):
    """
    Represents the debit/credit pair posted for one side (customer or
    referrer) of a usage's discount by a single Recognition document.

    One record is generated per **deferred** side of the usage's
    discount: two Recognition Lines when both sides are deferred, a
    single one when only the customer or only the referrer is (see
    ``promotion_code_usage_recognition._get_deferred_line_types``).
    Each line debits its own side's Final Account and credits its own
    side's Deferred Account, so it always releases exactly what that
    side booked. Debit and credit creation is delegated to the
    inherited ``mixin.account_move_double_line``.
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
        compute="_compute_credit_account_id",
        compute_sudo=True,
        help="Deferred Account this line's own side of the usage was "
        "booked to, credited by this Recognition Line: the usage's "
        "own 'Deferred Account' for the customer side, its 'Referrer "
        "Deferred Account' for a referrer side deferred on its own. "
        "Resolved from the usage's own ``_get_deferred_account`` -- "
        "the same resolver that picked the account when the usage was "
        "approved, so a line always credits back exactly what it "
        "debited.",
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

    @api.depends(
        "line_type",
        "recognition_id.usage_id.deferred_account_id",
        "recognition_id.usage_id.referrer_deferred_account_id",
        "recognition_id.usage_id.referrer_recognition_method",
    )
    def _compute_credit_account_id(self):
        """Resolve the Deferred Account this line credits, per side.

        Reading the usage's own 'Deferred Account' for *every* line
        was wrong the moment each side got a recognition method of its
        own: on a usage deferred for the referrer alone, the voucher
        user's own 'Deferred Account' is empty, so the referrer line
        credited nothing at all and the journal entry was refused by
        the database (``account_move_line_check_accountable_required_
        fields``).

        :return: nothing; assigns ``credit_account_id``
        """
        for record in self:
            result = self.env["account.account"]
            usage = record.recognition_id.usage_id
            if usage:
                result = usage._get_deferred_account(
                    referrer=record.line_type == "referrer"
                )
            record.credit_account_id = result

    def _get_standard_label(self, direction):
        """Return the move line label.

        Combines the parent Recognition document's own number with
        the usage's own promotion code.

        :param direction: ``'debit'`` or ``'credit'`` (unused, both
            sides share the same label)
        :return: the composed label string
        """
        self.ensure_one()
        return "%s - %s" % (
            self.recognition_id.name,
            self.recognition_id.usage_id.promotion_code_id.name,
        )
