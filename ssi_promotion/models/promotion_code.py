# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class PromotionCode(models.Model):
    """
    A single voucher/referral code issued from a promotion_type.

    Becomes usable (state "open") after the approval workflow completes.
    The optional partner_id (inherited from mixin.transaction_partner)
    identifies the referrer this code was issued for; when set, approving
    a usage of this code also creates a credit note for that referrer
    (see promotion_code_usage).
    """

    _name = "promotion_code"
    _description = "Promotion Code"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_confirm",
        "mixin.transaction_partner",
        "mixin.transaction_date_duration",
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
    voucher_code = fields.Char(
        string="Voucher Code",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Code the customer redeems to use this promotion. Must be "
        "unique across all promotion codes.",
    )
    type_id = fields.Many2one(
        string="Promotion Type",
        comodel_name="promotion_type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Promotion type that determines the discount rule, usage "
        "limit, validity, allowed reference documents, and credit note "
        "accounting for this code.",
    )
    partner_id = fields.Many2one(
        string="Referrer",
        required=False,
        help="Partner this promotion code was issued for as a referrer. "
        "When set, approving a usage of this code also creates a credit "
        "note for this partner in addition to the voucher user's credit "
        "note.",
    )
    date_start = fields.Date(
        required=False,
        default=lambda self: date.today(),
        help="Date this promotion code becomes valid. Required only when "
        "'Promotion Type' has a validity period.",
    )
    date_end = fields.Date(
        required=False,
        help="Date this promotion code expires. Computed from 'Date Start' "
        "and the promotion type's validity duration; required only when "
        "'Promotion Type' has a validity period.",
    )
    discount_type = fields.Selection(
        string="Discount Type",
        related="type_id.discount_type",
        store=True,
        compute_sudo=True,
        help="Discount computation mode copied from 'Promotion Type'.",
    )
    discount_amount = fields.Float(
        string="Discount Amount",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Flat discount amount granted per usage. Defaulted from "
        "'Promotion Type' and may be overridden while in draft.",
    )
    discount_percentage = fields.Float(
        string="Discount Percentage (%)",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Percentage discount granted per usage. Defaulted from "
        "'Promotion Type' and may be overridden while in draft.",
    )
    usage_limit = fields.Integer(
        string="Usage Limit",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Maximum number of times this code may be used (state open "
        "or done). Defaulted from 'Promotion Type'; 0 means unlimited.",
    )
    usage_ids = fields.One2many(
        string="Usages",
        comodel_name="promotion_code_usage",
        inverse_name="promotion_code_id",
        help="Usage records created against this promotion code.",
    )
    usage_count = fields.Integer(
        string="Usage Count",
        compute="_compute_usage_count",
        store=True,
        compute_sudo=True,
        help="Number of usages of this code currently in state open or "
        "done, counted against 'Usage Limit'.",
    )

    # G. Compute Methods
    @api.depends(
        "usage_ids",
        "usage_ids.state",
    )
    def _compute_usage_count(self):
        for record in self:
            record.usage_count = len(
                record.usage_ids.filtered(lambda usage: usage.state in ("open", "done"))
            )

    # H. Onchange Methods
    @api.onchange(
        "type_id",
    )
    def onchange_discount_type(self):
        self.discount_type = self.type_id.discount_type

    @api.onchange(
        "type_id",
    )
    def onchange_discount_amount(self):
        self.discount_amount = self.type_id.discount_amount

    @api.onchange(
        "type_id",
    )
    def onchange_discount_percentage(self):
        self.discount_percentage = self.type_id.discount_percentage

    @api.onchange(
        "type_id",
    )
    def onchange_usage_limit(self):
        self.usage_limit = self.type_id.usage_limit

    @api.onchange(
        "type_id",
        "date_start",
    )
    def onchange_date_end(self):
        self.date_end = False
        if self.type_id.has_validity and self.date_start:
            self.date_end = self.date_start + timedelta(
                days=self.type_id.validity_duration
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
