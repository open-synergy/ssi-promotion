# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestMixinPromotionObject(YamlTransactionCase):
    """Scenario tests for ``mixin.promotion_object``, exercised through
    its first inheriting model, ``account.move``.
    """

    def test_mixin_promotion_object(self):
        """Run the ``promotion_usage_ids``/``promotion_usage_count``
        scenario.
        """
        self.run_yaml_scenario("test_data_mixin_promotion_object.yaml")

    def test_action_open_promotion_usage_returns_action(self):
        """Assert the window action returned by
        ``action_open_promotion_usage``.

        Pure Python -- trigger P1 (L-01: the ``call`` action discards
        the return value, so YAML cannot assert a dict's keys).
        """
        journal = self.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        move = self.env["account.move"].create(
            {"move_type": "entry", "journal_id": journal.id}
        )
        action = move.action_open_promotion_usage()
        self.assertEqual(action["res_model"], "promotion_code_usage")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["domain"], [("id", "in", move.promotion_usage_ids.ids)])

    def test_action_apply_promotion_code_returns_action(self):
        """Assert the window action returned by
        ``action_apply_promotion_code``.

        Pure Python -- trigger P1 (L-01: the ``call`` action discards
        the return value, so YAML cannot assert a dict's keys).
        """
        journal = self.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        move = self.env["account.move"].create(
            {"move_type": "entry", "journal_id": journal.id}
        )
        action = move.action_apply_promotion_code()
        self.assertEqual(action["res_model"], "apply_promotion_code")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["target"], "new")
        self.assertEqual(
            action["context"],
            {"active_model": "account.move", "active_id": move.id},
        )
