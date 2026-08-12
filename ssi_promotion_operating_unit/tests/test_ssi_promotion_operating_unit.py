# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSsiPromotionOperatingUnit(YamlTransactionCase):
    """Cover operating unit propagation and record rule scoping.

    Exercises ``promotion_code``/``promotion_code_usage``: the
    ``operating_unit_id`` value set on creation, and that the record
    rule actually restricts visibility between users of different
    operating units.
    """

    def test_ssi_promotion_operating_unit(self):
        """Run the ``test_data_ssi_promotion_operating_unit.yaml`` scenario."""
        self.run_yaml_scenario("test_data_ssi_promotion_operating_unit.yaml")
