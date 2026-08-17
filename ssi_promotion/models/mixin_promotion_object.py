# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class MixinPromotionObject(models.AbstractModel):
    """Let a document model be tracked and self-serve its promotions.

    Inheriting a model into this mixin and setting its two
    configurator attributes below makes 'Promotion Code Usages' /
    'Num. of Promotion Code Usages' available on it (found by
    matching either ``promotion_code_usage.document_reference`` or
    ``promotion_code_usage.referrer_document_reference`` back to
    this record), and its own eligible receivable journal items
    reachable via ``_get_promotion_move_lines`` -- the same
    recordset ``promotion_code_usage.action_populate_allocation``
    reads to fill 'Allocations' automatically.

    ``_promotion_move_line_field_name`` names the field (on the
    inheriting model) holding the journal item(s) to be reconciled;
    it is read with ``mapped()`` rather than ``getattr`` -- unlike
    the ``_*_field_name`` idiom of ``ssi_accounting_entry_mixin`` --
    because the target may sit more than one hop away (e.g. a
    school payment term storing it at
    ``customer_invoice_id.receivable_move_line_id``), and only
    ``mapped()`` can walk a dotted path. ``False`` (the default)
    means the inheriting model has not wired a target yet, so
    ``_get_promotion_move_lines`` returns an empty recordset.

    ``_promotion_partner_id_field_name`` names the field holding the
    partner promoted as 'Voucher User', defaulting to ``partner_id``.

    Both attributes are the standard path; ``_get_promotion_move_lines``
    and ``_get_promotion_partner`` remain override-able escape hatches
    for a target that cannot be expressed as a field path at all.
    """

    _name = "mixin.promotion_object"
    _description = "Promotion Object Mixin"

    _promotion_move_line_field_name = False
    _promotion_partner_id_field_name = "partner_id"

    promotion_usage_ids = fields.Many2many(
        string="Promotion Code Usages",
        comodel_name="promotion_code_usage",
        compute="_compute_promotion_usage_ids",
        store=False,
        compute_sudo=True,
        help="promotion_code_usage records whose own 'Reference "
        "Document' or 'Referrer Reference Document' points back to "
        "this record.",
    )
    promotion_usage_count = fields.Integer(
        string="Num. of Promotion Code Usages",
        compute="_compute_promotion_usage_ids",
        store=False,
        compute_sudo=True,
        help="Number of records in 'Promotion Code Usages'.",
    )

    def _get_promotion_usage_ids_criteria(self):
        """Build the domain matching this record's own usages.

        Both ``document_reference`` and
        ``referrer_document_reference`` are matched, so a record
        named as the referrer's own document reports the usage
        touching it just as the voucher user's own document does.
        Both are ``fields.Reference``, stored as text
        (``"<model>,<id>"``), so each can be searched with a plain
        ``=`` against the same text built from this record.

        :return: a search domain for ``promotion_code_usage``
        """
        self.ensure_one()
        reference = "{},{}".format(self._name, self.id)
        return [
            "|",
            ("document_reference", "=", reference),
            ("referrer_document_reference", "=", reference),
        ]

    def _compute_promotion_usage_ids(self):
        """Look up promotion_code_usage records referencing this
        record.

        No ``@api.depends`` is declared: the search key
        (``document_reference``) lives on ``promotion_code_usage``,
        not on this record, so this compute has no dependency on
        any field of ``self`` at all (10-compute.md, exception 2).

        :return: nothing; assigns ``promotion_usage_ids`` and
            ``promotion_usage_count``
        """
        Usage = self.env["promotion_code_usage"]  # pylint: disable=invalid-name
        for record in self:
            result_usages = Usage
            if record.id:
                criteria = record._get_promotion_usage_ids_criteria()
                result_usages = Usage.search(criteria)
            record.promotion_usage_ids = result_usages
            record.promotion_usage_count = len(result_usages)

    def action_open_promotion_usage(self):
        """Open 'Promotion Code Usages' referencing this record.

        Pure navigation to a smart button target -- no dedicated
        Instruksi Kerja is written for it.

        :return: an ``ir.actions.act_window`` dict for
            ``promotion_code_usage``, filtered to this record's own
            'Promotion Code Usages'
        """
        self.ensure_one()
        return {
            "name": _("Promotion Code Usages"),
            "type": "ir.actions.act_window",
            "res_model": "promotion_code_usage",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.promotion_usage_ids.ids)],
        }

    def _get_promotion_move_lines(self):
        """Resolve this record's own journal items open to promotion.

        Reads ``_promotion_move_line_field_name`` with ``mapped()``
        -- see the class docstring for why. Extension point:
        override when the target cannot be expressed as a field
        path at all.

        :return: ``account.move.line`` recordset, filtered to lines
            whose 'Account' allows reconciliation, whose own move is
            'Posted', and whose 'Residual Amount' is positive; empty
            when ``_promotion_move_line_field_name`` is ``False``
        """
        if not self._promotion_move_line_field_name:
            return self.env["account.move.line"]
        move_lines = self.mapped(self._promotion_move_line_field_name)
        return move_lines.filtered(
            lambda line: line.account_id.reconcile
            and line.parent_state == "posted"
            and line.amount_residual > 0
        )

    def _get_promotion_partner(self):
        """Resolve the partner promoted as this record's Voucher User.

        Reads ``_promotion_partner_id_field_name`` with ``getattr``,
        following the standard ``_*_field_name`` idiom of
        ``ssi_accounting_entry_mixin``. Extension point: override
        when the partner cannot be expressed as a field name at all.

        :return: a ``res.partner`` record, possibly empty
        """
        self.ensure_one()
        return getattr(self, self._promotion_partner_id_field_name)

    def action_apply_promotion_code(self):
        """Open the Apply Promotion Code wizard for this record.

        Wired to a button on the form of each ``mixin.promotion_object``
        implementer -- the mixin itself installs no button (see
        ``apply_promotion_code_action``'s own ``binding_model_id`` for
        the Action-menu alternative that needs no button at all).
        Passes this record's own model/id through context so the
        wizard (``apply_promotion_code``) can read it back with
        ``env.context['active_model']``/``['active_id']``.

        :return: an ``ir.actions.act_window`` dict opening the wizard
        """
        self.ensure_one()
        return {
            "name": _("Apply Promotion Code"),
            "type": "ir.actions.act_window",
            "res_model": "apply_promotion_code",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
            },
        }
