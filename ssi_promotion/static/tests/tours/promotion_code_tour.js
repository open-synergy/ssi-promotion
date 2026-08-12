odoo.define("ssi_promotion.promotion_code_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // ── Shared Flow 1 — Open the Promotion > Codes menu.
    var openCodesMenuSteps = [
        tour.stepUtils.showAppsMenuItem(),
        {
            content: "Open the Promotion app",
            trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
        },
        {
            content: "Open the Codes menu",
            trigger:
                '.o_menu_sections [data-menu-xmlid="ssi_promotion.promotion_code_menu"]',
        },
        {
            // Gerbang: tunggu action TUJUAN benar-benar terpasang (nama
            // action, bukan nama menuitem -- keduanya berbeda di sini:
            // menuitem "Codes", action "Promotion Codes").
            content: "Codes list is displayed",
            trigger:
                ".o_control_panel .breadcrumb-item.active:contains(Promotion Codes)",
            extra_trigger: ".o_list_view",
            run: function () {
                // Assertion only; do not trigger the default click action.
            },
        },
    ];

    // IK: docs/promotion_code/01-create.md
    tour.register(
        "ssi_promotion_promotion_code_create",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
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

            // Flow 3 — Fill in the required fields (Voucher Code,
            // Promotion Type). Discount & Usage tab fields are
            // auto-filled by onchange once Promotion Type is picked --
            // out of tour scope (value verification is unit-test
            // territory).
            {
                content: "Fill in the Voucher Code",
                trigger: ".o_field_widget[name='voucher_code']",
                extra_trigger: ".o_form_view.o_form_editable",
                run: "text TOUR-PC-CREATE",
            },
            {
                content: "Select the Promotion Type",
                trigger: ".o_field_many2one[name='type_id'] input",
                run: "text TOUR PC Type",
            },
            {
                content: "Pick the type from the dropdown",
                trigger: ".ui-autocomplete .ui-menu-item a:contains(TOUR PC Type)",
                in_modal: false,
            },

            // Flow 5 — Click Save.
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

    // IK: docs/promotion_code/02-edit.md
    tour.register(
        "ssi_promotion_promotion_code_edit",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Find and open the record to edit.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-EDIT) .o_data_cell:first",
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

            // Flow 4 — Open the Note tab and change the Note field.
            // The Note tab is not the active tab by default (the
            // Discount & Usage tab is inserted first): its pane stays
            // display:none, hiding the textarea from the tour, until
            // this tab is opened.
            {
                content: "Open the Note tab",
                trigger: ".o_notebook .nav-link:contains(Note)",
            },
            {
                content: "Change the Note",
                trigger: "textarea.o_field_widget[name='note']",
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

    // IK: docs/promotion_code/03-delete.md
    tour.register(
        "ssi_promotion_promotion_code_delete",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to delete.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-DELETE) .o_data_cell:first",
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
                content: "Click the Promotion Codes breadcrumb",
                trigger: ".breadcrumb-item.o_back_button a:contains(Promotion Codes)",
            },

            // Post-Condition — Back on the list, without the record.
            {
                content: "Back to the list without the deleted record",
                trigger: ".o_list_view:not(:has(.o_data_row:contains(TOUR-PC-DELETE)))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/04-confirm.md
    tour.register(
        "ssi_promotion_promotion_code_confirm",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to confirm.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-CONFIRM) .o_data_cell:first",
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

    // IK: docs/promotion_code/05-approve.md
    tour.register(
        "ssi_promotion_promotion_code_approve",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to approve.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-APPROVE) .o_data_cell:first",
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

            // Post-Condition — Sole approval level fulfilled: this
            // document is automatically opened, status jumps straight
            // to Open.
            {
                content: "Status is Open",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='open'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/06-reject.md
    tour.register(
        "ssi_promotion_promotion_code_reject",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to reject.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-REJECT) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Reject button.
            {
                content: "Click the Reject button",
                trigger: ".o_statusbar_buttons button[name='action_reject_approval']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Rejected.
            {
                content: "Status is Rejected",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='reject'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/09-finish.md
    tour.register(
        "ssi_promotion_promotion_code_finish",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to finish.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-FINISH) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Done button.
            {
                content: "Click the Done button",
                trigger: ".o_statusbar_buttons button[name='action_done']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Done.
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

    // IK: docs/promotion_code/10-cancel.md
    tour.register(
        "ssi_promotion_promotion_code_cancel",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to cancel.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-CANCEL) .o_data_cell:first",
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
            // Cancel_reason_id is rendered with widget="radio" by
            // the Select Cancel Reason wizard view
            // (ssi_transaction_cancel_mixin/wizards/
            // base_select_cancel_reason_views.xml), so it is a radio
            // item that gets clicked -- not a many2one autocomplete.
            {
                content: "Select the cancellation reason",
                trigger:
                    ".o_field_widget[name='cancel_reason_id'] " +
                    ".o_radio_item:contains(TOUR PC Cancel Reason) input",
                run: "click",
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

    // IK: docs/promotion_code/12-restart.md
    tour.register(
        "ssi_promotion_promotion_code_restart",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to restart.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-RESTART) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Restart button.
            {
                content: "Click the Restart button",
                trigger: ".o_statusbar_buttons button[name='action_restart']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status returns to Draft.
            {
                content: "Status is Draft",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/13-reset-number.md
    tour.register(
        "ssi_promotion_promotion_code_reset_number",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record whose document number will be
            // reset. The Pre-Condition fixture carries the manually
            // assigned number "TOUR-PC-RESET-MANUAL".
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-RESET) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open with its manual document number",
                trigger:
                    ".oe_title .o_field_widget[name='display_name']" +
                    ":contains(TOUR-PC-RESET-MANUAL)",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Reset Document Number button.
            {
                content: "Click the Reset Document Number button",
                trigger:
                    ".o_statusbar_buttons button[name='action_reset_document_number']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Document number returns to "/", shown
            // as "*<id>" by name_get (mixin_transaction.py). This
            // string could not have matched before the reset ran,
            // since the record showed its manual number instead
            // (patterns.md §P).
            {
                content: "Document number returns to /",
                trigger: ".oe_title .o_field_widget[name='display_name']:contains(*)",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/14-restart-approval.md
    tour.register(
        "ssi_promotion_promotion_code_restart_approval",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to restart the approval
            // process for.
            {
                content: "Open the record",
                trigger:
                    ".o_data_row:contains(TOUR-PC-RESTART-APPROVAL) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Restart Approval Process button.
            {
                content: "Click the Restart Approval Process button",
                trigger:
                    ".o_statusbar_buttons button[name='action_reload_approval_template']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status remains Waiting for Approval, and
            // the Approvals tab displays the approval list newly formed
            // from the approval template. Row count/content is out of
            // tour scope (unit test territory); the gate below only
            // proves the reload happened.
            {
                content: "Open the Approvals tab",
                trigger: ".o_notebook .nav-link:contains(Approvals)",
                extra_trigger: "body:not(:has(.modal))",
            },
            {
                content: "The approval process has been rebuilt",
                trigger: ".o_field_widget[name='approval_ids'] .o_data_row",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content: "Status is still Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );
});
