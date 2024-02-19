# Copyright (c) 2023, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe
import calendar
from datetime import datetime
from frappe import _
from frappe.desk.query_report import run


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
			"fieldname": "opening_stock",
			"fieldtype": "data",
			"label": "Opening Stock",
		},
		{
			"fieldname": "delivery_qty",
			"fieldtype": "float",
			"label": "Delivered QTY",
		},
		{
			"fieldname": "sales_qty",
			"fieldtype": "float",
			"label": "Sales Qty",
		},
		{
			"fieldname": "scheduled_qty",
			"fieldtype": "float",
			"label": "Scheduled Qty",
		},
		{
			"fieldname": "scheduled_percentage",
			"fieldtype": "float",
			"label": "% Copmiance with Sch",
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
		{
			"fieldname": "job_work_inward",
			"fieldtype": "float",
			"label": "Job Work Inward",
		},
		{
			"fieldname": "purchase_inward",
			"fieldtype": "float",
			"label": "Purchase Inward",
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
		cr_per=0
		mr_per=0
		rw_per=0
		if total_qty != 0:
			cr_per = (cr_qty / total_qty) * 100
			mr_per = (mr_qty / total_qty) * 100
			rw_per = (rw_qty / total_qty) * 100

		total_rejection = cr_qty + mr_qty + rw_qty
		delivery_qty = get_delivery_qty(i,filters)
		scheduled_qty = get_scheduled_qty(i,filters)
		sales_qty = get_sales_qty(i,filters)
		scheduled_percentage = 0
		if scheduled_qty:
			scheduled_percentage = round((delivery_qty/scheduled_qty)*100 , 2)
		item_dict ={
					'item_code':i,
					'item_name': frappe.get_value('Item', i ,'item_name'),
					'opening_stock': get_all_available_quantity(i,filters),
					'delivery_qty': delivery_qty,
					'scheduled_qty': scheduled_qty,
					'sales_qty':sales_qty,
					'scheduled_percentage':scheduled_percentage,
					'ok_qty': ok_qty ,
					'cr_qty': cr_qty,
					'mr_qty': mr_qty ,
					'rw_qty': rw_qty,
					'cr_per': round(cr_per,2) ,
					'mr_per': round(mr_per,2) ,
					'rw_per': round(rw_per,2) ,
					'total_rejection':total_rejection ,
					'total_qty': total_qty,
					"job_work_inward": get_job_work_qty(i,filters),
					"purchase_inward":get_purchase_inward_qty(i,filters),
     
     	}
		
		result_list.append(item_dict)

	
	# frappe.msgprint(str(qty_details))
	return result_list 

def get_conditions(filters):
	date_filter ={}
	company_filter = {}
	item_code_filter = {}

	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
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


def get_all_available_quantity(item_code,filters): 
	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	company_name=filters.get('company')
 
	fiscal_year = frappe.db.sql("""
		SELECT name 
		FROM `tabFiscal Year`
		ORDER BY creation ASC
		LIMIT 1
			""", as_dict=True)
 
	warehouse_list=frappe.db.sql("""
								select name from `tabWarehouse` where company="{0}"
                              """.format(company_name),as_dict=True)
	opn_sum = 0
	for warehouse in warehouse_list:
		opening_balance=frappe.db.sql("""
								SELECT qty_after_transaction 
								FROM `tabStock Ledger Entry` 
								WHERE posting_date < '{0}' 
									AND warehouse = '{1}' 
									AND item_code = '{2}' 
									AND fiscal_year = '{3}' 
									AND company = '{4}' 
								ORDER BY creation DESC 
								LIMIT 1
                              """.format(from_date,warehouse.name,item_code,fiscal_year[0].name,company_name),as_dict=True)
		if opening_balance:
			opn_sum += opening_balance[0].qty_after_transaction
	
	return opn_sum


def get_delivery_qty(item_code ,filters):
	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	qty = frappe.db.sql("""
							SELECT b.item_code, SUM(b.qty) 'qty' 
							FROM `tabDelivery Note` a
							LEFT JOIN `tabDelivery Note Item` b ON a.name = b.parent
							WHERE a.posting_date BETWEEN %s AND %s AND b.item_code = %s AND b.docstatus = 1
						""",(from_date ,to_date ,item_code),as_dict="True")

	return qty[0].qty if qty[0].qty else 0


def get_job_work_qty(item_code ,filters):
	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	qty = frappe.db.sql("""
							SELECT b.raw_item_code, SUM(b.required_qty) 'qty' 
							FROM `tabJob Work Receipt` a
							LEFT JOIN `tabJob Work Receipt Raw Item` b ON a.name = b.parent
							WHERE a.posting_date BETWEEN %s AND %s AND b.raw_item_code = %s AND b.docstatus = 1
						""",(from_date ,to_date ,item_code),as_dict="True")

	return qty[0].qty if qty[0].qty else 0


def get_purchase_inward_qty(item_code ,filters):
	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	qty = frappe.db.sql("""
							SELECT b.item_code, SUM(b.qty) 'qty' 
							FROM `tabPurchase Receipt` a
							LEFT JOIN `tabPurchase Receipt Item` b ON a.name = b.parent
							WHERE a.posting_date BETWEEN %s AND %s AND b.item_code = %s AND b.docstatus = 1
						""",(from_date ,to_date ,item_code),as_dict="True")

	return qty[0].qty if qty[0].qty else 0


def get_sales_qty(item_code ,filters):
	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	qty = frappe.db.sql("""
							SELECT b.item_code, SUM(b.qty) 'qty' 
							FROM `tabSales Invoice` a
							LEFT JOIN `tabSales Invoice Item` b ON a.name = b.parent
							WHERE a.posting_date BETWEEN %s AND %s AND b.item_code = %s AND b.docstatus = 1
						""",(from_date ,to_date ,item_code),as_dict="True")

	return qty[0].qty if qty[0].qty else 0

def get_month_dates(year, month_name):
		month_number = datetime.strptime(month_name, "%B").month
		_, last_day = calendar.monthrange(year, month_number)

		start_date = datetime(year, month_number, 1)
		end_date = datetime(year, month_number, last_day)

		return start_date, end_date

def get_scheduled_qty(item_code,filters):
	machining_schedule =  frappe.get_value("Machining Schedule",{'company':filters.get('company'),'month':filters.get('month'),'year':filters.get('year')},"name")
	if machining_schedule:
		qty =  frappe.get_value("Item Machining Schedule",{'parent':machining_schedule,'item_code':item_code},"schedule_quantity")
		return qty if qty else 0
	return 0


# def get_opening_stock(item_code, month):
#     opening_stock = 0

#     # Get the first day of the month
#     first_day_of_month = frappe.utils.data.get_first_day(month)

#     # Query Stock Ledger Entries to get the opening stock
#     stock_ledger_entries = frappe.get_all(
#         'Stock Ledger Entry',
#         filters={
#             'item_code': item_code,
#             'posting_date': ('<', first_day_of_month),
#         },
#         fields=['actual_qty', 'voucher_type', 'posting_date'],
#         order_by='posting_date DESC, name DESC',
#         limit=1
#     )

#     if stock_ledger_entries:
#         opening_stock = stock_ledger_entries[0]['actual_qty']

#         # Adjust for the sign based on the voucher type
#         # if stock_ledger_entries[0]['voucher_type'] == 'Stock Entry':
#         #     opening_stock *= -1

#     return opening_stock