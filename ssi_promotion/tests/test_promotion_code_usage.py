# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionCodeUsage(YamlTransactionCase):
    def _setup_accounting(self):
        account_type = self.env.ref("account.data_account_type_revenue")
        income_account = self.env["account.account"].create(
            {
                "code": "PROMO-TEST",
                "name": "Promotion Test Income",
                "user_type_id": account_type.id,
            }
        )
        journal = self.env["account.journal"].create(
            {
                "name": "Promotion Test Sales Journal",
                "code": "PROMOTEST",
                "type": "sale",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        product = self.env["product.product"].create(
            {
                "name": "Promotion Test Product",
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )
        return income_account, journal, product

    def _confirm_and_approve(self, record):
        admin = self.env.ref("base.user_admin")
        record.with_user(admin).action_confirm()
        # Force a fresh read of policy fields (confirm_ok/approve_ok/...):
        # approval.approval records created by action_confirm() above are
        # linked via a plain Integer res_id (not a Many2one), so Odoo's ORM
        # cannot auto-invalidate the cached policy fields computed earlier
        # in this same admin environment.
        record.invalidate_cache()
        record.with_user(admin).action_approve_approval()

    def _open_promotion_code(self, promotion_code):
        self._confirm_and_approve(promotion_code)

    def test_promotion_code_usage(self):
        self.run_yaml_scenario("test_data_promotion_code_usage.yaml")

    def test_document_reference_disallowed_model_rejected(self):
        """Setting document_reference to a model not listed in the
        promotion type's allowed_model_ids raises a ValidationError."""
        _income_account, journal, product = self._setup_accounting()
        ptype = self.env["promotion_type"].create(
            {
                "name": "Disallowed Model Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
                "journal_id": journal.id,
                "product_id": product.id,
            }
        )
        promotion_code = self.env["promotion_code"].create(
            {
                "voucher_code": "DISALLOWED-001",
                "type_id": ptype.id,
            }
        )
        self._open_promotion_code(promotion_code)
        customer = self.env["res.partner"].create({"name": "Customer Disallowed"})
        other_partner = self.env["res.partner"].create({"name": "Some Other Partner"})
        with self.assertRaises(ValidationError):
            with self.cr.savepoint():
                self.env["promotion_code_usage"].create(
                    {
                        "promotion_code_id": promotion_code.id,
                        "partner_id": customer.id,
                        "document_reference": "res.partner,%d" % other_partner.id,
                    }
                )

    def test_confirm_fails_when_usage_limit_exceeded(self):
        """Confirming a usage beyond the promotion type's usage_limit
        raises a UserError."""
        _income_account, journal, product = self._setup_accounting()
        ptype = self.env["promotion_type"].create(
            {
                "name": "Limited Usage Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
                "journal_id": journal.id,
                "product_id": product.id,
            }
        )
        promotion_code = self.env["promotion_code"].create(
            {
                "voucher_code": "LIMIT-001",
                "type_id": ptype.id,
                "usage_limit": 1,
            }
        )
        self._open_promotion_code(promotion_code)
        customer = self.env["res.partner"].create({"name": "Customer Limit"})
        first_usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": promotion_code.id,
                "partner_id": customer.id,
            }
        )
        self._confirm_and_approve(first_usage)
        second_usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": promotion_code.id,
                "partner_id": customer.id,
            }
        )
        with self.assertRaises(UserError):
            second_usage.with_user(self.env.ref("base.user_admin")).action_confirm()

    def test_confirm_fails_when_validity_python_code_false(self):
        """Confirming a usage of a type whose validity_python_code assigns
        result = False raises a UserError."""
        _income_account, journal, product = self._setup_accounting()
        ptype = self.env["promotion_type"].create(
            {
                "name": "Always Invalid Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
                "journal_id": journal.id,
                "product_id": product.id,
                "validity_python_code": "result = False",
            }
        )
        promotion_code = self.env["promotion_code"].create(
            {
                "voucher_code": "INVALID-001",
                "type_id": ptype.id,
            }
        )
        self._open_promotion_code(promotion_code)
        customer = self.env["res.partner"].create({"name": "Customer Invalid"})
        usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": promotion_code.id,
                "partner_id": customer.id,
            }
        )
        with self.assertRaises(UserError):
            usage.with_user(self.env.ref("base.user_admin")).action_confirm()

    def test_approve_fails_when_credit_note_configuration_missing(self):
        """Approving a usage of a type without journal_id/product_id raises
        a UserError instead of silently skipping credit note creation."""
        ptype = self.env["promotion_type"].create(
            {
                "name": "No Accounting Config Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
            }
        )
        promotion_code = self.env["promotion_code"].create(
            {
                "voucher_code": "NOCONFIG-001",
                "type_id": ptype.id,
            }
        )
        self._open_promotion_code(promotion_code)
        customer = self.env["res.partner"].create({"name": "Customer No Config"})
        usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": promotion_code.id,
                "partner_id": customer.id,
            }
        )
        admin = self.env.ref("base.user_admin")
        usage.with_user(admin).action_confirm()
        usage.invalidate_cache()
        with self.assertRaises(UserError):
            usage.with_user(admin).action_approve_approval()

    def test_credit_note_creation_is_not_duplicated_on_replay(self):
        """Calling the credit note creation hook again after approval must
        not create a second credit note (idempotency guard)."""
        _income_account, journal, product = self._setup_accounting()
        ptype = self.env["promotion_type"].create(
            {
                "name": "Guard Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 3000.0,
                "journal_id": journal.id,
                "product_id": product.id,
            }
        )
        promotion_code = self.env["promotion_code"].create(
            {
                "voucher_code": "GUARD-001",
                "type_id": ptype.id,
            }
        )
        self._open_promotion_code(promotion_code)
        customer = self.env["res.partner"].create({"name": "Customer Guard"})
        usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": promotion_code.id,
                "partner_id": customer.id,
            }
        )
        self._confirm_and_approve(usage)
        credit_note = usage.credit_note_id
        self.assertTrue(credit_note)
        move_domain = [("invoice_origin", "=", usage.name)]
        move_count_before = self.env["account.move"].search_count(move_domain)
        usage._10_create_credit_note()
        self.assertEqual(usage.credit_note_id, credit_note)
        move_count_after = self.env["account.move"].search_count(move_domain)
        self.assertEqual(move_count_before, move_count_after)
