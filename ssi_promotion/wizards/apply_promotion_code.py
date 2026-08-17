# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ApplyPromotionCode(models.TransientModel):
    """
    Wizard that redeems a promotion_code against the document it was
    opened from -- any record whose own model carries
    mixin.promotion_object (open-synergy/ssi-promotion#30).

    'Side' states which of the two parties the caller document belongs
    to, and it is the only thing that changes what confirming does.

    On the voucher user's own side ('customer'), confirming creates
    one draft promotion_code_usage, with 'Reference Document' set to
    the caller document and 'Voucher User' resolved from the caller
    document's own _get_promotion_partner().

    On the referrer's own side ('referrer'), confirming creates
    nothing: it attaches the caller document to the 'Referrer
    Reference Document' of a promotion_code_usage that is already
    there and still Draft. A second usage is deliberately not created
    -- promotion_code.usage_count counts open/done usages and backs
    'Usage Limit', so one referral event spread over two usages would
    be counted twice.

    Either way 'Allocations' is then pre-filled from the documents'
    own eligible journal items via action_populate_allocation(), and
    the usage is left in Draft for review; it is neither confirmed nor
    approved.

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

    side = fields.Selection(
        string="Side",
        selection=[
            ("customer", "Voucher User"),
            ("referrer", "Referrer"),
        ],
        required=True,
        default=lambda self: self._default_side(),
        help="Which party the caller document belongs to. 'Voucher "
        "User' creates a new usage for it. 'Referrer' attaches it to "
        "the 'Referrer Reference Document' of the Draft usage that is "
        "already there, instead of creating a second one. Derived "
        "from the selected 'Promotion Code', and editable -- a "
        "referrer can also redeem somebody else's code.",
    )
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
        help="Partner who will be billed the resulting accounting "
        "entry, resolved from the caller document's own "
        "_get_promotion_partner(). Shown for review only -- not "
        "editable here.",
    )

    @api.model
    def _default_side(self):
        """Default 'Side' from whatever promotion code is known yet.

        Opening this wizard from a document's own button or Action
        menu carries no promotion code at all, so this normally lands
        on 'Voucher User' -- the derivation only becomes meaningful
        once a code is picked, which is what ``onchange_side`` is
        for. A caller that does pass one through the context
        (``default_promotion_code_id``) gets it derived right away.

        :return: ``'customer'`` or ``'referrer'``
        """
        promotion_code = self.env["promotion_code"]
        code_id = self.env.context.get("default_promotion_code_id")
        if code_id:
            promotion_code = promotion_code.browse(code_id)
        return self._derive_side(promotion_code)

    @api.model
    def _derive_side(self, promotion_code):
        """Derive 'Side' by comparing both sides' own partner.

        The caller document belongs to the referrer exactly when the
        partner it promotes is the promotion code's own referrer
        ('Partner'). Evidence, not a guess -- and deliberately not
        proof: one person can be a referrer on one code and a voucher
        user on another, which this comparison cannot tell apart, so
        'Side' stays editable.

        'Partner' is read with ``sudo()``: promotion_code carries a
        record rule restricted to ``user_id``, and deriving a default
        must never turn into an Access Error over a record the user
        merely picked from a dropdown.

        :param promotion_code: the ``promotion_code`` record being
            applied, possibly empty
        :return: ``'referrer'`` when the caller document promotes the
            promotion code's own referrer, ``'customer'`` otherwise --
            including when either side's own partner is unknown
        """
        document = self._get_document()
        if not promotion_code or not document:
            return "customer"
        if "promotion_usage_ids" not in document._fields:
            return "customer"
        referrer = promotion_code.sudo().partner_id
        if referrer and referrer == document._get_promotion_partner():
            return "referrer"
        return "customer"

    @api.onchange("promotion_code_id")
    def onchange_side(self):
        """Re-derive 'Side' from the newly selected 'Promotion Code'.

        Without this the derivation would never run on a real form:
        no code is selected yet when ``_default_side`` is evaluated,
        so 'Side' would always start out as 'Voucher User'.

        :return: nothing; assigns ``side``
        """
        self.side = self._derive_side(self.promotion_code_id)

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

    def _get_localdict(self, document):
        """Build the safe-eval context for the apply-check Python code.

        Carries exactly five names, and ``side`` is one of them on
        purpose: both sides go through this very same wizard, and only
        the voucher user's own side has a claim to check, so a
        configuration that cannot tell them apart cannot express the
        rule it was added for.

        :param document: the caller document record, already proven to
            carry ``mixin.promotion_object`` by ``_check_document``
        :return: dict passed as ``localdict`` to ``safe_eval``
        """
        self.ensure_one()
        return {
            "env": self.env,
            "document": document,
            "promotion_code": self.promotion_code_id,
            "promotion_type": self.promotion_code_id.type_id,
            "side": self.side,
        }

    def _check_apply_python_code(self, document):
        """Let the promotion type's own rule refuse this application.

        Runs ``type_id.apply_python_code`` with the localdict from
        ``_get_localdict``. The code is expected to assign a boolean to
        a ``result`` variable, and may assign a sentence to a
        ``message`` variable explaining the refusal.

        An unset ``result`` counts as ``True``, exactly like
        ``promotion_code_usage._check_validity_python_code()`` -- a
        half-written configuration must not silently block everything.
        An empty code field is not evaluated at all, which is what
        keeps every installed instance behaving as it did before this
        check existed.

        :param document: the caller document record
        :raises UserError: when the code assigns a falsy ``result``
        """
        self.ensure_one()
        code = self.promotion_code_id.type_id.apply_python_code
        if not code:
            return
        localdict = self._get_localdict(document)
        safe_eval(code, localdict, mode="exec", nocopy=True)
        if localdict.get("result", True):
            return
        problem = localdict.get("message") or (
            "Promotion code '%s' may not be applied to this document -- the "
            "Apply Check Python Code of promotion type '%s' rejected it"
            % (
                self.promotion_code_id.display_name,
                self.promotion_code_id.type_id.display_name,
            )
        )
        error_message = """
Context: Apply promotion code
Database ID: %s
Problem: %s
Solution: Satisfy the rule written in the 'Apply Check Python Code' of \
promotion type '%s', or update that configuration
""" % (
            self.id,
            problem,
            self.promotion_code_id.type_id.display_name,
        )
        raise UserError(_(error_message))

    def action_apply_promotion_code(self):
        """Apply this wizard's own promotion code to its caller
        document.

        Depending on 'Side' this either creates a draft Usage or
        attaches the caller document to one that already exists --
        see ``_apply_promotion_code``.

        :return: an ``ir.actions.act_window`` dict for the resulting
            ``promotion_code_usage``
        """
        for record in self.sudo():
            result = record._apply_promotion_code()
        return result

    def _apply_promotion_code(self):
        """Apply this wizard's own promotion code, per 'Side'.

        Runs ``_check_document`` and ``_check_allowed_model`` first --
        both sides are held to the very same 'Allowed Reference
        Models' rule -- and then ``_check_apply_python_code``, the
        instance's own rule. That one runs last of the three and
        before the branch on 'Side', so the configuration it evaluates
        reads a caller document already proven to exist and to be
        allowed, and gets to see both sides.

        Then branches on 'Side': 'Voucher User'
        creates a new usage (``_create_usage``), 'Referrer' attaches
        the caller document to one that already exists
        (``_attach_referrer_document``). Either way the resulting
        usage then fills 'Allocations' from its own documents'
        eligible journal items through
        ``action_populate_allocation``, which skips journal items it
        has already allocated -- so replaying it over an existing
        usage only ever adds that usage's referrer rows. Does not
        confirm or approve the usage; it is left in Draft for review.

        :return: an ``ir.actions.act_window`` dict opening the
            resulting ``promotion_code_usage`` form
        """
        self.ensure_one()
        self._check_document()
        document = self._get_document()
        self._check_allowed_model(document)
        self._check_apply_python_code(document)
        if self.side == "referrer":
            usage = self._attach_referrer_document(document)
        else:
            usage = self._create_usage(document)
        usage.action_populate_allocation()
        return self._open_usage(usage)

    def _create_usage(self, document):
        """Create one draft Usage for the voucher user's own side.

        :param document: the caller document record
        :return: the new ``promotion_code_usage`` record
        """
        self.ensure_one()
        return self.env["promotion_code_usage"].create(
            self._prepare_usage_data(document)
        )

    def _attach_referrer_document(self, document):
        """Attach the caller document to an existing draft Usage.

        The referrer's own side is only ever attachable while the
        usage is still Draft: both accounting entries are created by
        the ``post_open_action`` hook, and
        ``_create_referrer_move()`` stays silent when no allocation
        row carries 'Source' 'Referrer' at the moment the usage is
        opened. Once opened, 'Referrer Accounting Entry' can no
        longer be filled at all without cancelling the document, so
        an opened usage is not a candidate here.

        :param document: the caller document record
        :raises UserError: when no Draft usage of this promotion code
            is still waiting for a referrer reference document, or
            when more than one is -- guessing which one is meant is
            not allowed
        :return: the ``promotion_code_usage`` record just attached to
        """
        self.ensure_one()
        candidates = self._get_referrer_usage_candidates()
        if not candidates:
            error_message = """
Context: Apply promotion code
Database ID: %s
Problem: No Draft usage of promotion code '%s' is waiting for a referrer \
reference document
Solution: Apply this promotion code to the voucher user's own document \
first, and leave the resulting usage in 'Draft' -- the referrer's own side \
can only be attached before the usage is opened
""" % (
                self.id,
                self.promotion_code_id.display_name,
            )
            raise UserError(_(error_message))
        if len(candidates) > 1:
            error_message = """
Context: Apply promotion code
Database ID: %s
Problem: %s Draft usages of promotion code '%s' are waiting for a referrer \
reference document: %s
Solution: Open the usage this document belongs to and fill in its own \
'Referrer Reference Document' there -- this wizard does not guess which one \
is meant
""" % (
                self.id,
                len(candidates),
                self.promotion_code_id.display_name,
                self._get_candidate_labels(candidates),
            )
            raise UserError(_(error_message))
        candidates.write(
            {
                "referrer_document_reference": "{},{}".format(
                    document._name, document.id
                ),
            }
        )
        return candidates

    def _get_referrer_usage_candidates(self):
        """Find the draft Usages the referrer's own side could join.

        'Referrer Reference Document' is filtered in Python rather
        than in the domain on purpose: it is a ``fields.Reference``,
        an empty one reads back as ``None`` rather than ``False``, so
        plain truthiness is the one test that holds for both. The
        two criteria that do go into the domain -- 'Promotion Code'
        and 'Status' -- are columns of ``promotion_code_usage``
        itself, which keeps that model's own record rule the only one
        the search has to answer to.

        :return: ``promotion_code_usage`` records of this wizard's
            own 'Promotion Code' that are still Draft and whose own
            'Referrer Reference Document' is empty
        """
        self.ensure_one()
        usages = self.env["promotion_code_usage"].search(
            [
                ("promotion_code_id", "=", self.promotion_code_id.id),
                ("state", "=", "draft"),
            ]
        )
        return usages.filtered(lambda usage: not usage.referrer_document_reference)

    def _get_candidate_labels(self, candidates):
        """Render candidate Usages for the ambiguity error message.

        Each one is named by its own document number *and* database
        id: a Draft usage has not been through its own sequence yet,
        so every candidate would otherwise be printed as '/'.

        :param candidates: ``promotion_code_usage`` records to name
        :return: a comma-separated string naming every candidate
        """
        self.ensure_one()
        return ", ".join(
            "%s (ID %s)" % (usage.display_name, usage.id) for usage in candidates
        )

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
