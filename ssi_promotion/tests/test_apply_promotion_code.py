# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestApplyPromotionCode(YamlTransactionCase):
    """Scenario tests for the ``apply_promotion_code`` wizard."""

    def test_apply_promotion_code(self):
        """Run the positive and negative-path Apply Promotion Code
        scenarios.
        """
        self.run_yaml_scenario("test_data_apply_promotion_code.yaml")

    def test_apply_python_code(self):
        """Run the promotion type's own Apply Check Python Code
        scenarios.

        Kept in its own file, and so in its own transaction: the
        scenarios of a single YAML file share one, and these ones each
        rebuild a promotion type of their own.
        """
        self.run_yaml_scenario("test_data_apply_promotion_code_apply_python.yaml")

    def test_action_apply_promotion_code_returns_action(self):
        """Assert the window action returned by the wizard's own
        ``action_apply_promotion_code``.

        Pure Python -- trigger P1 (L-01: the ``wizard`` action calls
        the method but does not expose its return value, so YAML
        cannot assert a dict's keys).
        """
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        income_account = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        product = self.env["product.product"].create(
            {
                "name": "Apply Promotion Code Return Product",
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )
        account_move_model = self.env["ir.model"].search(
            [("model", "=", "account.move")], limit=1
        )
        income_usage = self.env.ref(
            "ssi_product_usage_account_type.product_usage_type_income"
        )
        promotion_type = self.env["promotion_type"].create(
            {
                "name": "Apply Promotion Code Return Type",
                "code": "/",
                "discount_usage_id": income_usage.id,
                "discount_type": "fixed",
                "discount_amount": 50000.0,
                "journal_id": journal.id,
                "product_id": product.id,
                "allowed_model_ids": [(6, 0, account_move_model.ids)],
            }
        )
        admin = self.env.ref("base.user_admin")
        code = self.env["promotion_code"].create(
            {
                "voucher_code": "APPLYPC-RETURN-001",
                "type_id": promotion_type.id,
                "user_id": admin.id,
            }
        )
        code.with_user(admin).action_confirm()
        code.invalidate_cache()
        code.with_user(admin).action_approve_approval()
        customer = self.env["res.partner"].create(
            {"name": "Apply Promotion Code Return Customer"}
        )
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": customer.id,
                "journal_id": journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": 1,
                            "price_unit": 1000000.0,
                            "name": "Apply Promotion Code Return Line",
                            "account_id": income_account.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        wizard = (
            self.env["apply_promotion_code"]
            .with_context(active_model="account.move", active_id=invoice.id)
            .create({"promotion_code_id": code.id})
        )
        action = wizard.action_apply_promotion_code()
        usage = self.env["promotion_code_usage"].search(
            [
                ("promotion_code_id", "=", code.id),
                ("document_reference", "=", "account.move,%d" % invoice.id),
            ]
        )
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "promotion_code_usage")
        self.assertEqual(action["res_id"], usage.id)
