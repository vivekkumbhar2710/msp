// Copyright (c) 2024, Abhishek Chougule and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Machine Shop OEE"] = {
	"filters": [
		{
			fieldname: "company",
			fieldtype: "Link",
			label: "Company",
			options: "Company",
			default: frappe.defaults.get_user_default('company')
		},
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: "From Date",
			default:frappe.datetime.add_days(frappe.datetime.get_today(), -30),
			reqd: 1
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: "To Date",
			default:frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "machine",
			fieldtype: "Link",
			label: "Machine",
			options: "Machine",
			
		},
	]
};
