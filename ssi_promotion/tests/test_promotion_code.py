# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionCode(YamlTransactionCase):
    """Scenario tests for ``promotion_code``."""

    def test_promotion_code(self):
        """Run the CRUD, workflow, and onchange scenarios."""
        self.run_yaml_scenario("test_data_promotion_code.yaml")
