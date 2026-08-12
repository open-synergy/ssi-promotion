odoo.define("ssi_promotion.promotion_code_usage_recognition_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // ── Shared Flow 1 — Open the Promotion > Usage Recognitions menu.
    var openUsageRecognitionsMenuSteps = [
        tour.stepUtils.showAppsMenuItem(),
        {
            content: "Open the Promotion app",
            trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
        },
        {
            content: "Open the Usage Recognitions menu",
            trigger:
                '.o_menu_sections [data-menu-xmlid="ssi_promotion.promotion_code_usage_recognition_menu"]',
        },
        {
            // Gerbang: tunggu action TUJUAN benar-benar terpasang, bukan
            // sekadar "ada list di layar" (landasan app adalah Codes).
            content: "Usage Recognitions list is displayed",
            trigger:
                ".o_control_panel .breadcrumb-item.active:contains(Usage Recognitions)",
            extra_trigger: ".o_list_view",
            run: function () {
                // Assertion only.
            },
        },
    ];

    // IK: docs/promotion_code_usage_recognition/01-create.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_create",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Click the New button. (14.0: "Create")
            {
                content: "Click Create",
                trigger: ".o_list_button_add",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Form is open in edit mode",
                trigger: ".o_form_view.o_form_editable",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Fill in the required fields (# Usage; Amount and
            // Journal are auto-filled from # Usage via onchange).
            {
                content: "Select the # Usage",
                trigger: ".o_field_many2one[name='usage_id'] input",
                run: "text TOUR-PCUR-USAGE",
            },
            {
                content: "Pick the usage from the dropdown",
                trigger: ".ui-autocomplete .ui-menu-item a:contains(TOUR-PCUR-USAGE)",
                in_modal: false,
            },

            // Flow 4 — Click Save.
            {
                content: "Save the record",
                trigger: ".o_form_button_save",
            },

            // Post-Condition — A new record is created in Draft status.
            {
                content: "Record is saved in Draft status",
                trigger: ".o_form_view.o_form_readonly",
                extra_trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage_recognition/02-edit.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_edit",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Find and open the record to edit.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCUR-EDIT) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Edit button.
            {
                content: "Click the Edit button",
                trigger: ".o_form_button_edit",
            },
            {
                content: "Form is now editable",
                trigger: ".o_form_view.o_form_editable",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 4 — Change the Note field.
            {
                content: "Change the Note",
                trigger: ".o_field_widget[name='note'] textarea",
                run: "text Edited via UI test tour.",
            },

            // Flow 5 — Click Save.
            {
                content: "Save the record",
                trigger: ".o_form_button_save",
            },

            // Post-Condition — The record is updated with the new values.
            {
                content: "Record is saved",
                trigger: ".o_form_view.o_form_readonly",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage_recognition/03-delete.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_delete",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Open the record to delete.
            // This fixture keeps its default document number "/" (the
            // IK Pre-Condition for delete), so its own display name
            // renders as "*<id>" (mixin_transaction.py name_get) --
            // the only row in this list carrying a literal "*".
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(*) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click Action > Delete.
            {
                content: "Open the Action menu",
                trigger: ".o_cp_action_menus button:contains(Action)",
            },
            {
                content: "Click Delete",
                // Item Action menu adalah komponen Owl; cocokkan LABEL
                // PERSIS, bukan substring ":contains" yang bisa keliru
                // menunjuk item lain (mis. "Archive").
                trigger: ".o_cp_action_menus .o_menu_item a",
                run: function () {
                    var $delete = $(".o_cp_action_menus .o_menu_item a").filter(
                        function () {
                            return $(this).text().trim() === "Delete";
                        }
                    );
                    $delete[0].click();
                },
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm deletion",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // After delete, 14.0 can display the NEXT record in the
            // list instead of returning to the list itself. Click the
            // breadcrumb explicitly before asserting the list.
            {
                content: "Click the Usage Recognitions breadcrumb",
                trigger:
                    ".breadcrumb-item.o_back_button a:contains(Usage Recognitions)",
            },

            // Post-Condition — Back on the list, without the record.
            {
                content: "Back to the list without the deleted record",
                trigger: ".o_list_view:not(:has(.o_data_row:contains(*)))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage_recognition/04-confirm.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_confirm",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Open the record to confirm.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCUR-CONFIRM) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Confirm button.
            {
                content: "Click the Confirm button",
                trigger: ".o_statusbar_buttons button[name='action_confirm']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Waiting for Approval.
            {
                content: "Status is Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage_recognition/05-approve.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_approve",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Open the record to approve.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCUR-APPROVE) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Approve button.
            {
                content: "Click the Approve button",
                trigger: ".o_statusbar_buttons button[name='action_approve_approval']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — All approval levels fulfilled: this
            // document is automatically finished, status jumps
            // straight to Done.
            {
                content: "Status is Done",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='done'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage_recognition/10-cancel.md
    tour.register(
        "ssi_promotion_promotion_code_usage_recognition_cancel",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsageRecognitionsMenuSteps, [
            // Flow 2 — Open the record to cancel.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCUR-CANCEL) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Cancel button.
            // The Cancel button is type="action" (it opens the
            // base.select_cancel_reason wizard action) -- its "name"
            // attribute resolves to a numeric action id at render time,
            // so it must be targeted by label, not by name
            // (selectors.md §4).
            {
                content: "Click the Cancel button",
                trigger: ".o_statusbar_buttons button:enabled:contains('Cancel')",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — In the wizard that appears, select the
            // Cancellation Reason.
            {
                content: "Wizard is open",
                // 14.0: trigger is searched INSIDE the modal, so do not
                // prefix it with ".modal" (see patterns.md §H).
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content: "Select the cancellation reason",
                trigger: ".o_field_many2one[name='cancel_reason_id'] input",
                run: "text TOUR Cancel Reason",
            },
            {
                content: "Pick the reason from the dropdown",
                trigger:
                    ".ui-autocomplete .ui-menu-item a:contains(TOUR Cancel Reason)",
                in_modal: false,
            },

            // Flow 5 — Click Confirm.
            {
                content: "Confirm the wizard",
                trigger: ".modal-footer button[name='action_confirm']",
                in_modal: true,
            },

            // Flow 6 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Cancelled.
            {
                content: "Status is Cancelled",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='cancel'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );
});
