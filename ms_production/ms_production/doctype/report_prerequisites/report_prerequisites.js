// Copyright (c) 2024, Abhishek Chougule and contributors
// For license information, please see license.txt

frappe.ui.form.on('Report Prerequisites', {
	total_working_days_in_month: function(frm) {
		if(frm.doc.total_working_days_in_month>31)
		{
			frappe.throw("Working days can not be greater than 31 Days")
		}
	},
	available_time_per_day: function(frm) {
		if(frm.doc.available_time_per_day>24)
		{
			frappe.throw("Available Time Per Day can not be greater than 24 Hours")
		}
	},
	planned__downtime_per_day: function(frm) {
		if(frm.doc.planned__downtime_per_day>24)
		{
			frappe.throw("Planned Downtime Time Per Day can not be greater than 24 Hours")
		}
		if(frm.doc.total_available_hours_per_day)
		{
			frm.doc.available_time_per_day=frm.doc.total_available_hours_per_day-frm.doc.planned__downtime_per_day
			frm.refresh_field("available_time_per_day")
		}
	},
	total_available_hours_per_day: function(frm) {
		if(frm.doc.total_available_hours_per_day>24)
		{
			frappe.throw("Total Available Hours Per Day can not be greater than 24 Hours")
		}
		if(frm.doc.planned__downtime_per_day)
		{
			frm.doc.available_time_per_day=frm.doc.total_available_hours_per_day-frm.doc.planned__downtime_per_day
			frm.refresh_field("available_time_per_day")
		}
	}
});
