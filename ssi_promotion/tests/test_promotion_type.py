# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionType(YamlTransactionCase):
    """Scenario tests for ``promotion_type``."""

    def test_promotion_type(self):
        """Run the CRUD scenarios."""
        self.run_yaml_scenario("test_data_promotion_type.yaml")
