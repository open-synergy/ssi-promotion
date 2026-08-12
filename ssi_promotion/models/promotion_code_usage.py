# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class PromotionCodeUsage(models.Model):
    """
    Records one redemption of a promotion_code against an arbitrary Odoo
    document (sale order, invoice, etc. — depending on what the promotion
    type allows).

    Confirming a usage runs the promotion type's validity Python code
    together with the usage-limit and validity-period checks. Approving a
    usage (state open) automatically creates a customer credit note for
    partner_id, and a referrer credit note for promotion_code_id.partner_id
    when the code has a referrer (see the post_open_action hook).

    Recognition Method controls which account those credit note lines
    debit: Immediate (the default, copied from the promotion type)
    debits the Final Account right away; Deferred debits Deferred
    Account instead, so the discount can be recognized later by a
    separate document (out of scope for this module so far).
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
        "customer credit note when this usage is approved.",
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
    credit_note_id = fields.Many2one(
        string="Customer Credit Note",
        comodel_name="account.move",
        readonly=True,
        copy=False,
        help="Credit note automatically created for 'Voucher User' when "
        "this usage is approved.",
    )
    referrer_credit_note_id = fields.Many2one(
        string="Referrer Credit Note",
        comodel_name="account.move",
        readonly=True,
        copy=False,
        help="Credit note automatically created for the promotion code's "
        "referrer (promotion_code_id.partner_id) when this usage is "
        "approved, if the promotion code has a referrer.",
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
        "usage is in Draft. Deferred routes the credit note line(s) "
        "created on approval to 'Deferred Account' instead of their "
        "Final Account.",
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
        help="Account debited on the credit note line(s) created for "
        "this usage instead of their Final Account, while this "
        "usage's own 'Recognition Method' is Deferred. Defaulted from "
        "the promotion type's own 'Deferred Account'. Required while "
        "'Recognition Method' is Deferred.",
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
        for record in self:
            record.discount_amount = record._get_discount_amount()

    def _get_discount_amount(self):
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
        self.ensure_one()
        if not self.document_reference:
            return 0.0
        if "amount_total" in self.document_reference._fields:
            return self.document_reference.amount_total
        return 0.0

    def _evaluate_discount_python_code(self):
        self.ensure_one()
        localdict = self._get_localdict()
        code = self.promotion_code_id.type_id.discount_python_code
        safe_eval(code, localdict, mode="exec", nocopy=True)
        return localdict.get("result", 0.0)

    def _get_localdict(self):
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

    # G2. Onchange Methods
    @api.onchange("type_id")
    def onchange_deferred_account_id(self):
        self.deferred_account_id = False
        if self.type_id:
            self.deferred_account_id = self.type_id.deferred_account_id

    # H. Constrains
    @api.constrains(
        "document_reference",
        "promotion_code_id",
    )
    def _check_document_reference_model(self):
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
        self.ensure_one()
        return (
            self._check_validity_usage_limit()
            and self._check_validity_period()
            and self._check_validity_python_code()
        )

    def _check_validity_usage_limit(self):
        self.ensure_one()
        limit = self.promotion_code_id.usage_limit
        if limit <= 0:
            return True
        return self.promotion_code_id.usage_count < limit

    def _check_validity_period(self):
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
        self.ensure_one()
        code = self.type_id.validity_python_code
        if not code:
            return True
        localdict = self._get_localdict()
        safe_eval(code, localdict, mode="exec", nocopy=True)
        return bool(localdict.get("result", True))

    @ssi_decorator.pre_confirm_check()
    def _10_check_validity(self):
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

    # L. Credit Note Creation (post-open hook)
    @ssi_decorator.post_open_action()
    def _10_create_credit_note(self):
        self._create_customer_credit_note()
        self._create_referrer_credit_note()

    def _create_customer_credit_note(self):
        self.ensure_one()
        if self.credit_note_id:
            return
        self._check_credit_note_configuration(referrer=False)
        move = self.env["account.move"].create(
            self._prepare_customer_credit_note_data()
        )
        self.write({"credit_note_id": move.id})

    def _create_referrer_credit_note(self):
        self.ensure_one()
        if self.referrer_credit_note_id:
            return
        if not self.promotion_code_id.partner_id:
            return
        self._check_credit_note_configuration(referrer=True)
        move = self.env["account.move"].create(
            self._prepare_referrer_credit_note_data()
        )
        self.write({"referrer_credit_note_id": move.id})

    def _check_credit_note_configuration(self, referrer=False):
        self.ensure_one()
        promotion_type = self.type_id
        journal = (
            promotion_type.referrer_journal_id or promotion_type.journal_id
            if referrer
            else promotion_type.journal_id
        )
        product = (
            promotion_type.referrer_product_id or promotion_type.product_id
            if referrer
            else promotion_type.product_id
        )
        if not journal or not product:
            error_message = """
Context: Create credit note from promotion code usage
Database ID: %s
Problem: Promotion type '%s' does not have a complete credit note \
configuration (journal and/or product)
Solution: Set 'Credit Note Journal' and 'Credit Note Product' (and the \
referrer equivalents if applicable) on the promotion type
""" % (
                self.id,
                promotion_type.display_name,
            )
            raise UserError(_(error_message))

    def _get_final_account(self, referrer=False):
        """Resolve the non-deferred account for a credit note line.

        Extension point: override to change how the customer or
        referrer credit note line's own Final Account is resolved,
        independently of 'Recognition Method'.

        :param referrer: resolve the referrer's Final Account instead
            of the voucher user's
        :return: an ``account.account`` record, possibly empty
        """
        self.ensure_one()
        promotion_type = self.type_id
        if referrer:
            product = promotion_type.referrer_product_id or promotion_type.product_id
            return product.property_account_income_id
        return (
            promotion_type.account_id
            or promotion_type.product_id.property_account_income_id
        )

    def _get_credit_note_account(self, referrer=False):
        """Resolve the account a credit note line of this usage debits.

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

    def _prepare_customer_credit_note_data(self):
        """Build the customer credit note ``account.move`` values.

        The single line debits
        ``_get_credit_note_account(referrer=False)``.

        :return: dict of ``account.move`` values
        """
        self.ensure_one()
        promotion_type = self.type_id
        return {
            "move_type": "out_refund",
            "partner_id": self.partner_id.id,
            "invoice_date": self.date,
            "journal_id": promotion_type.journal_id.id,
            "invoice_origin": self.name,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    self._prepare_credit_note_line_data(
                        promotion_type.product_id,
                        self._get_credit_note_account(referrer=False),
                    ),
                )
            ],
        }

    def _prepare_referrer_credit_note_data(self):
        """Build the referrer credit note ``account.move`` values.

        The single line debits
        ``_get_credit_note_account(referrer=True)``.

        :return: dict of ``account.move`` values
        """
        self.ensure_one()
        promotion_type = self.type_id
        product = promotion_type.referrer_product_id or promotion_type.product_id
        journal = promotion_type.referrer_journal_id or promotion_type.journal_id
        return {
            "move_type": "out_refund",
            "partner_id": self.promotion_code_id.partner_id.id,
            "invoice_date": self.date,
            "journal_id": journal.id,
            "invoice_origin": self.name,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    self._prepare_credit_note_line_data(
                        product, self._get_credit_note_account(referrer=True)
                    ),
                )
            ],
        }

    def _prepare_credit_note_line_data(self, product, account):
        self.ensure_one()
        account_id = account.id if account else product.property_account_income_id.id
        return {
            "product_id": product.id,
            "quantity": 1,
            "price_unit": self.discount_amount,
            "name": product.name,
            "account_id": account_id,
        }

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
