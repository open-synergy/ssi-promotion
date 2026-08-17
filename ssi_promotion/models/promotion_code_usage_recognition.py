# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date as datetime_date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round

from odoo.addons.ssi_decorator import ssi_decorator


class PromotionCodeUsageRecognition(models.Model):
    """
    Represents one release of a promotion_code_usage's deferred
    discount into its own Final Account(s).

    A usage side whose own recognition method is 'Deferred' books its
    journal entry line to a Deferred Account instead of its own Final
    Account. This document later moves 'Amount' -- once for the full
    'Amount Deferred', or several times -- from Deferred Account to
    each journal entry's own Final Account, with one Line **per
    deferred side only**: a usage recognized on the spot for the
    voucher user but deferred for the referrer issues a single
    'referrer' Line, and no 'customer' Line at all.
    """

    _name = "promotion_code_usage_recognition"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_confirm",
        "mixin.company_currency",
        "mixin.account_move",
    ]
    _description = "Promotion Code Usage Recognition"
    _order = "date, id"

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "done"
    _approval_state = "confirm"
    _after_approved_method = "action_done"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False

    _statusbar_visible_label = "draft,confirm,done"
    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "done_ok",
        "cancel_ok",
        "restart_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "done"

    # Accounting Entry Header Mixin (``mixin.account_move``)
    _journal_id_field_name = "journal_id"
    _move_id_field_name = "move_id"
    _accounting_date_field_name = "date"
    _currency_id_field_name = "currency_id"
    _company_currency_id_field_name = "company_currency_id"

    usage_id = fields.Many2one(
        string="# Usage",
        comodel_name="promotion_code_usage",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        help="Deferred promotion_code_usage this document releases.",
    )
    date = fields.Date(
        string="Date",
        default=lambda r: datetime_date.today(),
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        help="Accounting date of this recognition document. May not "
        "be earlier than the usage's own Usage Date.",
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        help="Portion of the usage's own Amount Deferred released by "
        "this document. The sum of every Done Recognition's Amount "
        "may not exceed the usage's own Amount To Recognize.",
    )
    ratio = fields.Float(
        string="Ratio",
        compute="_compute_ratio",
        help="This document's own Amount divided by the usage's own "
        "Amount To Recognize -- the proportion of each Line released "
        "by this document.",
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        help="Accounting journal this document's own entry posts to.",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="company_currency_id",
        store=True,
        help="Currency this document is expressed in. This document "
        "does not support a currency other than the Company "
        "Currency.",
    )
    move_id = fields.Many2one(
        string="Move",
        comodel_name="account.move",
        readonly=True,
        copy=False,
        help="Journal entry generated when this document is Done.",
    )
    recognition_line_ids = fields.One2many(
        string="Recognition Lines",
        comodel_name="promotion_code_usage_recognition_line",
        inverse_name="recognition_id",
        readonly=True,
        copy=False,
        help="One technical line per deferred side of the usage's "
        "discount (customer, referrer, or both -- a side recognized "
        "on the spot gets no line at all), each carrying the "
        "debit/credit pair posted for it. Generated when this "
        "document is Done; cleared again if it is cancelled.",
    )
    note = fields.Text(
        string="Note",
        help="Free-form note about this recognition document.",
    )

    @api.depends("amount", "usage_id.amount_to_recognize")
    def _compute_ratio(self):
        """Compute the proportion of the usage released by this document.

        :return: nothing; assigns ``ratio``
        """
        for record in self:
            ratio = 0.0
            if record.usage_id.amount_to_recognize:
                ratio = record.amount / record.usage_id.amount_to_recognize
            record.ratio = ratio

    @api.onchange("usage_id")
    def onchange_amount(self):
        """Default Amount from the usage's own Amount Deferred.

        :return: nothing
        """
        self.amount = 0.0
        if self.usage_id:
            self.amount = self.usage_id.amount_deferred

    @api.onchange("usage_id")
    def onchange_journal_id(self):
        """Default Journal from the usage's own Recognition Journal.

        :return: nothing
        """
        self.journal_id = False
        if self.usage_id:
            self.journal_id = self.usage_id.recognition_journal_id

    @api.constrains("amount", "date", "state")
    def _check_amount_not_exceed_to_recognize(self):
        """Forbid Done Recognitions of a usage exceeding its total.

        :raises ValidationError: when the sum of every Done
            Recognition's Amount on the same usage exceeds that
            usage's own Amount To Recognize.
        """
        for record in self:
            if record.state != "done":
                continue
            usage = record.usage_id
            done_recognitions = usage.recognition_ids.filtered(
                lambda recognition: recognition.state == "done"
            )
            total_recognized = sum(done_recognitions.mapped("amount"))
            precision = record.company_currency_id.decimal_places
            if (
                float_compare(
                    total_recognized,
                    usage.amount_to_recognize,
                    precision_digits=precision,
                )
                > 0
            ):
                error_message = """
Document Type: %s
Context: Configure recognition amount
Database ID: %s
Problem: Total Done Recognition amount %s exceeds the usage's own Amount To Recognize %s
Solution: Lower this document's own Amount so the total stays within Amount To Recognize
""" % (
                    record._description,
                    record.id,
                    total_recognized,
                    usage.amount_to_recognize,
                )
                raise ValidationError(_(error_message))

    @api.constrains("date")
    def _check_date_not_before_usage(self):
        """Forbid a Date earlier than the usage's own Usage Date.

        :raises ValidationError: when ``date`` is earlier than
            ``usage_id.date``.
        """
        for record in self:
            if (
                record.date
                and record.usage_id.date
                and (record.date < record.usage_id.date)
            ):
                error_message = """
Document Type: %s
Context: Configure recognition date
Database ID: %s
Problem: Date %s is earlier than the usage's own Usage Date %s
Solution: Select a Date on or after the usage's own Usage Date
""" % (
                    record._description,
                    record.id,
                    record.date,
                    record.usage_id.date,
                )
                raise ValidationError(_(error_message))

    @api.constrains("usage_id")
    def _check_usage_recognition_method_deferred(self):
        """Forbid recognizing a usage with no deferred side at all.

        Read per side (``promotion_code_usage._get_recognition_method``)
        rather than off the voucher user's own 'Recognition Method'
        alone: a usage recognized on the spot for the voucher user but
        deferred for the referrer does carry a deferred amount, and
        must be recognizable. Only a usage where *neither* side is
        deferred has nothing to release.

        :raises ValidationError: when neither the voucher user's nor
            the referrer's own recognition method is ``deferred``.
        """
        for record in self:
            if record.usage_id and not record._get_deferred_line_types():
                error_message = """
Document Type: %s
Context: Select usage to recognize
Database ID: %s
Problem: Usage '%s' has no deferred side: neither its own Recognition \
Method nor its Referrer Recognition Method is 'Deferred'
Solution: Select a usage whose own Recognition Method, or whose Referrer \
Recognition Method, is 'Deferred'
""" % (
                    record._description,
                    record.id,
                    record.usage_id.display_name,
                )
                raise ValidationError(_(error_message))

    @ssi_decorator.post_done_action()
    def _10_create_accounting_entry(self):
        """Create and post this document's ``account.move``.

        Creates the header move, then one
        ``promotion_code_usage_recognition_line`` per **deferred**
        side of the usage (see ``_get_deferred_line_types``) -- which
        may be the customer alone, the referrer alone, or both --
        rounded to the currency's own precision with the rounding
        remainder charged to the last line so the move stays
        balanced, then posts the move.

        :return: nothing
        :raises UserError: via ``_create_recognition_lines`` when the
            usage has no deferred side left to release
        """
        self.ensure_one()
        self._create_standard_move()
        self._create_recognition_lines()
        for recognition_line in self.recognition_line_ids:
            recognition_line._create_standard_ml()
        self._post_standard_move()

    def _get_deferred_line_types(self):
        """List the sides of the usage this document has to release.

        A side qualifies only while its own recognition method
        (``promotion_code_usage._get_recognition_method``) is
        ``deferred`` -- an ``immediate`` side already debited its own
        Final Account when the usage was approved, so releasing it
        again would book the discount twice. The referrer side
        additionally requires the usage's promotion code to have a
        referrer at all, since no referrer journal entry is issued
        without one.

        Read through ``sudo()``: answering this needs the usage's own
        promotion code, and that model carries a record rule scoped to
        ``user_id == user.id``. A user may perfectly well own a usage
        whose promotion code belongs to somebody else, and refusing to
        save their recognition over it -- with an Access Error naming
        a model they never asked about -- would be a security check
        firing on a technical lookup. The very same fields are already
        read this way by ``promotion_code_usage._compute_amount_to_
        recognize`` (``compute_sudo=True``).

        :return: a list holding ``'customer'``, ``'referrer'``, both,
            or neither, in that order
        """
        self.ensure_one()
        usage = self.usage_id.sudo()
        result = []
        if usage._get_recognition_method() == "deferred":
            result.append("customer")
        if (
            usage.promotion_code_id.partner_id
            and usage._get_recognition_method(referrer=True) == "deferred"
        ):
            result.append("referrer")
        return result

    def _create_recognition_lines(self):
        """Create one Recognition Line per deferred side of the usage.

        Each deferred side's own share is its own deferred amount (see
        ``_get_line_type_base_amount``) scaled by this document's own
        Ratio, rounded to the Company Currency's own precision. The
        rounding remainder is charged to the last line so the move
        stays balanced against this document's own Amount. Sides
        recognized on the spot are skipped entirely (see
        ``_get_deferred_line_types``).

        :return: the created
            ``promotion_code_usage_recognition_line`` recordset
        :raises UserError: when the usage has no deferred side left,
            so this document would post a journal entry with no line
        """
        self.ensure_one()
        Line = self.env["promotion_code_usage_recognition_line"]
        line_types = self._get_deferred_line_types()
        if not line_types:
            error_message = """
Document Type: %s
Context: Create recognition accounting entry
Database ID: %s
Problem: Usage '%s' has no deferred side left to release: neither its own \
Recognition Method nor its Referrer Recognition Method is 'Deferred'
Solution: Cancel this document, or set 'Recognition Method' (or 'Referrer \
Recognition Method') on the usage back to 'Deferred'
""" % (
                self._description,
                self.id,
                self.usage_id.display_name,
            )
            raise UserError(_(error_message))
        precision = self.company_currency_id.decimal_places
        amounts = [
            float_round(
                self._get_line_type_base_amount(line_type) * self.ratio,
                precision_digits=precision,
            )
            for line_type in line_types
        ]
        remainder = float_round(self.amount - sum(amounts), precision_digits=precision)
        amounts[-1] = float_round(amounts[-1] + remainder, precision_digits=precision)
        lines = Line
        for line_type, amount in zip(line_types, amounts):
            lines |= Line.create(self._prepare_recognition_line(line_type, amount))
        return lines

    def _get_line_type_base_amount(self, line_type):
        """Resolve the deferred amount one side of the usage carries.

        Each side's own journal entry line was booked with its own
        amount, so each side is released with its own amount too:
        'Referrer Discount Amount' for the referrer, 'Discount
        Amount' for the voucher user. The two coincide only while the
        promotion type's own 'Referrer Discount Type' is 'Same as
        Customer'. Their sum is the usage's own Amount To Recognize.

        :param line_type: ``'customer'`` or ``'referrer'``
        :return: the usage's own deferred amount for that side
        """
        self.ensure_one()
        if line_type == "referrer":
            return self.usage_id.referrer_discount_amount
        return self.usage_id.discount_amount

    def _prepare_recognition_line(self, line_type, amount):
        """Build one Recognition Line's create values.

        :param line_type: ``'customer'`` or ``'referrer'``
        :param amount: this Recognition Line's own share of
            ``amount``, already rounded
        :return: dict of ``promotion_code_usage_recognition_line``
            values
        """
        self.ensure_one()
        referrer = line_type == "referrer"
        return {
            "recognition_id": self.id,
            "line_type": line_type,
            "amount": amount,
            "debit_account_id": self.usage_id._get_final_account(referrer=referrer).id,
        }

    @ssi_decorator.post_cancel_action()
    def _10_delete_accounting_entry(self):
        """Delete this document's ``account.move``.

        :return: nothing
        """
        self.ensure_one()
        self._delete_standard_move()

    @ssi_decorator.post_cancel_action()
    def _20_delete_recognition_lines(self):
        """Delete this document's own Recognition Lines.

        Regenerated from scratch by ``_create_recognition_lines`` the
        next time this document reaches Done.

        :return: nothing
        """
        self.ensure_one()
        self.recognition_line_ids.unlink()

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        """Reconfigure the statusbar's visible states on the form view.

        :param view_arch: the parsed form view architecture
        :return: the (possibly modified) view architecture
        """
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch

    @api.model
    def _get_policy_field(self):
        """Register this model's policy fields for ``mixin.policy``.

        :return: the base policy fields of the standard three-mixin
            workflow combo
        """
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res
