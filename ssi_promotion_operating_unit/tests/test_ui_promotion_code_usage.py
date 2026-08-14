# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. In 14.0, plain HttpCase does not set
# up ``cls.env`` in ``setUpClass`` (see odoo-development-ui-test skill,
# structure-and-runner.md "Base class").
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiPromotionCodeUsageOperatingUnit(HttpSavepointCase):
    """UI/UX tour test for the ``promotion_code_usage`` delta work
    instruction.

    ``ssi_promotion_operating_unit`` is an extension module, so its IK
    file is a delta IK: it carries no Flow of its own, only an
    "Additional Fields" section on top of the Flow written in
    ``ssi_promotion``. The tour run here is delta-only accordingly -- it
    borrows the navigation of the base Flow and asserts only that the
    **Operating Unit** field is rendered on the ``promotion_code_usage``
    create form.
    """

    @classmethod
    def setUpClass(cls):
        """Prepare the IK Pre-Conditions of the delta
        promotion_code_usage tour.

        * ``Module`` -- satisfied by the module being installed, which
          is what makes this test run at all.
        * ``Access`` -- the tour user is put in
          ``operating_unit.group_multi_operating_unit``, without which
          the **Operating Unit** field is not rendered at all and the
          tour would fail for the wrong reason. ``base.user_admin``
          already holds it through ``group_manager_operating_unit``; it
          is written explicitly here so the Pre-Condition does not
          depend on that implication staying in place.
        * ``Access`` of the base Flow -- the same user is put in
          ``ssi_promotion.promotion_code_usage_user_group``, the group
          the base IK names as actor.

        No record fixture is needed: the tour stops at the blank create
        form, which already renders the Operating Unit field without any
        data being entered.
        """
        super().setUpClass()

        cls.user_admin = cls.env.ref("base.user_admin")
        groups = cls.env.ref(
            "ssi_promotion.promotion_code_usage_user_group"
        ) + cls.env.ref("operating_unit.group_multi_operating_unit")
        groups.sudo().write(
            {
                "users": [(4, cls.user_admin.id)],
            }
        )

    def test_create(self):
        """Run the delta create tour for ``promotion_code_usage``.

        The tour is delta-only: it walks Flow 1 to Flow 2 of the base IK
        (``ssi_promotion/docs/promotion_code_usage/01-create.md``) to
        reach the blank create form, then asserts the **Operating Unit**
        field the delta IK adds to it.

        IK: docs/promotion_code_usage/01-create.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_operating_unit_promotion_code_usage_create",
            login="admin",
        )
