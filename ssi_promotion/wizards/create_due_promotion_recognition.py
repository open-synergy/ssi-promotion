# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreateDuePromotionRecognition(models.TransientModel):
    """
    Wizard that releases every due, deferred promotion_code_usage --
    ``recognition_state`` ``pending`` and *either* side's own due date
    (``recognition_date`` or ``referrer_recognition_date``) on or
    before the selected Date -- into one draft
    ``promotion_code_usage_recognition`` document each, for the
    usage's own full ``amount_deferred``.

    Both dates are looked at because each side of a usage carries its
    own one: a referral reward may fall due long before or after the
    voucher user's own discount, and a usage due only because of its
    'Referrer Recognition Date' is due all the same -- as long as the
    referrer side really is deferred on its own (see
    ``_get_due_usage_ids``).
    """

    _name = "create_due_promotion_recognition"
    _description = "Create Due Promotion Recognition"

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
        help="Recognition documents are created for every usage whose "
        "own Recognition Date -- or whose own Referrer Recognition "
        "Date -- falls on or before this date, and this is also the "
        "Date of every document created.",
    )
    usage_ids = fields.Many2many(
        string="Usages",
        comodel_name="promotion_code_usage",
        relation="rel_create_due_promotion_recognition_usage",
        column1="wizard_id",
        column2="usage_id",
        readonly=True,
        help="Deferred usages due for recognition as of Date, "
        "computed automatically.",
    )

    @api.model
    def default_get(self, fields_list):
        """Prefill Usages from today's due, deferred usages.

        :param fields_list: field names requested by the client
        :return: dict of default values
        """
        res = super().default_get(fields_list)
        res["usage_ids"] = [(6, 0, self._get_due_usage_ids(fields.Date.today()))]
        return res

    @api.onchange("date")
    def onchange_usage_ids(self):
        """Refresh Usages whenever Date changes.

        :return: nothing
        """
        self.usage_ids = [(6, 0, self._get_due_usage_ids(self.date))]

    def _get_due_usage_ids(self, date):
        """Search deferred usages due for recognition as of date.

        A usage qualifies when *either* side's own due date --
        'Recognition Date' or 'Referrer Recognition Date' -- falls on
        or before date. Matching on 'Recognition Date' alone would
        leave behind every usage that fell due through its referral
        side only.

        The referral arm only counts while that side is deferred on
        its own: 'Referrer Recognition Date' is defaulted on *every*
        usage, referrer or not, so an arm reading it unconditionally
        would report a usage as due the day it was created --
        including usages whose referrer merely follows the voucher
        user ('Same as Customer'), which the first arm already covers.

        Both arms stay on ``promotion_code_usage``'s own columns on
        purpose. Reaching across to ``promotion_code_id.partner_id``
        to also require a referrer would drag that model's own record
        rule (``user_id == user.id``) into the subquery, silently
        dropping usages whose promotion code belongs to somebody else
        -- a wrong answer nobody would see. The over-inclusion left
        behind is harmless: a usage without a referrer but with an
        explicitly Deferred referrer method is deferred on its voucher
        user side anyway (``recognition_state`` ``pending`` says so),
        so it does have something to release; only its due date
        arrives earlier.

        :param date: latest due date to include, on either side, or
            ``False`` for no upper bound
        :return: list of matching ``promotion_code_usage`` ids
        """
        domain = [("recognition_state", "=", "pending")]
        if date:
            domain += [
                "|",
                ("recognition_date", "<=", date),
                "&",
                ("referrer_recognition_method", "=", "deferred"),
                ("referrer_recognition_date", "<=", date),
            ]
        return self.env["promotion_code_usage"].search(domain).ids

    def action_create_due_recognition(self):
        """Release every selected Usage's own Amount Deferred.

        :return: an ``ir.actions.act_window`` dict listing the newly
            created ``promotion_code_usage_recognition`` documents
        """
        for record in self.sudo():
            result = record._create_due_recognition()
        return result

    def _create_due_recognition(self):
        """Create one draft Recognition per selected Usage.

        :return: an ``ir.actions.act_window`` dict opening the newly
            created documents
        :raises UserError: when no Usage is selected
        """
        self.ensure_one()
        self._check_usage_ids()
        Recognition = self.env["promotion_code_usage_recognition"]
        recognitions = Recognition
        for usage in self.usage_ids:
            recognitions |= Recognition.create(
                self._prepare_due_recognition_data(usage)
            )
        return self._open_recognitions(recognitions)

    def _check_usage_ids(self):
        """Reject running the wizard with no Usage selected.

        :raises UserError: when ``usage_ids`` is empty
        """
        self.ensure_one()
        if not self.usage_ids:
            error_message = (
                _(
                    """
Context: Create due promotion recognition
Database ID: %s
Problem: No Usage is due for recognition as of the selected Date
Solution: Pick a later Date, or check the usages' own Recognition Date
"""
                )
                % (self.id,)
            )
            raise UserError(error_message)

    def _prepare_due_recognition_data(self, usage):
        """Build one Recognition document's create values.

        :param usage: the due, deferred ``promotion_code_usage``
            being released
        :return: dict of ``promotion_code_usage_recognition`` values
        """
        self.ensure_one()
        return {
            "usage_id": usage.id,
            "date": self.date,
            "amount": usage.amount_deferred,
            "journal_id": usage.recognition_journal_id.id,
        }

    def _open_recognitions(self, recognitions):
        """Build the window action listing the newly created documents.

        :param recognitions: the ``promotion_code_usage_recognition``
            recordset just created
        :return: an ``ir.actions.act_window`` dict
        """
        self.ensure_one()
        waction = self.env.ref(
            "ssi_promotion.promotion_code_usage_recognition_action"
        ).read()[0]
        waction.update(
            {
                "view_mode": "tree,form",
                "domain": [("id", "in", recognitions.ids)],
            }
        )
        return waction
