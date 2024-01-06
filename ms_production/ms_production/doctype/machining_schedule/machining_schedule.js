// Copyright (c) 2024, Abhishek Chougule and contributors
// For license information, please see license.txt

frappe.ui.form.on('Machining Schedule', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Machining Schedule', {
    item_group: function(frm) {
		frm.clear_table("item_machining_schedule");
		frm.refresh_field('item_machining_schedule');
		frm.clear_table("machining_schedule_details");
		frm.refresh_field('machining_schedule_details');
            frm.call({
			method:'method_after_item_group',
			doc:frm.doc,
		});
    }
});

frappe.ui.form.on('Machining Schedule', {
    refresh: function(frm) {

            frm.call({
			method:'method_on_refresh',
			doc:frm.doc,
		});
    }
});

frappe.ui.form.on('Machining Schedule', {
    refresh_button: function(frm) {

            frm.call({
			method:'method_on_refresh',
			doc:frm.doc,
		});
    }
});
// ==========================================================================================Item Machining Schedule================================================================

frappe.ui.form.on('Item Machining Schedule', {
    schedule_quantity: function(frm) {
            frm.call({
			method:'set_estimated_cycle_time',
			doc:frm.doc,
		});
    }
});