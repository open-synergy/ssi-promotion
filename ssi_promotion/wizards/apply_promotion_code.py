# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ApplyPromotionCode(models.TransientModel):
    """
    Wizard that redeems a promotion_code against the document it was
    opened from -- any record whose own model carries
    mixin.promotion_object (open-synergy/ssi-promotion#30). Confirming
    it creates one draft promotion_code_usage, with 'Reference
    Document' set to the caller document, 'Voucher User' resolved
    from the caller document's own _get_promotion_partner(), and
    'Allocations' pre-filled from the caller document's own eligible
    journal items via action_populate_allocation() -- but leaves the
    new usage in Draft for review; it does not confirm or approve it.

    Reads the caller document from context active_model/active_id,
    exactly like the standard SSI cancel-reason wizard
    (base.select_cancel_reason). It is opened either by a button a
    mixin.promotion_object implementer wires on its own form (calling
    mixin.promotion_object.action_apply_promotion_code()), or directly
    from that document's own Action (gear) menu -- see
    apply_promotion_code_action's own binding_model_id.
    """

    _name = "apply_promotion_code"
    _description = "Apply Promotion Code"

    promotion_code_id = fields.Many2one(
        string="Promotion Code",
        comodel_name="promotion_code",
        domain=[("state", "=", "open")],
        required=True,
        help="Promotion code to redeem against the caller document. "
        "Only codes in state 'Open' can be selected.",
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=lambda self: date.today(),
        help="Date the promotion code is used. Copied to the new "
        "usage's own 'Usage Date'.",
    )
    partner_id = fields.Many2one(
        string="Voucher User",
        comodel_name="res.partner",
        readonly=True,
        default=lambda self: self._default_partner_id(),
        help="Partner who will be billed the resulting credit note, "
        "resolved from the caller document's own "
        "_get_promotion_partner(). Shown for review only -- not "
        "editable here.",
    )

    @api.model
    def _default_partner_id(self):
        """Default Voucher User from the caller document's own partner.

        Silently returns empty when the caller document does not
        carry ``mixin.promotion_object`` yet -- confirming the wizard
        is where that is rejected with a proper error (see
        ``_check_document``), not opening it.

        :return: a ``res.partner`` id, or ``False``
        """
        document = self._get_document()
        if document and "promotion_usage_ids" in document._fields:
            return document._get_promotion_partner().id
        return False

    def _get_document(self):
        """Resolve the caller document referenced by this wizard.

        Reads ``active_model``/``active_id`` from context, exactly as
        set by the button or Action-menu binding that opened this
        wizard.

        :return: the caller document record, or ``False`` when
            ``active_model``/``active_id`` are missing from context,
            or ``active_model`` is not a registered model
        """
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        if not active_model or not active_id or active_model not in self.env:
            return False
        return self.env[active_model].browse(active_id)

    def _check_document(self):
        """Require this wizard's own caller document to carry the mixin.

        :raises UserError: when ``active_model``/``active_id`` are
            missing from context, or ``active_model`` does not carry
            ``mixin.promotion_object`` (detected by the presence of
            its own ``promotion_usage_ids`` field)
        """
        self.ensure_one()
        document = self._get_document()
        if not document or "promotion_usage_ids" not in document._fields:
            error_message = """
Context: Apply promotion code
Database ID: %s
Problem: The document this wizard was opened from does not support \
promotion codes (its own model does not carry mixin.promotion_object)
Solution: Open this wizard from a document whose own model inherits \
mixin.promotion_object
""" % (
                self.id,
            )
            raise UserError(_(error_message))

    def _check_allowed_model(self, document):
        """Require the promotion type to allow the document's own model.

        :param document: the caller document record
        :raises UserError: when the promotion type of the selected
            'Promotion Code' does not allow the document's own model
        """
        self.ensure_one()
        allowed_models = self.promotion_code_id.type_id.allowed_model_ids.mapped(
            "model"
        )
        if document._name not in allowed_models:
            error_message = """
Context: Apply promotion code
Database ID: %s
Problem: The promotion type of promotion code '%s' does not allow \
reference document model '%s'
Solution: Choose a promotion code whose own promotion type's Allowed \
Reference Models includes '%s', or update that configuration
""" % (
                self.id,
                self.promotion_code_id.display_name,
                document._name,
                document._name,
            )
            raise UserError(_(error_message))

    def action_apply_promotion_code(self):
        """Create a draft Usage for this wizard's own caller document.

        :return: an ``ir.actions.act_window`` dict for the new
            ``promotion_code_usage``
        """
        for record in self.sudo():
            result = record._apply_promotion_code()
        return result

    def _apply_promotion_code(self):
        """Create and populate one draft Usage from this wizard.

        Runs ``_check_document`` and ``_check_allowed_model`` first,
        creates the ``promotion_code_usage``, then delegates to its
        own ``action_populate_allocation`` to fill 'Allocations' from
        the caller document's own eligible journal items. Does not
        confirm or approve the new usage -- it is left in Draft for
        review.

        :return: an ``ir.actions.act_window`` dict opening the new
            ``promotion_code_usage`` form
        """
        self.ensure_one()
        self._check_document()
        document = self._get_document()
        self._check_allowed_model(document)
        usage = self.env["promotion_code_usage"].create(
            self._prepare_usage_data(document)
        )
        usage.action_populate_allocation()
        return self._open_usage(usage)

    def _prepare_usage_data(self, document):
        """Build the new Usage's own create values.

        :param document: the caller document record
        :return: dict of ``promotion_code_usage`` values
        """
        self.ensure_one()
        return {
            "promotion_code_id": self.promotion_code_id.id,
            "date": self.date,
            "document_reference": "{},{}".format(document._name, document.id),
            "partner_id": document._get_promotion_partner().id,
        }

    def _open_usage(self, usage):
        """Build the window action opening the new Usage's own form.

        :param usage: the newly created ``promotion_code_usage``
            record
        :return: an ``ir.actions.act_window`` dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "promotion_code_usage",
            "res_id": usage.id,
            "view_mode": "form",
        }
