odoo.define("ssi_promotion.promotion_code_usage_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // IK: docs/promotion_code_usage/01-create-due-recognition.md
    tour.register(
        "ssi_promotion_promotion_code_usage_create_due_recognition",
        {
            test: true,
            url: "/web",
        },
        [
            // Flow 1 — Open the Promotion > Create Due Recognition menu.
            tour.stepUtils.showAppsMenuItem(),
            {
                content: "Open the Promotion app",
                trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
            },
            {
                content: "Open the Create Due Recognition menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_promotion.create_due_promotion_recognition_menu"]',
            },

            // Flow 2 — The wizard opens with Date and Usages pre-filled.
            {
                content: "The wizard is displayed",
                // 14.0: trigger is searched INSIDE the modal, so do not
                // prefix it with ".modal" (see patterns.md §H).
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Create Due Recognition button.
            {
                content: "Click the Create Due Recognition button",
                trigger: ".modal-footer button[name='action_create_due_recognition']",
            },

            // Post-Condition — The list of newly created Usage Recognition
            // documents is displayed.
            {
                content: "Usage Recognitions list is displayed",
                trigger:
                    ".o_control_panel .breadcrumb-item.active:contains(Usage Recognitions)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only.
                },
            },
        ]
    );
});
