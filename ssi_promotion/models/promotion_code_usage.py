# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class PromotionCodeUsage(models.Model):
    """
    Records one redemption of a promotion_code against an arbitrary Odoo
    document (sale order, invoice, etc. — depending on what the promotion
    type allows).

    Confirming a usage runs the promotion type's validity Python code
    together with the usage-limit and validity-period checks. Approving a
    usage (state open) automatically creates and posts a plain journal
    entry (account.move, move_type 'entry') for partner_id when
    allocation_ids has a 'customer' row, and a second one for
    promotion_code_id.partner_id when the code has a referrer and
    allocation_ids has a 'referrer' row (see the post_open_action
    hooks). A side without an allocation row gets no journal entry --
    its own credit line's account is resolved from allocation_ids,
    not from a partner's own accounting configuration (see
    '_get_allocation_account'). Each posted journal entry's own
    receivable journal item is kept on receivable_move_line_id /
    referrer_receivable_move_line_id. Cancelling the usage deletes
    both journal entries again and clears those four fields (see the
    post_cancel_action hook).

    Recognition Method controls which account those journal entry
    lines debit: Immediate (the default, copied from the promotion
    type) debits the Final Account right away; Deferred debits
    Deferred Account instead, so the discount can be recognized later
    by one or more promotion_code_usage_recognition documents.
    'Amount To Recognize', 'Amount Recognized', 'Amount Deferred', and
    'Recognition State' track that release; they stay 'Not
    Applicable' while Recognition Method is Immediate.

    allocation_ids lists reconcilable account.move.line records this
    usage's own journal entry(-ies) should reduce instead of only
    adding to the source partner's credit balance. Every allocation
    row of one source is also this usage's own source for that
    side's credit line account (see '_get_allocation_account'), so
    every row of one source must share one account. Opening a usage
    first validates every row and that per-source account sharing
    (see '_15_check_allocation'), then reconciles each source's own
    journal entry receivable line against its own allocation rows in
    order (see '_30_reconcile'). Cancelling the usage undoes that
    reconciliation before its own journal entry(-ies) are deleted
    (see '_05_unreconcile').
    """

    _name = "promotion_code_usage"
    _description = "Promotion Code Usage"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_confirm",
        "mixin.transaction_partner",
        "mixin.localdict",
    ]

    # A. Multiple Approval Attributes
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # B. Automatic View Element Attributes
    _automatically_insert_view_element = True
    _automatically_insert_open_button = False
    _automatically_insert_open_policy_fields = False

    # C. Form View Attributes
    _statusbar_visible_label = "draft,confirm,open"
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
        "action_approve",
        "action_reject",
        "action_done",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # D. Search View Attributes
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_open",
        "dom_done",
        "dom_cancel",
        "dom_reject",
    ]

    # E. Sequence Attribute
    _create_sequence_state = "open"

    # F. Field Definitions
    promotion_code_id = fields.Many2one(
        string="Promotion Code",
        comodel_name="promotion_code",
        domain=[("state", "=", "open")],
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Promotion code being used. Only codes in state 'Open' can "
        "be selected.",
    )
    type_id = fields.Many2one(
        string="Promotion Type",
        comodel_name="promotion_type",
        related="promotion_code_id.type_id",
        store=True,
        compute_sudo=True,
        help="Promotion type of the promotion code being used, copied for "
        "filtering and reporting convenience.",
    )
    partner_id = fields.Many2one(
        string="Voucher User",
        help="Partner who redeemed the promotion code. Receives the "
        "customer accounting entry when this usage is approved.",
    )
    date = fields.Date(
        string="Usage Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: date.today(),
        help="Date the promotion code was used. Checked against the "
        "promotion code's validity period when confirming this usage.",
    )
    document_reference = fields.Reference(
        string="Reference Document",
        selection="_selection_document_reference",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Document this usage is attached to (e.g. a sale order or an "
        "invoice). The document's model must be listed in the promotion "
        "type's 'Allowed Reference Models'.",
    )
    discount_amount = fields.Float(
        string="Discount Amount",
        compute="_compute_discount_amount",
        store=True,
        compute_sudo=True,
        help="Discount amount granted by this usage, computed from the "
        "promotion type's discount rule (fixed amount, percentage of the "
        "reference document's total, or custom Python code).",
    )
    move_id = fields.Many2one(
        string="Customer Accounting Entry",
        comodel_name="account.move",
        readonly=True,
        copy=False,
        help="Journal entry automatically created for 'Voucher User' "
        "when this usage is approved.",
    )
    referrer_move_id = fields.Many2one(
        string="Referrer Accounting Entry",
        comodel_name="account.move",
        readonly=True,
        copy=False,
        help="Journal entry automatically created for the promotion "
        "code's referrer (promotion_code_id.partner_id) when this "
        "usage is approved, if the promotion code has a referrer.",
    )
    receivable_move_line_id = fields.Many2one(
        string="Customer Receivable Journal Item",
        comodel_name="account.move.line",
        readonly=True,
        copy=False,
        help="Receivable journal item of 'Customer Accounting Entry', "
        "filled by the '_20_post_accounting_entry' hook when this "
        "usage's own customer journal entry is posted.",
    )
    referrer_receivable_move_line_id = fields.Many2one(
        string="Referrer Receivable Journal Item",
        comodel_name="account.move.line",
        readonly=True,
        copy=False,
        help="Receivable journal item of 'Referrer Accounting Entry', "
        "filled by the '_20_post_accounting_entry' hook when this "
        "usage's own referrer journal entry is posted.",
    )
    recognition_method = fields.Selection(
        string="Recognition Method",
        selection=[
            ("immediate", "Immediate"),
            ("deferred", "Deferred"),
        ],
        compute="_compute_recognition_method",
        store=True,
        readonly=False,
        compute_sudo=True,
        help="Defaulted from the promotion type's own 'Recognition "
        "Method', but may still be overridden manually while this "
        "usage is in Draft. Deferred routes the journal entry "
        "line(s) created on approval to 'Deferred Account' instead "
        "of their Final Account.",
    )
    recognition_date = fields.Date(
        string="Recognition Date",
        compute="_compute_recognition_date",
        store=True,
        readonly=False,
        compute_sudo=True,
        help="Date the deferred amount is due to be recognized. "
        "Defaulted to 'Usage Date', but may still be overridden "
        "manually while this usage is in Draft.",
    )
    deferred_account_id = fields.Many2one(
        string="Deferred Account",
        comodel_name="account.account",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Account debited on the journal entry line(s) created "
        "for this usage instead of their Final Account, while this "
        "usage's own 'Recognition Method' is Deferred. Defaulted from "
        "the promotion type's own 'Deferred Account'. Required while "
        "'Recognition Method' is Deferred.",
    )
    recognition_journal_id = fields.Many2one(
        string="Recognition Journal",
        comodel_name="account.journal",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Accounting journal used by promotion_code_usage_"
        "recognition documents created against this usage. "
        "Defaulted from the promotion type's own 'Recognition "
        "Journal'.",
    )
    amount_to_recognize = fields.Float(
        string="Amount To Recognize",
        compute="_compute_amount_to_recognize",
        store=True,
        compute_sudo=True,
        help="Total amount this usage's journal entry line(s) debited "
        "to Deferred Account, due to be released by "
        "promotion_code_usage_recognition documents: 'Discount "
        "Amount', doubled when this usage's promotion code has a "
        "referrer (both the customer and referrer journal entry "
        "lines carry the same 'Discount Amount').",
    )
    amount_recognized = fields.Float(
        string="Amount Recognized",
        compute="_compute_amount_recognized",
        store=True,
        compute_sudo=True,
        help="Sum of 'Amount' of every Done "
        "promotion_code_usage_recognition document created against "
        "this usage.",
    )
    amount_deferred = fields.Float(
        string="Amount Deferred",
        compute="_compute_amount_deferred",
        store=True,
        compute_sudo=True,
        help="'Amount To Recognize' still not released: 'Amount To "
        "Recognize' minus 'Amount Recognized'.",
    )
    recognition_state = fields.Selection(
        string="Recognition State",
        selection=[
            ("not_applicable", "Not Applicable"),
            ("pending", "Pending"),
            ("partial", "Partially Recognized"),
            ("recognized", "Recognized"),
        ],
        compute="_compute_recognition_state",
        store=True,
        compute_sudo=True,
        help="Progress releasing this usage's own 'Amount To "
        "Recognize'. 'Not Applicable' while 'Recognition Method' is "
        "Immediate; otherwise 'Pending' until the first Done "
        "recognition, 'Partially Recognized' until 'Amount "
        "Recognized' reaches 'Amount To Recognize', then "
        "'Recognized'.",
    )
    recognition_ids = fields.One2many(
        string="Recognitions",
        comodel_name="promotion_code_usage_recognition",
        inverse_name="usage_id",
        readonly=True,
        help="promotion_code_usage_recognition documents created "
        "against this usage, releasing its own 'Amount Deferred' "
        "into their own Final Account(s).",
    )
    allocation_ids = fields.One2many(
        string="Allocations",
        comodel_name="promotion_code_usage_allocation",
        inverse_name="usage_id",
        copy=False,
        help="Receivable journal items this usage's own journal "
        "entry(-ies) should be reconciled against once this usage "
        "opens (see the '_30_reconcile' hook). Journal items "
        "reached after their own source journal entry runs out of "
        "residual keep an empty 'Partial Reconcile'.",
    )

    # G. Compute Methods
    @api.model
    def _selection_document_reference(self):
        models_obj = self.env["ir.model"]
        allowed_model_ids = (
            self.env["promotion_type"].sudo().search([]).allowed_model_ids.ids
        )
        allowed_models = models_obj.sudo().browse(allowed_model_ids)
        return [(model.model, model.name) for model in allowed_models]

    @api.depends(
        "promotion_code_id",
        "promotion_code_id.discount_type",
        "promotion_code_id.discount_amount",
        "promotion_code_id.discount_percentage",
        "document_reference",
    )
    def _compute_discount_amount(self):
        """Compute the discount amount granted by this usage.

        Delegates to ``_get_discount_amount`` for the actual rule.

        :return: nothing; assigns ``discount_amount``
        """
        for record in self:
            record.discount_amount = record._get_discount_amount()

    def _get_discount_amount(self):
        """Resolve the discount amount per the promotion type's rule.

        Fixed returns the promotion code's own 'Discount Amount'.
        Percentage applies the promotion code's 'Discount Percentage'
        to ``_get_reference_base_amount``. Python evaluates the
        promotion type's ``discount_python_code`` via
        ``_evaluate_discount_python_code``.

        :return: the discount amount, ``0.0`` when the promotion
            code is empty or the discount type is unrecognized
        """
        self.ensure_one()
        if not self.promotion_code_id:
            return 0.0
        discount_type = self.promotion_code_id.discount_type
        if discount_type == "fixed":
            return self.promotion_code_id.discount_amount
        if discount_type == "percentage":
            base_amount = self._get_reference_base_amount()
            return base_amount * self.promotion_code_id.discount_percentage / 100.0
        if discount_type == "python":
            return self._evaluate_discount_python_code()
        return 0.0

    def _get_reference_base_amount(self):
        """Resolve the base amount a percentage discount applies to.

        :return: 'Reference Document' ``amount_total`` when that
            field exists on the document, else ``0.0``
        """
        self.ensure_one()
        if not self.document_reference:
            return 0.0
        if "amount_total" in self.document_reference._fields:
            return self.document_reference.amount_total
        return 0.0

    def _evaluate_discount_python_code(self):
        """Evaluate the promotion type's discount Python code.

        Runs ``type_id.discount_python_code`` with the localdict from
        ``_get_localdict`` (``promotion_code``, ``promotion_type``,
        ``reference_document``, plus the base variables provided by
        ``mixin.localdict``). The code is expected to assign the
        discount amount to a ``result`` variable.

        :return: ``localdict["result"]``, or ``0.0`` when the code
            does not set it
        """
        self.ensure_one()
        localdict = self._get_localdict()
        code = self.promotion_code_id.type_id.discount_python_code
        safe_eval(code, localdict, mode="exec", nocopy=True)
        return localdict.get("result", 0.0)

    def _get_localdict(self):
        """Build the safe-eval context for this usage's Python code.

        Extends ``_get_default_localdict`` (``mixin.localdict``) with
        ``promotion_code``, ``promotion_type``, and
        ``reference_document``, shared by the discount and validity
        Python code fields.

        :return: dict passed as ``localdict`` to ``safe_eval``
        """
        self.ensure_one()
        localdict = self._get_default_localdict()
        localdict.update(
            {
                "promotion_code": self.promotion_code_id,
                "promotion_type": self.promotion_code_id.type_id,
                "reference_document": self.document_reference,
            }
        )
        return localdict

    @api.depends("type_id.recognition_method")
    def _compute_recognition_method(self):
        """Default Recognition Method from the promotion type's config.

        :return: nothing; assigns ``recognition_method``
        """
        for record in self:
            result = "immediate"
            if record.type_id:
                result = record.type_id.recognition_method
            record.recognition_method = result

    @api.depends("date")
    def _compute_recognition_date(self):
        """Default Recognition Date to this usage's own Usage Date.

        :return: nothing; assigns ``recognition_date``
        """
        for record in self:
            record.recognition_date = record.date

    @api.depends(
        "discount_amount",
        "promotion_code_id.partner_id",
    )
    def _compute_amount_to_recognize(self):
        """Compute the total amount due to be released by recognitions.

        Doubles 'Discount Amount' when this usage's promotion code
        has a referrer, since the customer and referrer journal
        entry lines both carry the same 'Discount Amount'.

        :return: nothing; assigns ``amount_to_recognize``
        """
        for record in self:
            result = record.discount_amount
            if record.promotion_code_id.partner_id:
                result = 2 * record.discount_amount
            record.amount_to_recognize = result

    @api.depends(
        "recognition_ids.state",
        "recognition_ids.amount",
    )
    def _compute_amount_recognized(self):
        """Sum the Amount of every Done recognition of this usage.

        :return: nothing; assigns ``amount_recognized``
        """
        for record in self:
            done_recognitions = record.recognition_ids.filtered(
                lambda recognition: recognition.state == "done"
            )
            record.amount_recognized = sum(done_recognitions.mapped("amount"))

    @api.depends(
        "amount_to_recognize",
        "amount_recognized",
    )
    def _compute_amount_deferred(self):
        """Compute the remaining amount still not recognized.

        :return: nothing; assigns ``amount_deferred``
        """
        for record in self:
            record.amount_deferred = (
                record.amount_to_recognize - record.amount_recognized
            )

    @api.depends(
        "recognition_method",
        "amount_to_recognize",
        "amount_recognized",
    )
    def _compute_recognition_state(self):
        """Compute the recognition progress state.

        :return: nothing; assigns ``recognition_state``
        """
        for record in self:
            record.recognition_state = record._get_recognition_state()

    def _get_recognition_state(self):
        """Resolve this usage's own recognition progress state.

        :return: ``'not_applicable'``, ``'pending'``, ``'partial'``,
            or ``'recognized'``
        """
        self.ensure_one()
        if self.recognition_method != "deferred":
            return "not_applicable"
        precision = self.env.company.currency_id.decimal_places
        if float_is_zero(self.amount_recognized, precision_digits=precision):
            return "pending"
        if (
            float_compare(
                self.amount_recognized,
                self.amount_to_recognize,
                precision_digits=precision,
            )
            >= 0
        ):
            return "recognized"
        return "partial"

    # G2. Onchange Methods
    @api.onchange("type_id")
    def onchange_deferred_account_id(self):
        self.deferred_account_id = False
        if self.type_id:
            self.deferred_account_id = self.type_id.deferred_account_id

    @api.onchange("type_id")
    def onchange_recognition_journal_id(self):
        """Default Recognition Journal from the promotion type's own
        Recognition Journal.

        :return: nothing
        """
        self.recognition_journal_id = False
        if self.type_id:
            self.recognition_journal_id = self.type_id.recognition_journal_id

    # H. Constrains
    @api.constrains(
        "document_reference",
        "promotion_code_id",
    )
    def _check_document_reference_model(self):
        """Require 'Reference Document' model to be allowed by the type.

        :raises ValidationError: when 'Reference Document' is set and
            its model is not listed in the promotion type's 'Allowed
            Reference Models'
        """
        for record in self.sudo():
            if not record._check_document_reference_model_condition():
                error_message = """
Context: Set reference document on promotion code usage
Database ID: %s
Problem: Reference document model '%s' is not allowed by promotion type '%s'
Solution: Choose a document whose model is listed in the promotion type's \
Allowed Reference Models, or update that configuration
""" % (
                    record.id,
                    record.document_reference._name,
                    record.type_id.display_name,
                )
                raise ValidationError(_(error_message))

    def _check_document_reference_model_condition(self):
        """Check whether 'Reference Document' model is allowed.

        :return: ``True`` when 'Reference Document' is empty, or its
            model is listed in the promotion type's 'Allowed
            Reference Models'
        """
        self.ensure_one()
        if not self.document_reference:
            return True
        model_name = self.document_reference._name
        allowed_models = self.type_id.allowed_model_ids.mapped("model")
        return model_name in allowed_models

    @api.constrains(
        "recognition_method",
        "deferred_account_id",
    )
    def _check_deferred_account_required(self):
        """Require Deferred Account whenever Recognition Method is
        Deferred.

        :raises ValidationError: when 'Recognition Method' is
            ``deferred`` and 'Deferred Account' is empty.
        """
        for record in self:
            if not record._check_deferred_account_required_condition():
                error_message = """
Context: Set recognition method on promotion code usage
Database ID: %s
Problem: Recognition Method is 'Deferred' but Deferred Account is empty
Solution: Set 'Deferred Account' on this usage, or on its promotion \
type so it defaults automatically
""" % (
                    record.id,
                )
                raise ValidationError(_(error_message))

    def _check_deferred_account_required_condition(self):
        """Check whether Deferred Account is set when required.

        :return: ``True`` when 'Recognition Method' is not
            ``deferred``, or when 'Deferred Account' is set
        """
        self.ensure_one()
        if self.recognition_method != "deferred":
            return True
        return bool(self.deferred_account_id)

    @api.constrains(
        "recognition_method",
        "recognition_date",
        "date",
    )
    def _check_recognition_date_not_before_date(self):
        """Require Recognition Date on/after Usage Date while Deferred.

        :raises ValidationError: when 'Recognition Method' is
            ``deferred`` and 'Recognition Date' falls before 'Usage
            Date'.
        """
        for record in self:
            if not record._check_recognition_date_not_before_date_condition():
                error_message = """
Context: Set recognition date on promotion code usage
Database ID: %s
Problem: Recognition Date (%s) is earlier than Usage Date (%s) while \
Recognition Method is 'Deferred'
Solution: Set 'Recognition Date' to a date on or after 'Usage Date'
""" % (
                    record.id,
                    record.recognition_date,
                    record.date,
                )
                raise ValidationError(_(error_message))

    def _check_recognition_date_not_before_date_condition(self):
        """Check whether Recognition Date respects Usage Date.

        :return: ``True`` when 'Recognition Method' is not
            ``deferred``, or when 'Recognition Date' is not before
            'Usage Date'
        """
        self.ensure_one()
        if self.recognition_method != "deferred":
            return True
        if not self.recognition_date or not self.date:
            return True
        return self.recognition_date >= self.date

    # I. Validity Check (pre-confirm hook)
    def _check_validity(self):
        """Check every validity rule before this usage can confirm.

        Combines the usage-limit, validity-period, and validity
        Python code checks; used by the ``_10_check_validity`` hook.

        :return: ``True`` only when all three checks pass
        """
        self.ensure_one()
        return (
            self._check_validity_usage_limit()
            and self._check_validity_period()
            and self._check_validity_python_code()
        )

    def _check_validity_usage_limit(self):
        """Check the promotion code has not reached its usage limit.

        :return: ``True`` when 'Usage Limit' is ``0`` (unlimited), or
            the promotion code's current 'Usage Count' is below it
        """
        self.ensure_one()
        limit = self.promotion_code_id.usage_limit
        if limit <= 0:
            return True
        return self.promotion_code_id.usage_count < limit

    def _check_validity_period(self):
        """Check 'Usage Date' falls within the promotion code's period.

        :return: ``True`` when the promotion type has no validity
            period, or 'Usage Date' is on/after 'Date Start' and
            on/before 'Date End' of the promotion code
        """
        self.ensure_one()
        code = self.promotion_code_id
        if not code.type_id.has_validity:
            return True
        if code.date_start and self.date < code.date_start:
            return False
        if code.date_end and self.date > code.date_end:
            return False
        return True

    def _check_validity_python_code(self):
        """Evaluate the promotion type's validity Python code.

        Runs ``type_id.validity_python_code`` with the localdict from
        ``_get_localdict`` (``promotion_code``, ``promotion_type``,
        ``reference_document``, plus the base variables provided by
        ``mixin.localdict``). The code is expected to assign a
        boolean to a ``result`` variable.

        :return: ``True`` when the code is empty, or
            ``localdict["result"]``, defaulting to ``True``
        """
        self.ensure_one()
        code = self.type_id.validity_python_code
        if not code:
            return True
        localdict = self._get_localdict()
        safe_eval(code, localdict, mode="exec", nocopy=True)
        return bool(localdict.get("result", True))

    @ssi_decorator.pre_confirm_check()
    def _10_check_validity(self):
        """Block confirming a usage that fails ``_check_validity``.

        Runs on the pre-check of the draft-to-confirm transition
        (``action_confirm``), before the state actually changes.

        :raises UserError: when ``_check_validity`` returns falsy
        """
        if not self._check_validity():
            error_message = """
Context: Confirm promotion code usage
Database ID: %s
Problem: Usage does not satisfy the promotion type's validity rules
Solution: Check the usage limit, validity period, and validity Python \
code configured on promotion type '%s'
""" % (
                self.id,
                self.type_id.display_name,
            )
            raise UserError(_(error_message))

    # K1. Populate Allocation (button, inline action)
    def action_populate_allocation(self):
        """Fill 'Allocations' from the reference document's own
        eligible journal items.

        Delegates to
        ``document_reference._get_promotion_move_lines()`` for the
        eligible ``account.move.line`` recordset, walking it in the
        order it is returned and skipping any journal item already
        present on 'Allocations'. Every new row is created with
        'Source' 'Voucher User'. Wired to a button on the
        'Allocation' page -- an inline action documented as a Flow
        step in ``docs/promotion_code_usage/01-create.md`` and
        ``docs/promotion_code_usage/02-edit.md``, not a file of its
        own.

        :raises UserError: via ``_check_populate_allocation`` when
            this usage cannot be populated yet
        :return: ``True``
        """
        self.ensure_one()
        self._check_populate_allocation()
        Allocation = self.env[  # pylint: disable=invalid-name
            "promotion_code_usage_allocation"
        ]
        existing_move_line_ids = self.allocation_ids.mapped("move_line_id").ids
        move_lines = self.document_reference._get_promotion_move_lines()
        sequence = 5
        for move_line in move_lines:
            if move_line.id in existing_move_line_ids:
                continue
            Allocation.create(
                {
                    "usage_id": self.id,
                    "move_line_id": move_line.id,
                    "source": "customer",
                    "sequence": sequence,
                }
            )
            sequence += 5
        return True

    def _check_populate_allocation(self):
        """Validate this usage can run ``action_populate_allocation``.

        :raises UserError: when 'Status' is not 'Draft', 'Reference
            Document' is empty, the reference document's own model
            does not carry ``mixin.promotion_object``, or the
            reference document has no eligible journal item at all
        """
        self.ensure_one()
        if self.state != "draft":
            error_message = """
Context: Populate allocation from reference document
Database ID: %s
Problem: Status is not 'Draft'
Solution: Only a Draft usage can populate its own 'Allocations'
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        if not self.document_reference:
            error_message = """
Context: Populate allocation from reference document
Database ID: %s
Problem: 'Reference Document' is empty
Solution: Set 'Reference Document' before populating 'Allocations'
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        if "promotion_usage_ids" not in self.document_reference._fields:
            error_message = """
Context: Populate allocation from reference document
Database ID: %s
Problem: Reference document model '%s' does not support automatic \
allocation (it does not carry mixin.promotion_object)
Solution: Choose a reference document whose model inherits \
mixin.promotion_object, or add rows to 'Allocations' manually
""" % (
                self.id,
                self.document_reference._name,
            )
            raise UserError(_(error_message))
        if not self.document_reference._get_promotion_move_lines():
            error_message = """
Context: Populate allocation from reference document
Database ID: %s
Problem: Reference document '%s' has no eligible journal item to \
allocate (reconcilable account, posted move, positive residual)
Solution: Post the reference document, or wait until it has an \
outstanding receivable balance
""" % (
                self.id,
                self.document_reference.display_name,
            )
            raise UserError(_(error_message))

    # K2. Allocation Check (pre-open hook)
    @ssi_decorator.pre_open_action()
    def _15_check_allocation(self):
        """Validate every allocation row before this usage can open.

        Runs on the pre-action of the confirm-to-open transition
        (approval, ``action_open``), before the state actually
        changes and before ``_30_reconcile`` runs. Delegates each
        row of 'Allocations' to ``_check_allocation_line``, then
        checks every 'Source' shares one account with
        ``_check_allocation_account_per_source`` -- the credit
        account of that source's own journal entry is resolved from
        'Allocations' (see ``_get_allocation_account``), and this
        usage keeps a single credit line per source.

        :raises UserError: via ``_check_allocation_line`` or
            ``_check_allocation_account_per_source`` when any
            allocation row fails a check
        """
        self.ensure_one()
        for line in self.allocation_ids:
            self._check_allocation_line(line)
        self._check_allocation_account_per_source()

    def _check_allocation_line(self, line):
        """Check one allocation row is safe to reconcile against.

        Any reconcilable account is accepted -- this hook no longer
        requires the row's own 'Journal Item' to sit on the expected
        source partner's own receivable account (see
        ``_check_allocation_account_per_source`` for the constraint
        that replaces it: every row of one 'Source' still shares a
        single account).

        :param line: a ``promotion_code_usage_allocation`` record
            of this usage's own 'Allocations'
        :raises UserError: when the row's own 'Journal Item' is not
            reconcilable, not posted, already reconciled or has no
            positive residual, is in a foreign currency, does not
            belong to the expected source partner, or the row's own
            'Source' is 'Referrer' while this usage's own promotion
            code has none
        """
        self.ensure_one()
        move_line = line.move_line_id
        if not move_line.account_id.reconcile:
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own journal item '%s' is on an account that \
does not allow reconciliation
Solution: Choose a journal item whose account has 'Allow Reconciliation' \
enabled
""" % (
                self.id,
                move_line.display_name,
            )
            raise UserError(_(error_message))
        if move_line.parent_state != "posted":
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own journal item '%s' belongs to a journal \
entry that is not posted
Solution: Choose a journal item from a posted journal entry, or post \
the journal entry first
""" % (
                self.id,
                move_line.display_name,
            )
            raise UserError(_(error_message))
        if move_line.reconciled or not (move_line.amount_residual > 0):
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own journal item '%s' has no positive \
residual amount left to reconcile
Solution: Choose a journal item that still has an outstanding \
residual amount
""" % (
                self.id,
                move_line.display_name,
            )
            raise UserError(_(error_message))
        if move_line.currency_id != move_line.company_currency_id:
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own journal item '%s' is denominated in a \
foreign currency, which this feature does not support
Solution: Choose a journal item posted in the company currency
""" % (
                self.id,
                move_line.display_name,
            )
            raise UserError(_(error_message))
        if line.source == "referrer" and not self.promotion_code_id.partner_id:
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own 'Source' is 'Referrer' but this usage's \
own promotion code has no referrer
Solution: Change the row's 'Source' to 'Voucher User', or set a \
referrer on the promotion code
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        expected_partner = self._get_allocation_expected_partner(line.source)
        if not expected_partner or move_line.partner_id != expected_partner:
            error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation row's own journal item '%s' does not belong to the \
expected source partner
Solution: Choose a journal item whose partner matches the '%s' source \
for this usage
""" % (
                self.id,
                move_line.display_name,
                line.source,
            )
            raise UserError(_(error_message))

    def _check_allocation_account_per_source(self):
        """Require every allocation row of one 'Source' to share one
        account.

        A single credit line is posted per source (see
        ``_prepare_customer_move_data`` /
        ``_prepare_referrer_move_data``), so its own account cannot
        represent 'Allocations' spread across more than one account.

        :raises UserError: when 'Allocations' of the same 'Source'
            target 'Journal Item' on more than one account
        """
        self.ensure_one()
        for source in ("customer", "referrer"):
            lines = self.allocation_ids.filtered(
                lambda allocation, source=source: allocation.source == source
            )
            accounts = lines.mapped("move_line_id.account_id")
            if len(accounts) > 1:
                error_message = """
Context: Open promotion code usage
Database ID: %s
Problem: Allocation rows under Source '%s' target journal items on more \
than one account (%s)
Solution: Make every allocation row of that Source point to journal \
items sharing the same account
""" % (
                    self.id,
                    source,
                    ", ".join(accounts.mapped("display_name")),
                )
                raise UserError(_(error_message))

    def _get_allocation_account(self, source):
        """Resolve the account this side's own allocation rows share.

        Used both by ``_check_allocation_account_per_source`` (via
        the constraint it enforces) and by ``_create_customer_move``
        / ``_create_referrer_move`` to resolve the credit account of
        this usage's own journal entry(-ies).

        :param source: ``'customer'`` or ``'referrer'``
        :return: the ``account.account`` shared by every allocation
            row of that 'Source', empty when that 'Source' has no
            allocation row
        """
        self.ensure_one()
        lines = self.allocation_ids.filtered(
            lambda allocation, source=source: allocation.source == source
        )
        return lines.mapped("move_line_id.account_id")[:1]

    def _get_allocation_expected_partner(self, source):
        """Resolve the partner an allocation row's own 'Source' expects.

        :param source: ``'customer'`` or ``'referrer'``
        :return: 'Voucher User' when 'customer', this usage's own
            promotion code referrer ('promotion_code_id.partner_id')
            when 'referrer', possibly empty
        """
        self.ensure_one()
        if source == "referrer":
            return self.promotion_code_id.partner_id
        return self.partner_id

    # L. Accounting Entry Creation (post-open hook)
    @ssi_decorator.post_open_action()
    def _10_create_accounting_entry(self):
        """Create the journal entry(-ies) for a newly approved usage.

        Runs after the confirm-to-open transition (approval,
        ``action_open``) completes. Creates the customer journal
        entry when 'Allocations' has at least one 'customer' row
        (its own credit account is resolved from there, see
        ``_get_allocation_account``); also creates the referrer
        journal entry when the promotion code has a referrer
        ('partner_id' set) and 'Allocations' has at least one
        'referrer' row. A source without an allocation row does not
        issue a journal entry.
        """
        self._create_customer_move()
        self._create_referrer_move()

    def _create_customer_move(self):
        """Create the customer journal entry for this usage, once.

        No-op when 'Customer Accounting Entry' is already set, or
        when 'Allocations' has no 'customer' row -- there is then no
        account to credit (see ``_get_allocation_account``).

        :raises UserError: via ``_check_accounting_configuration``
            when the promotion type accounting configuration is
            incomplete
        """
        self.ensure_one()
        if self.move_id:
            return
        receivable_account = self._get_allocation_account("customer")
        if not receivable_account:
            return
        self._check_accounting_configuration(referrer=False)
        move = self.env["account.move"].create(
            self._prepare_customer_move_data(receivable_account)
        )
        self.write({"move_id": move.id})

    def _create_referrer_move(self):
        """Create the referrer journal entry for this usage, once.

        No-op when 'Referrer Accounting Entry' is already set, the
        promotion code has no referrer ('partner_id' empty), or
        'Allocations' has no 'referrer' row -- there is then no
        account to credit (see ``_get_allocation_account``).

        :raises UserError: via ``_check_accounting_configuration``
            when the promotion type accounting configuration is
            incomplete
        """
        self.ensure_one()
        if self.referrer_move_id:
            return
        if not self.promotion_code_id.partner_id:
            return
        receivable_account = self._get_allocation_account("referrer")
        if not receivable_account:
            return
        self._check_accounting_configuration(referrer=True)
        move = self.env["account.move"].create(
            self._prepare_referrer_move_data(receivable_account)
        )
        self.write({"referrer_move_id": move.id})

    @ssi_decorator.post_open_action()
    def _20_post_accounting_entry(self):
        """Post the journal entry(-ies) created by
        ``_10_create_accounting_entry``.

        Runs after the confirm-to-open transition (approval,
        ``action_open``) completes, right after journal entry
        creation, so the "create then post" order reads from the
        prefix numbers. Posts 'Customer Accounting Entry' and, when
        present, 'Referrer Accounting Entry', then fills their own
        receivable journal item field.
        """
        self._post_customer_move()
        self._post_referrer_move()

    def _post_customer_move(self):
        """Post 'Customer Accounting Entry' and fill its receivable line.

        No-op when 'Customer Accounting Entry' is empty or already
        'posted'.

        :return: nothing
        """
        self.ensure_one()
        if not self.move_id or self.move_id.state == "posted":
            return
        self.move_id.action_post()
        self.receivable_move_line_id = self._get_receivable_move_line(self.move_id)

    def _post_referrer_move(self):
        """Post 'Referrer Accounting Entry' and fill its receivable line.

        No-op when 'Referrer Accounting Entry' is empty or already
        'posted'.

        :return: nothing
        """
        self.ensure_one()
        move = self.referrer_move_id
        if not move or move.state == "posted":
            return
        move.action_post()
        self.referrer_receivable_move_line_id = self._get_receivable_move_line(move)

    def _get_receivable_move_line(self, move):
        """Resolve a posted journal entry's own receivable journal item.

        ``move`` always carries exactly the two lines built by
        ``_prepare_customer_move_data`` / ``_prepare_referrer_move_data``:
        a debit-only discount line, and a credit-only line on the
        account resolved from 'Allocations' (see
        ``_get_allocation_account``). That account need not carry
        'internal_type' 'receivable' -- ``_check_allocation_line``
        accepts any reconcilable account -- so the credit line is
        picked by its own 'Credit' side instead.

        :param move: a posted ``account.move`` (journal entry)
        :return: the ``account.move.line`` on the credit side,
            possibly empty
        """
        self.ensure_one()
        return move.line_ids.filtered(lambda line: line.credit > 0)[:1]

    # L2. Allocation Reconciliation (post-open hook)
    @ssi_decorator.post_open_action()
    def _30_reconcile(self):
        """Reconcile the journal entry(-ies) against every allocation row.

        Runs after ``_20_post_accounting_entry``, once both journal
        entries are posted, so their own receivable journal item is
        available on 'Customer Receivable Journal Item' /
        'Referrer Receivable Journal Item'. Consumes each source's
        own journal entry receivable line against this usage's own
        'Allocations', in ``_order`` (grouped by 'Source'), skipping
        rows once that source's journal entry runs out of residual.
        """
        self.ensure_one()
        self._reconcile_allocation_source("customer")
        self._reconcile_allocation_source("referrer")

    def _reconcile_allocation_source(self, source):
        """Consume one source's own journal entry against its rows.

        A journal entry's own receivable line sits on the credit
        side of its journal entry, so its own 'Amount Residual' is
        negative (``balance = debit - credit``) -- unlike an
        allocation row's own target line, which sits on the debit
        side and is checked for a positive residual instead (see
        ``_check_allocation_line``). Exhaustion is therefore read
        off a zero residual, not a positive one.

        :param source: ``'customer'`` or ``'referrer'``
        :return: nothing
        """
        self.ensure_one()
        receivable_move_line = self._get_allocation_receivable_move_line(source)
        if not receivable_move_line:
            return
        precision = self.env.company.currency_id.decimal_places
        lines = self.allocation_ids.filtered(
            lambda allocation: allocation.source == source
        )
        for line in lines:
            if receivable_move_line.reconciled or float_is_zero(
                receivable_move_line.amount_residual, precision_digits=precision
            ):
                break
            line._reconcile(receivable_move_line)

    def _get_allocation_receivable_move_line(self, source):
        """Resolve one source's own journal entry receivable line.

        :param source: ``'customer'`` or ``'referrer'``
        :return: 'Customer Receivable Journal Item' for
            ``'customer'``, 'Referrer Receivable Journal Item' for
            ``'referrer'``, possibly empty
        """
        self.ensure_one()
        if source == "referrer":
            return self.referrer_receivable_move_line_id
        return self.receivable_move_line_id

    def _check_accounting_configuration(self, referrer=False):
        """Require a complete accounting configuration for this side.

        The credit (receivable) line's own account no longer comes
        from the partner's own 'property_account_receivable_id' --
        it is resolved from 'Allocations' instead (see
        ``_get_allocation_account``), and its own presence is
        already guaranteed by the caller (``_create_customer_move`` /
        ``_create_referrer_move``) before this check runs. Only the
        promotion type's own configuration is checked here.

        :param referrer: check the referrer's own configuration
            instead of the voucher user's
        :raises UserError: when the resolved journal is empty, or
            the resolved discount account
            (``_get_discount_account``) is empty
        """
        self.ensure_one()
        promotion_type = self.type_id
        journal = (
            promotion_type.referrer_journal_id or promotion_type.journal_id
            if referrer
            else promotion_type.journal_id
        )
        if not journal:
            error_message = """
Context: Create accounting entry from promotion code usage
Database ID: %s
Problem: Promotion type '%s' does not have a Journal configured
Solution: Set 'Discount Journal' (or 'Referrer Discount Journal') on the \
promotion type
""" % (
                self.id,
                promotion_type.display_name,
            )
            raise UserError(_(error_message))
        if not self._get_discount_account(referrer=referrer):
            error_message = """
Context: Create accounting entry from promotion code usage
Database ID: %s
Problem: Promotion type '%s' does not have a Discount Account configured
Solution: Set 'Discount Account' (and the 'Discount Product' income \
account fallback) on the promotion type, or 'Deferred Account' while \
'Recognition Method' is Deferred
""" % (
                self.id,
                promotion_type.display_name,
            )
            raise UserError(_(error_message))

    def _get_move_partner(self, referrer=False):
        """Resolve the partner one side of the journal entry belongs to.

        :param referrer: resolve the promotion code's own referrer
            instead of the voucher user's
        :return: a ``res.partner`` record, possibly empty
        """
        self.ensure_one()
        if referrer:
            return self.promotion_code_id.partner_id
        return self.partner_id

    def _get_final_account(self, referrer=False):
        """Resolve the non-deferred account for a journal entry line.

        Extension point: override to change how the customer or
        referrer journal entry line's own Final Account is resolved,
        independently of 'Recognition Method'. 'Discount Account'
        (``account_id``) wins over resolution when set, on either
        side. Otherwise the account is resolved through the Product
        Usage Account Type mechanism
        (``product.product._get_product_account``), walking product
        -> template -> category -> usage type's own 'Account', for
        the product and discount usage that apply to this side:
        'Discount Product'/'Discount Usage' for the voucher user,
        'Referrer Discount Product'/'Referrer Discount Usage'
        (falling back to the voucher user's own when either is
        empty) for the referrer.

        :param referrer: resolve the referrer's Final Account instead
            of the voucher user's
        :return: an ``account.account`` record, possibly empty
        """
        self.ensure_one()
        promotion_type = self.type_id
        if promotion_type.account_id:
            return promotion_type.account_id
        if referrer:
            product = promotion_type.referrer_product_id or promotion_type.product_id
            usage = (
                promotion_type.referrer_discount_usage_id
                or promotion_type.discount_usage_id
            )
        else:
            product = promotion_type.product_id
            usage = promotion_type.discount_usage_id
        if not product:
            return product
        return product._get_product_account(usage_code=usage.code)

    def _get_discount_account(self, referrer=False):
        """Resolve the account a journal entry line of this usage debits.

        Returns this usage's own 'Deferred Account' while
        'Recognition Method' is ``deferred``; otherwise falls back to
        ``_get_final_account``, keeping the Immediate behaviour
        unchanged.

        :param referrer: resolve the referrer's account instead of
            the voucher user's
        :return: an ``account.account`` record, possibly empty
        """
        self.ensure_one()
        if self.recognition_method == "deferred":
            return self.deferred_account_id
        return self._get_final_account(referrer=referrer)

    def _prepare_customer_move_data(self, receivable_account):
        """Build the customer journal entry ``account.move`` values.

        Two lines: a debit line on
        ``_get_discount_account(referrer=False)``, and a credit line
        on ``receivable_account``.

        :param receivable_account: account credited by the credit
            line, resolved by the caller
            (``_get_allocation_account``) from this usage's own
            'customer' 'Allocations'
        :return: dict of ``account.move`` values
        """
        self.ensure_one()
        promotion_type = self.type_id
        partner = self._get_move_partner(referrer=False)
        return {
            "journal_id": promotion_type.journal_id.id,
            "partner_id": partner.id,
            "date": self.date,
            "ref": self.name,
            "line_ids": [
                (
                    0,
                    0,
                    self._prepare_discount_line_data(
                        partner, self._get_discount_account(referrer=False)
                    ),
                ),
                (
                    0,
                    0,
                    self._prepare_receivable_line_data(partner, receivable_account),
                ),
            ],
        }

    def _prepare_referrer_move_data(self, receivable_account):
        """Build the referrer journal entry ``account.move`` values.

        Two lines: a debit line on
        ``_get_discount_account(referrer=True)``, and a credit line
        on ``receivable_account``.

        :param receivable_account: account credited by the credit
            line, resolved by the caller
            (``_get_allocation_account``) from this usage's own
            'referrer' 'Allocations'
        :return: dict of ``account.move`` values
        """
        self.ensure_one()
        promotion_type = self.type_id
        partner = self._get_move_partner(referrer=True)
        journal = promotion_type.referrer_journal_id or promotion_type.journal_id
        return {
            "journal_id": journal.id,
            "partner_id": partner.id,
            "date": self.date,
            "ref": self.name,
            "line_ids": [
                (
                    0,
                    0,
                    self._prepare_discount_line_data(
                        partner, self._get_discount_account(referrer=True)
                    ),
                ),
                (
                    0,
                    0,
                    self._prepare_receivable_line_data(partner, receivable_account),
                ),
            ],
        }

    def _get_move_line_label(self):
        """Build the label shared by both lines of a journal entry.

        Combines this usage's own document number with its own
        promotion code's voucher code.

        :return: the composed label string
        """
        self.ensure_one()
        return "%s - %s" % (self.name, self.promotion_code_id.voucher_code)

    def _prepare_discount_line_data(self, partner, account):
        """Build the debit (discount) ``account.move.line`` values dict.

        :param partner: partner recorded on the line
        :param account: account debited by the line
        :return: dict of ``account.move.line`` values
        """
        self.ensure_one()
        return {
            "partner_id": partner.id,
            "account_id": account.id,
            "name": self._get_move_line_label(),
            "debit": self.discount_amount,
            "credit": 0.0,
        }

    def _prepare_receivable_line_data(self, partner, account):
        """Build the credit (receivable) ``account.move.line`` values dict.

        :param partner: partner recorded on the line
        :param account: account credited by the line -- the account
            shared by this side's own 'Allocations' rows (see
            ``_get_allocation_account``), not the partner's own
            'property_account_receivable_id'
        :return: dict of ``account.move.line`` values
        """
        self.ensure_one()
        return {
            "partner_id": partner.id,
            "account_id": account.id,
            "name": self._get_move_line_label(),
            "debit": 0.0,
            "credit": self.discount_amount,
        }

    # M0. Allocation Un-Reconciliation (post-cancel hook)
    @ssi_decorator.post_cancel_action()
    def _05_unreconcile(self):
        """Undo every allocation reconciliation before the journal
        entry(-ies) are deleted.

        Runs on the transition to Cancel, with a prefix number
        smaller than ``_10_delete_accounting_entry`` so this hook
        runs first -- reconciliation must be undone before the
        journal items it points to are removed. Calls
        ``remove_move_reconcile`` on 'Customer Receivable Journal
        Item' and, when present, 'Referrer Receivable Journal Item',
        then clears 'Partial Reconcile' on every row of
        'Allocations'. Idempotent: an empty receivable line field is
        skipped, so this hook is safe to run repeatedly.
        """
        self.ensure_one()
        receivable_move_lines = (
            self.receivable_move_line_id + self.referrer_receivable_move_line_id
        )
        if receivable_move_lines:
            receivable_move_lines.remove_move_reconcile()
        self.allocation_ids.write({"partial_reconcile_id": False})

    # M. Accounting Entry Deletion (post-cancel hook)
    @ssi_decorator.post_cancel_action()
    def _10_delete_accounting_entry(self):
        """Delete the journal entry(-ies) created for this usage.

        Runs after the transition to Cancel. Returns 'Customer
        Accounting Entry' and, when present, 'Referrer Accounting
        Entry' to draft, then deletes them, clearing 'Customer
        Accounting Entry', 'Referrer Accounting Entry', and their own
        receivable journal item field. Idempotent: an accounting
        entry field already empty is skipped, so this hook is safe to
        run repeatedly.
        """
        self._delete_customer_move()
        self._delete_referrer_move()

    def _delete_customer_move(self):
        """Delete 'Customer Accounting Entry', once.

        No-op when 'Customer Accounting Entry' is already empty.

        :return: nothing
        """
        self.ensure_one()
        if not self.move_id:
            return
        move = self.move_id
        if move.state != "draft":
            move.button_draft()
        # 'posted_before' stays True after button_draft(), so plain
        # unlink() still raises "You cannot delete an entry which has
        # been posted once." -- force_delete is account.move's own
        # sanctioned bypass for that guard (see account_payment.py /
        # account_bank_statement.py core usage of the same context key).
        move.with_context(force_delete=True).unlink()
        self.write(
            {
                "move_id": False,
                "receivable_move_line_id": False,
            }
        )

    def _delete_referrer_move(self):
        """Delete 'Referrer Accounting Entry', once.

        No-op when 'Referrer Accounting Entry' is already empty.

        :return: nothing
        """
        self.ensure_one()
        if not self.referrer_move_id:
            return
        move = self.referrer_move_id
        if move.state != "draft":
            move.button_draft()
        # See the matching comment in _delete_customer_move.
        move.with_context(force_delete=True).unlink()
        self.write(
            {
                "referrer_move_id": False,
                "referrer_receivable_move_line_id": False,
            }
        )

    # J. Insert Form Element Decorator
    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch

    # K. Override _get_policy_field
    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "reject_ok",
            "done_ok",
            "cancel_ok",
            "open_ok",
            "restart_ok",
            "manual_number_ok",
            "restart_approval_ok",
        ]
        res += policy_field
        return res
