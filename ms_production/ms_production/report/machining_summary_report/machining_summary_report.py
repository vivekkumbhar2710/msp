# Copyright (c) 2023, Abhishek Chougule and contributors
# For license information, please see license.txt
from frappe.query_builder.functions import Coalesce, CombineDatetime
import frappe
import calendar
from datetime import datetime
from frappe import _
from frappe.desk.query_report import run



def execute(filters=None):
	if not filters: filters={}
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)

	if not data:
		frappe.msgprint('🙄😵 NO RECORD FOUND 😵🙄')
		return columns, data
	return columns, data


def add_column(fieldname,fieldtype,label,link_doc=None,uom_status=False, uom=None):
	column_li=[]
	if(link_doc!=None):
		column = {
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"label": label,
			"options":link_doc
		}
	else:
		column = {
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"label": label,
		}
	column_li.append(column)
	if(uom_status):
		temp=str(label)+" In "+str(uom)
		column = {
			"fieldname":temp,
			"fieldtype": "data",
			"label": temp,
		}
		column_li.append(column)
	return column_li
 

def get_columns(filters):
    column_list = []
    uom_status, uom = get_uom_status(filters)
    column_list.extend(add_column("item_code","Link","Item","Item"))
    column_list.extend(add_column("item_name", "Data", "Item Name"))
    column_list.extend(add_column("opening_stock", "Float", "Opening Stock",None, uom_status, uom))
    column_list.extend(add_column("purchase_inward", "Float", "Purchase Inward",None, uom_status, uom))
    column_list.extend(add_column("job_work_inward", "Float", "Job Work Inward",None, uom_status, uom))
    column_list.extend(add_column("scheduled_qty", "Float", "Scheduled Qty",None, uom_status, uom))
    column_list.extend(add_column("scheduled_percentage", "Float", "% Compliance with Sch"))
    column_list.extend(add_column("ok_qty", "Float", "OK Produced Qty",None, uom_status, uom))
    column_list.extend(add_column("ok_qty_per", "Float", "OK Produced Qty In %"))
    column_list.extend(add_column("cr_qty", "Float", "CR Qty",None, uom_status, uom))
    column_list.extend(add_column("cr_per", "Float", "CR In %"))
    column_list.extend(add_column("mr_qty", "Float", "MR Qty",None, uom_status, uom))
    column_list.extend(add_column("mr_per", "Float", "MR In %"))
    column_list.extend(add_column("rw_qty", "Float", "RW Qty",None, uom_status, uom))
    column_list.extend(add_column("rw_per", "Float", "RW In %"))
    column_list.extend(add_column("total_rejection", "Float", "Total Rejection",None,uom_status, uom))
    column_list.extend(add_column("total_qty", "Float", "Total Quantity",None, uom_status, uom))
    column_list.extend(add_column("delivery_qty", "Float", "Delivered Qty",None, uom_status, uom))
    column_list.extend(add_column("sales_qty", "Float", "Sales Qty",None, uom_status, uom))
    column_list.extend(add_column("closing_bal", "Float", "Closing Balance",None, uom_status, uom))
    return column_list



def get_data(filters):
	date_filter , company_filter , item_code_filter = get_conditions(filters)
	production_filter = {**date_filter , **company_filter}
	production_list = get_production_list(production_filter)
	production_id_filter = {'parent':['in',production_list]}
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
		ok_qty_per=0
		if(ok_qty):
			ok_qty_per=round(((ok_qty/total_qty)*100),2)
   
		item_dict={}
		uom_status,uom=get_uom_status(filters)
  
		item_dict['item_code']=i
  
		item_dict['item_name']=frappe.get_value('Item', i ,'item_name')
  
		item_dict['opening_stock']=get_all_available_quantity(i,filters)
  
		if uom_status:
			temp="Opening Stock In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['opening_stock'],uom)
   
		item_dict['delivery_qty']=delivery_qty
		if uom_status:
			temp="Delivered Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['delivery_qty'],uom)
  
		item_dict['scheduled_qty']=scheduled_qty
		if uom_status:
			temp="Scheduled Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['scheduled_qty'],uom)
   
   
		item_dict['sales_qty']=sales_qty
		if uom_status:
			temp="Sales Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['sales_qty'],uom)
   
		item_dict['scheduled_percentage']=scheduled_percentage
  
		item_dict['ok_qty']=ok_qty
		if uom_status:
			temp="OK Produced Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['ok_qty'],uom)
   
		item_dict['ok_qty_per']=ok_qty_per
		
		item_dict['cr_qty']=cr_qty
		if uom_status:
			temp="CR Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['cr_qty'],uom)
   
		item_dict['mr_qty']=mr_qty
		if uom_status:
			temp="MR Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['mr_qty'],uom)
  
		item_dict['rw_qty']=rw_qty
		if uom_status:
			temp="RW Qty In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['rw_qty'],uom)
  
		item_dict['cr_per']=round(cr_per,2)
		item_dict['mr_per']=round(mr_per,2)
		item_dict['rw_per']=round(rw_per,2) 
		item_dict['total_rejection']=total_rejection
		if uom_status:
			temp="Total Rejection In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['total_rejection'],uom)
  
		item_dict['total_qty']=total_qty
		if uom_status:
			temp="Total Quantity In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['total_qty'],uom)
  
		item_dict['job_work_inward']=get_job_work_qty(i,filters)
		if uom_status:
			temp="Job Work Inward In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['job_work_inward'],uom)
   
		item_dict['purchase_inward']=get_purchase_inward_qty(i,filters)
		if uom_status:
			temp="Purchase Inward In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['purchase_inward'],uom)
   
		item_dict['closing_bal']=get_closing_balance(i,filters)
		if uom_status:
			temp="Closing Balance In "+str(uom)
			item_dict[temp]=get_uom_qty(i,item_dict['closing_bal'],uom)

		result_list.append(item_dict)
	return result_list 


def get_conditions(filters):
	date_filter ={}
	company_filter = {}
	item_code_filter = {}

	from_date ,to_date= get_month_dates(int(filters.get('year')), filters.get('month'))
	company = filters.get('company')
	item_code =  filters.get('item_code')
	if from_date or to_date:
		from_date = from_date.strftime("%Y-%m-%d")
		to_date = to_date.strftime("%Y-%m-%d")
		date_filter={'date': ['between',[ from_date, to_date ]]}
	if company :
		company_filter = {'company':company}

	if item_code :
		item_code_filter = {'item_code':item_code}
	return date_filter , company_filter , item_code_filter

def get_production_list(production_filters):
	docfilter={"docstatus":1}
	production_filters.update(docfilter)
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


def get_all_available_quantity(item_code, filters): 
	from_date, to_date = get_month_dates(int(filters.get('year')), filters.get('month'))
	company_name = filters.get('company')

	fiscal_year = frappe.db.sql("""
		SELECT name 
		FROM `tabFiscal Year`
		ORDER BY creation ASC
		LIMIT 1
	""", as_dict=True)

	warehouse_list = frappe.db.sql("""
		SELECT name FROM `tabWarehouse` WHERE company="{0}"
	""".format(company_name), as_dict=True)

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
									AND is_cancelled='{5}'
								ORDER BY creation DESC 
								LIMIT 1
								""".format(from_date,warehouse.name,item_code,fiscal_year[0].name,company_name,False),as_dict=True)
		if opening_balance:
			opn_sum += opening_balance[0].qty_after_transaction
	return opn_sum


def get_closing_balance(item_code, filters):
	from_date, to_date = get_month_dates(int(filters.get('year')), filters.get('month'))
	company_name = filters.get('company')

	fiscal_year = frappe.db.sql("""
		SELECT name 
		FROM `tabFiscal Year`
		ORDER BY creation ASC
		LIMIT 1
	""", as_dict=True)

	warehouse_list = frappe.db.sql("""
		SELECT name FROM `tabWarehouse` WHERE company="{0}"
	""".format(company_name), as_dict=True)

	closing_sum = 0
	for warehouse in warehouse_list:
		closing_bal=frappe.db.sql("""
								SELECT qty_after_transaction 
								FROM `tabStock Ledger Entry` 
								WHERE posting_date < '{0}' 
									AND warehouse = '{1}' 
									AND item_code = '{2}' 
									AND fiscal_year = '{3}' 
									AND company = '{4}' 
									AND is_cancelled='{5}'
								ORDER BY creation DESC 
								LIMIT 1
								""".format(to_date,warehouse.name,item_code,fiscal_year[0].name,company_name,False),as_dict=True)
		if closing_bal:
			closing_sum += closing_bal[0].qty_after_transaction
	return closing_sum



def get_uom_status(filters):
	uom=filters.get("include_uom")
	uom_status=False
	if(uom):
		uom_status=True
	return uom_status,uom


def get_uom_qty(item_code,qty,convert_to_uom):
	default_uom=frappe.get_value("Item",{'name':item_code},'stock_uom')
	if(default_uom):
		new_uom_factor=0
		default_uom_factor=frappe.get_value("UOM Conversion Detail",{'parent':item_code,"uom":default_uom},'conversion_factor')
		if(default_uom_factor):
			new_uom_factor=frappe.get_value("UOM Conversion Detail",{'parent':item_code,"uom":convert_to_uom},'conversion_factor')
			if(new_uom_factor):
				return round(qty/new_uom_factor,2)
	return "Weight Not Present"


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
	machining_schedule =  frappe.get_value("Machining Schedule",{'company':filters.get('company'),'month':filters.get('month'),'year':filters.get('year'),'docstatus':1},"name")
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