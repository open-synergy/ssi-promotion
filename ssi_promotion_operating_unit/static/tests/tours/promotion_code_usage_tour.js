// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("ssi_promotion_operating_unit.promotion_code_usage_tour", function (
    require
) {
    "use strict";

    var tour = require("web_tour.tour");

    // IK: docs/promotion_code_usage/01-create.md
    //
    // THIS IS A DELTA-ONLY TOUR (odoo-development-ui-test
    // patterns.md §O). ssi_promotion_operating_unit is an extension
    // module and its IK file is a delta IK: it carries no Flow of
    // its own, only an "Additional Fields" section on top of the
    // Flow of ssi_promotion's own
    // docs/promotion_code_usage/01-create.md. The navigation below
    // is therefore taken from the base Flow (Flow 1 to Flow 2 of
    // that file, opening a blank create form), and the only thing
    // this tour adds is the assertion that the Operating Unit field
    // is rendered on that form.
    //
    // TWO DELIBERATE BOUNDARIES, stated here rather than silently
    // skipped:
    //
    // 1. Base Flow 3 ("fill in the required fields") and Flow 5
    //    ("Click Save") are NOT walked. The item's Keputusan Desain
    //    scopes this tour to "assertion bahwa field Operating Unit
    //    muncul di form", and forbids the delta tour from
    //    re-walking the base create/edit flow. Actually creating a
    //    promotion_code_usage record is already covered by
    //    ssi_promotion's own create tour
    //    (ssi_promotion_promotion_code_usage_create). No fixture
    //    data is required for this tour as a result -- the blank
    //    create form already renders the field.
    // 2. The "Modified -- Record Visibility" section of the delta
    //    IK produces no step here. The Keputusan Desain rules it
    //    out, and the IK itself says "This is not a Flow step";
    //    which documents a record rule sees is a value fact covered
    //    by the unit tests in ssi_promotion_operating_unit/tests/
    //    test_data_ssi_promotion_operating_unit.yaml.
    tour.register(
        "ssi_promotion_operating_unit_promotion_code_usage_create",
        {
            test: true,
            url: "/web",
        },
        [
            // -- Base Flow 1 -- Open the Promotion > Usages menu.
            tour.stepUtils.showAppsMenuItem(),
            {
                content: "Open the Promotion app",
                trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
            },
            {
                content: "Open the Usages menu",
                trigger:
                    ".o_menu_sections " +
                    '[data-menu-xmlid="ssi_promotion.promotion_code_usage_menu"]',
            },
            {
                // Gerbang: tunggu action TUJUAN benar-benar
                // terpasang (nama action, bukan nama menuitem).
                content: "Usages list is displayed",
                trigger:
                    ".o_control_panel .breadcrumb-item.active" +
                    ":contains(Promotion Code Usages)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only; do not trigger the default
                    // click action.
                },
            },

            // -- Base Flow 2 -- Click the New button. (14.0:
            // "Create")
            {
                content: "Click Create",
                trigger: ".o_list_button_add",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Form is open in edit mode",
                trigger: ".o_form_view.o_form_editable",
                run: function () {
                    // Assertion only; do not trigger the default
                    // click action.
                },
            },

            // -- DELTA (Additional Fields of
            // ssi_promotion_operating_unit/docs/
            // promotion_code_usage/01-create.md) -- the Operating
            // Unit field is available on the promotion_code_usage
            // create form.
            //
            // The form opens in edit mode, so the many2one renders
            // its <input>, which has real dimensions even while the
            // field is empty. The field is not required and its
            // default comes from the user's default operating unit,
            // so it may well be empty here -- and this assertion
            // deliberately does not read its value, which is unit
            // test territory.
            //
            // The field is declared with
            // groups="operating_unit.group_multi_operating_unit" in
            // views/promotion_code_usage.xml, so it is only
            // rendered for a member of that group. setUpClass puts
            // the tour user there, which is the Access
            // Pre-Condition of the delta IK.
            {
                content: "The Operating Unit field is displayed in the form",
                trigger: ".o_field_widget[name='operating_unit_id'] input",
                run: function () {
                    // Assertion only; do not trigger the default
                    // click action.
                },
            },
        ]
    );
});
