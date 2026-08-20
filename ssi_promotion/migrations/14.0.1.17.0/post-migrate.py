# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Migration: 14.0.1.16.0 -> 14.0.1.17.0
#
# Changes: the manual 'Done' button on 'promotion_code_usage' is
#          removed -- the Open <-> Done transition is now driven
#          entirely by base.automation (open-synergy/ssi-promotion#72).
#          Existing rows stuck in 'open' with no deferred side left
#          (recognition_state 'not_applicable' or 'recognized') will
#          never trigger that automation again, since nothing ever
#          calls 'write()' on them after this upgrade. This stamps
#          those rows to 'done' directly.

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Move stale 'open' rows with nothing left deferred to 'done'.

    Writes 'state' directly through SQL instead of calling
    ``action_done()``: these rows already carry their own journal
    entry and document number from when they were first opened, so
    re-running the 'post_open'/'done' hooks on them would be wrong.

    :param env: the migration environment
    :param version: the version being migrated to (unused)
    :return: nothing; updates ``promotion_code_usage`` rows
    """
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE promotion_code_usage
        SET state = 'done'
        WHERE state = 'open'
        AND recognition_state IN ('not_applicable', 'recognized')
        """,
    )
    _logger.info(
        "Stamped state='done' on %s promotion_code_usage row(s) stuck "
        "in 'open' with nothing left deferred.",
        env.cr.rowcount,
    )
