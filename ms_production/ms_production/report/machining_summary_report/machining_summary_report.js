// Copyright (c) 2023, Abhishek Chougule and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Machining Summary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"options": "Company",
			'reqd':1,
		},
		{
			"fieldname": "month",
			"fieldtype": "Select",
			"label": "Month",
			"options": ["January","February","March","April","May","June","July","August","September","October","November","December"],
			'reqd':1,
			'default': 'December',
		},
		{
			"fieldname": "year",
			"fieldtype": "Select",
			"label": "Year",
			'reqd':1,
			"options": [2023,2024,2025,2026,2027],

		},
		{
			"fieldname": "item_code",
			"fieldtype": "Link",
			"label": "Item Code",
			"options": "Item",
			
		},
		{
			"fieldname": "include_uom",
			"fieldtype": "Link",
			"label": "Include UOM",
			"options": "UOM",
			'default': 'Kg',
		},
	]
};
