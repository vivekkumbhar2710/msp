# Copyright (c) 2023, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters: filters={}

	columns, data = [], []

	columns = get_columns()
	data = get_data(filters)

	if not data:
		frappe.msgprint('🙄😵 NO RECORD FOUND 😵🙄')
		return columns, data
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "item_code",
			"fieldtype": "Link",
			"label": "Item",
			"options": "Item",
		},
		{
			"fieldname": "item_name",
			"fieldtype": "data",
			"label": "Item_name",
		},
		{
			"fieldname": "ok_qty",
			"fieldtype": "float",
			"label": "OK Produced Qty",
		},
		{
			"fieldname": "cr_qty",
			"fieldtype": "float",
			"label": "CR Qty",
		},
		{
			"fieldname": "cr_per",
			"fieldtype": "float",
			"label": "CR in %",
		},
		{
			"fieldname": "mr_qty",
			"fieldtype": "float",
			"label": "MR Qty",
		},
		{
			"fieldname": "mr_per",
			"fieldtype": "float",
			"label": "MR in %",
		},
		{
			"fieldname": "rw_qty",
			"fieldtype": "float",
			"label": "RW Qty",
		},
		{
			"fieldname": "rw_per",
			"fieldtype": "float",
			"label": "RW in %",
		},
		{
			"fieldname": "total_rejection",
			"fieldtype": "float",
			"label": "Total Rejection",
		},
		{
			"fieldname": "total_qty",
			"fieldtype": "float",
			"label": "Total Quantity",
		},
	]


def get_data(filters):
	
	date_filter , company_filter , item_code_filter = get_conditions(filters)
	production_filter = {**date_filter , **company_filter}
	

	production_list = get_production_list(production_filter)
	production_id_filter = {'parent':['in',production_list]}
	# frappe.msgprint(str(item_code_filter))
	if item_code_filter:
		item_list = [item_code_filter['item_code']]
	else:
		item_list = get_item_list(production_id_filter)


	result_list = []

	for i in item_list:
		item_filter = {"item":i}
		qty_details_filter = {**item_filter , **production_id_filter}
		qty_details = frappe.get_all ("Qty Details",fields = ['ok_qty','cr_qty','mr_qty','rw_qty','total_qty'],filters = qty_details_filter,)
		ok_qty , cr_qty , mr_qty ,rw_qty , total_qty = 0 ,0, 0, 0, 0
		for j in qty_details:
			ok_qty = ok_qty + j.ok_qty
			cr_qty = cr_qty + j.cr_qty
			mr_qty = mr_qty + j.mr_qty
			rw_qty = rw_qty + j.rw_qty
		total_qty = ok_qty + cr_qty + mr_qty + rw_qty
		cr_per = (cr_qty / total_qty) * 100
		mr_per = (mr_qty / total_qty) * 100
		rw_per = (rw_qty / total_qty) * 100

		total_rejection = cr_qty + mr_qty + rw_qty
		item_dict ={
					'item_code':i,
					'item_name': frappe.get_value('Item', i ,'item_name'),
					'ok_qty': ok_qty ,
					'cr_qty': cr_qty,
					'mr_qty': mr_qty ,
					'rw_qty': rw_qty,
					'cr_per': round(cr_per,2) ,
					'mr_per': round(mr_per,2) ,
					'rw_per': round(rw_per,2) ,
					'total_rejection':total_rejection ,
					'total_qty': total_qty, }
		
		result_list.append(item_dict)

	
	# frappe.msgprint(str(qty_details))
	return result_list 

def get_conditions(filters):
	date_filter ={}
	company_filter = {}
	item_code_filter = {}

	from_date = filters.get('from_date')
	to_date =  filters.get('to_date')
	company = filters.get('company')
	item_code =  filters.get('item_code')


	if from_date or to_date:
		date_filter = {'date': ['between',[ filters.get('from_date', '2001-01-01'), filters.get('to_date', '2100-01-01')]]}

	if company :
		company_filter = {'company':company}

	if item_code :
		item_code_filter = {'item_code':item_code}
		
			
	return date_filter , company_filter , item_code_filter

def get_production_list(production_filters):
	return_list = []
	production = frappe.get_all ("Production",fields = ['name',],filters = production_filters,)
	if production:
		for p in production:
			return_list.append(p.name)

	return return_list

def get_item_list(parent_filter):
	return_list = []
	items = frappe.get_all("Items Production",fields = ['item',],filters = parent_filter, distinct="item")
	if items:
		for i in items:
			return_list.append(i.item)

	return return_list

