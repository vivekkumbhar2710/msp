// Copyright (c) 2023, Abhishek Chougule and contributors
// For license information, please see license.txt

frappe.ui.form.on('Job Work Receipt', {
	// refresh: function(frm) {

	// }
});


// ============================================================= Job Work Receipt ================================================= 

// frappe.ui.form.on('Job Work Receipt', {
//     setup: function (frm) {
//         frm.set_query("source_warehouse", "return_items", function (doc, cdt, cdn) {
//             let d = locals[cdt][cdn];
            
//             return {
//                 filters: 
//                     [["Warehouse", "name", 'in', ['CONSUMABLE - AFPLA']] ]//'rejection_type': d.rejection_type
                
//             };
//         });
//     }
// });




frappe.ui.form.on('Job Work Receipt', {
    return_against(frm) {
        frm.clear_table("return_items");
		frm.refresh_field('return_items');
        frm.call({
			method:'set_data_from_jwr',
			doc:frm.doc,
		})
    }
});



frappe.ui.form.on('Job Work Receipt', {
    set_warehouse: function(frm) {

		var args = {
            source_warehouse: frm.doc.set_warehouse,
            child_table: 'raw_items',
			warehouse_in_table: 'accepted_warehouse',
        };

        frm.call({
			method:'set_warehouse_in_child_table',
			args: args,
			doc:frm.doc,
		})
    }
});



frappe.ui.form.on('Job Work Receipt', {
    set_from_warehouse: function(frm) {

		var args = {
            source_warehouse: frm.doc.set_from_warehouse,
            child_table: 'return_items',
			warehouse_in_table: 'source_warehouse',
        };

        frm.call({
			method:'set_warehouse_in_child_table',
			args: args,
			doc:frm.doc,
		})
    }
});






frappe.ui.form.on('Job Work Receipt', {
    order_no: function (frm) {
        frm.clear_table("items");
		frm.refresh_field('items');

        frm.clear_table("raw_items");
		frm.refresh_field('raw_items');
        frm.call({
			method:'set_data_in_items',
			doc:frm.doc,
		})

    }
});


frappe.ui.form.on("Job Work Receipt", {
    setup: function (frm) {
        frm.set_query("source_warehouse", "return_items", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            
            return {
                filters: 
                    [["Warehouse", "company", '=', frm.doc.company]]//'rejection_type': d.rejection_type
                
            };
        });

        frm.set_query("source_warehouse", "return_raw_items_details", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            
            return {
                filters: 
                    [["Warehouse", "company", '=', frm.doc.company] ]//'rejection_type': d.rejection_type
                
            };
        });





        frm.set_query("set_warehouse", function () { // Replace with the name of the link field
            return {
                filters: [
                    ["Warehouse", "company", '=', frm.doc.company] ,// Replace with your actual filter criteria
                    
                ]
            };
        });

        frm.set_query("set_from_warehouse", function () { // Replace with the name of the link field
            return {
                filters: [
                    ["Warehouse", "company", '=', frm.doc.company] ,// Replace with your actual filter criteria
                    
                ]
            };
        });

        frm.set_query("return_against", function () { // Replace with the name of the link field
            return {
                filters: [
                    ["Job Work Receipt", "customer", '=', frm.doc.customer] ,// Replace with your actual filter criteria
                    ["Job Work Receipt", "docstatus", '=', 1],
                    ["Job Work Receipt", "is_return", '=', 0],
                ]
            };
        });

        frm.set_query("order_type", function () { // Replace with the name of the link field
            return {
                filters: [
                    ["DocType", "name", 'in', ["Blanket Order", "Sales Order"]] // Replace with your actual filter criteria
                ]
            };
        });


        frm.set_query("order_no", function () { // Replace with the name of the link field
            if (frm.doc.order_type == "Blanket Order") {
                return {

                    filters: [
                        ["Blanket Order", "blanket_order_type", '=', 'Selling'],
                        ["Blanket Order", "customer", '=', frm.doc.customer] ,// Replace with your actual filter criteria
                        ["Blanket Order", "company", '=', frm.doc.company]
                    ]
                };
            }
            if (frm.doc.order_type == "Sales Order") {
                return {

                    filters: [
                        ["Sales Order", "customer", '=', frm.doc.customer], // Replace with your actual filter criteria
                        ["Sales Order", "company", '=', frm.doc.company],
                        ["Sales Order", "docstatus", '=', 1],
                    ]
                };
            }
        });
    }
});


// ============================================================= Job Work Receipt Item ================================================= 


frappe.ui.form.on('Job Work Receipt Item', {
    item_code: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (frm.doc.set_warehouse) {
            frappe.model.set_value(child.doctype, child.name, 'warehouse', frm.doc.set_warehouse);
        }
        frm.refresh_field('items');
        frm.clear_table("raw_items");
		frm.refresh_field('raw_items');
        frm.call({
			method:'set_data_in_raw_items',
			doc:frm.doc,
		})
    }
});

frappe.ui.form.on('Job Work Receipt Item', {
    qty: function(frm) {
        frm.call({
			method:'set_req_qty_in_raw_table',
			doc:frm.doc,
		})
    }
});

// ============================================================= Return Job Work Receipt Item ================================================= 




frappe.ui.form.on('Return Job Work Receipt Item', {
    as_it_is: function (frm) {
        frm.clear_table("return_raw_items_details");
		frm.refresh_field('return_raw_items_details');
        frm.call({
            method: 'finish_total_quentity_calculate',
            doc: frm.doc,
        })


    }
});

frappe.ui.form.on('Return Job Work Receipt Item', {
    cr_rejection: function (frm) {
        frm.clear_table("return_raw_items_details");
		frm.refresh_field('return_raw_items_details');
        frm.call({
            method: 'finish_total_quentity_calculate',
            doc: frm.doc,
        })


    }
});
frappe.ui.form.on('Return Job Work Receipt Item', {
    mr_rejection: function (frm) {
        frm.clear_table("return_raw_items_details");
		frm.refresh_field('return_raw_items_details');
        frm.call({
            method: 'finish_total_quentity_calculate',
            doc: frm.doc,
        })


    }
});
frappe.ui.form.on('Return Job Work Receipt Item', {
    other_rejection: function (frm) {
        frm.clear_table("return_raw_items_details");
		frm.refresh_field('return_raw_items_details');
        frm.call({
            method: 'finish_total_quentity_calculate',
            doc: frm.doc,
        })


    }
});

frappe.ui.form.on('Return Job Work Receipt Item', {
    return_quantity: function (frm) {
        frm.clear_table("return_raw_items_details");
		frm.refresh_field('return_raw_items_details');
        frm.call({
            method: 'finish_total_quentity_calculate',
            doc: frm.doc,
        })


    }
});


