# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PromotionCodeUsageAllocation(models.Model):
    """
    Represents one receivable journal item (``account.move.line``) a
    ``promotion_code_usage`` wants reduced by one of its own journal
    entries.

    'Source' selects which of the usage's own two journal entries is
    consumed against 'Journal Item': the voucher user's own
    ('customer') or the promotion code's referrer own ('referrer').
    Opening the usage runs its own '_30_reconcile' hook, which
    reconciles each row's own journal entry receivable line against
    'Journal Item' in '_order' (grouped by 'Source'), stores the
    first ``account.partial.reconcile`` created on 'Partial
    Reconcile', and stops consuming a given journal entry once that
    journal entry's own residual reaches zero -- rows reached
    afterwards keep an empty 'Partial Reconcile' and a zero
    'Amount Reconciled'. Cancelling the usage undoes every
    reconciliation created this way and clears 'Partial Reconcile'
    again (see the usage's own '_05_unreconcile' hook).
    """

    _name = "promotion_code_usage_allocation"
    _inherit = [
        "mixin.many2one_configurator",
    ]
    _description = "Promotion Code Usage - Allocation"
    _order = "usage_id, sequence, id"

    usage_id = fields.Many2one(
        string="# Usage",
        comodel_name="promotion_code_usage",
        required=True,
        ondelete="cascade",
        help="Promotion code usage this allocation row belongs to.",
    )
    sequence = fields.Integer(
        string="Sequence",
        required=True,
        default=5,
        help="Order this row's own 'Journal Item' is consumed in, "
        "among the rows sharing the same 'Source', when the usage "
        "opens.",
    )
    source = fields.Selection(
        string="Source",
        selection=[
            ("customer", "Voucher User"),
            ("referrer", "Referrer"),
        ],
        default="customer",
        required=True,
        help="Which of the usage's own two journal entries is "
        "reconciled against 'Journal Item': the voucher user's own "
        "('Voucher User'), or the promotion code's referrer own "
        "('Referrer').",
    )
    move_line_id = fields.Many2one(
        string="Journal Item",
        comodel_name="account.move.line",
        required=True,
        ondelete="restrict",
        domain=[
            ("account_id.reconcile", "=", True),
            ("parent_state", "=", "posted"),
            ("reconciled", "=", False),
            ("amount_residual", ">", 0),
        ],
        help="Receivable journal item to reduce with this usage's "
        "own journal entry. Only posted, reconcilable, not yet fully "
        "reconciled journal items with a positive residual amount "
        "are selectable.",
    )
    move_id = fields.Many2one(
        string="Journal Entry",
        comodel_name="account.move",
        related="move_line_id.move_id",
        help="Journal entry 'Journal Item' belongs to.",
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
        related="move_line_id.account_id",
        help="Account of 'Journal Item'.",
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        related="move_line_id.partner_id",
        help="Partner of 'Journal Item'.",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="move_line_id.currency_id",
        store=True,
        help="Currency of 'Journal Item', empty when it is posted "
        "in the company currency. Allocations of a "
        "foreign-currency 'Journal Item' are rejected when the "
        "usage opens.",
    )
    company_currency_id = fields.Many2one(
        string="Company Currency",
        comodel_name="res.currency",
        related="move_line_id.company_currency_id",
        store=True,
        help="Company currency of 'Journal Item', also the "
        "currency 'Amount Residual' and 'Amount Reconciled' are "
        "expressed in.",
    )
    amount_residual = fields.Monetary(
        string="Amount Residual",
        currency_field="company_currency_id",
        related="move_line_id.amount_residual",
        help="Residual amount still due on 'Journal Item', before "
        "this usage's own reconciliation runs.",
    )
    partial_reconcile_id = fields.Many2one(
        string="Partial Reconcile",
        comodel_name="account.partial.reconcile",
        readonly=True,
        copy=False,
        help="First ``account.partial.reconcile`` created by the "
        "usage's own '_30_reconcile' hook when this row's own "
        "'Journal Item' was reconciled against the journal entry. "
        "Empty while the usage has not opened yet, or when the "
        "journal entry ran out of residual before reaching this "
        "row.",
    )
    amount_reconciled = fields.Monetary(
        string="Amount Reconciled",
        currency_field="company_currency_id",
        compute="_compute_amount_reconciled",
        store=True,
        compute_sudo=True,
        help="Amount actually reconciled against 'Journal Item': "
        "'Partial Reconcile''s own 'Amount', or zero while empty.",
    )
    allowed_account_ids = fields.Many2many(
        string="Allowed Accounts",
        comodel_name="account.account",
        compute="_compute_allowed_account_ids",
        store=False,
        compute_sudo=True,
        help="Accounts 'Journal Item' is allowed to sit on, resolved "
        "from '# Usage''s own promotion type through its 'Allocation "
        "Account Selection Method'. Used only to filter 'Journal "
        "Item' on this row's own form/tree view -- never displayed.",
    )

    @api.depends("partial_reconcile_id.amount")
    def _compute_amount_reconciled(self):
        """Compute the amount actually reconciled by this row.

        :return: nothing; assigns ``amount_reconciled``
        """
        for record in self:
            result = 0.0
            if record.partial_reconcile_id:
                result = record.partial_reconcile_id.amount
            record.amount_reconciled = result

    @api.depends("usage_id.type_id")
    def _compute_allowed_account_ids(self):
        """Resolve the accounts allowed by this row's own promotion type.

        Delegates to the m2o configurator on '# Usage''s own 'Type'
        (see ``mixin.many2one_configurator``). While 'Type' is empty
        (mis. a row created before its usage has one), falls back to
        every reconcilable account rather than ``search([])`` or an
        empty result -- 'reconcile' is a hard technical boundary that
        holds regardless of type configuration, unlike the "no
        restriction" default documented for other m2o configurators.

        :return: nothing; assigns ``allowed_account_ids``
        """
        Account = self.env["account.account"]  # pylint: disable=invalid-name
        for record in self:
            result = Account.search([("reconcile", "=", True)])
            if record.usage_id.type_id:
                type_id = record.usage_id.type_id
                result = record._m2o_configurator_get_filter(
                    object_name="account.account",
                    method_selection=(type_id.allocation_account_selection_method),
                    manual_recordset=type_id.allocation_account_ids,
                    domain=type_id.allocation_account_domain,
                    python_code=type_id.allocation_account_python_code,
                )
            record.allowed_account_ids = result

    @api.constrains(
        "usage_id",
        "move_line_id",
        "source",
    )
    def _check_move_line_unique(self):
        """Reject a 'Journal Item' allocated twice under one 'Source'.

        :raises ValidationError: when another row of the same
            '# Usage' and 'Source' already targets the same
            'Journal Item'
        """
        for record in self:
            if not record._check_move_line_unique_condition():
                error_message = """
Context: Set journal item on promotion code usage allocation
Database ID: %s
Problem: Journal item '%s' is already allocated under Source '%s' \
for this usage
Solution: Choose a different journal item, or remove the duplicate \
allocation row
""" % (
                    record.id,
                    record.move_line_id.display_name,
                    record.source,
                )
                raise ValidationError(_(error_message))

    def _check_move_line_unique_condition(self):
        """Check no sibling row duplicates this row's own key.

        :return: ``True`` when no other row of the same '# Usage'
            and 'Source' targets the same 'Journal Item'
        """
        self.ensure_one()
        domain = [
            ("id", "!=", self.id),
            ("usage_id", "=", self.usage_id.id),
            ("source", "=", self.source),
            ("move_line_id", "=", self.move_line_id.id),
        ]
        return self.search_count(domain) == 0

    @api.constrains(
        "usage_id",
        "move_line_id",
    )
    def _check_move_line_promotion_object(self):
        """Require 'Journal Item' to be an eligible line of the
        reference document, when that document carries
        ``mixin.promotion_object``.

        Reference documents that do not carry the mixin are left
        unconstrained by this rule, preserving the pre-existing
        behaviour of open-synergy/ssi-promotion#29.

        :raises ValidationError: via
            ``_check_move_line_promotion_object_condition`` when
            'Journal Item' is not part of the reference document's
            own ``_get_promotion_move_lines()``
        """
        for record in self:
            if not record._check_move_line_promotion_object_condition():
                error_message = """
Context: Set journal item on promotion code usage allocation
Database ID: %s
Problem: Journal item '%s' is not an eligible journal item of \
reference document '%s'
Solution: Choose a journal item returned by the reference \
document's own '_get_promotion_move_lines' (reconcilable account, \
posted move, positive residual)
""" % (
                    record.id,
                    record.move_line_id.display_name,
                    record.usage_id.document_reference.display_name,
                )
                raise ValidationError(_(error_message))

    def _check_move_line_promotion_object_condition(self):
        """Check 'Journal Item' passes the reference document's own
        promotion object contract.

        :return: ``True`` when '# Usage''s own 'Reference Document'
            is empty, its model does not carry
            ``mixin.promotion_object``, or 'Journal Item' is part of
            its own ``_get_promotion_move_lines()``
        """
        self.ensure_one()
        reference = self.usage_id.document_reference
        if not reference:
            return True
        if "promotion_usage_ids" not in reference._fields:
            return True
        return self.move_line_id in reference._get_promotion_move_lines()

    def _reconcile(self, receivable_move_line):
        """Reconcile this row's own 'Journal Item' against a journal
        entry receivable line.

        No-op when 'Partial Reconcile' is already set. Combines
        'Journal Item' with ``receivable_move_line`` and calls
        ``account.move.line.reconcile()``, then stores the first
        ``account.partial.reconcile`` it created on 'Partial
        Reconcile'.

        :param receivable_move_line: the journal entry's own
            receivable ``account.move.line`` to reconcile 'Journal
            Item' against
        :return: nothing
        """
        self.ensure_one()
        if self.partial_reconcile_id:
            return
        result = (self.move_line_id + receivable_move_line).reconcile()
        partials = result.get("partials")
        if partials:
            self.partial_reconcile_id = partials[:1]
