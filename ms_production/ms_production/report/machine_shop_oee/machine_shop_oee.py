# Copyright (c) 2024, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime,timedelta
def execute(filters=None):
	if not filters: filters={}
	columns, data =[],[]
	columns=get_column()
	data=get_data(filters)
	if not data:
		frappe.msgprint('NO RECORD FOUND')
		return columns, data

	return columns, data



def get_column():
    return[
			{
			"fieldname": "machine_id",
			"fieldtype": "Link",
			"label": "Machine Id",
			"options": "Machine",
			},
			{
			"fieldname": "machine_name",
			"fieldtype": "Data",
			"label": "Machine Name",
			},
			{
			"fieldname": "availability",
			"fieldtype": "Float",
			"label": "Availability",
			},
			{
			"fieldname": "performance",
			"fieldtype": "Float",
			"label": "Performance",
			},
			{
			"fieldname": "quality",
			"fieldtype": "Float",
			"label": "Quality",
			},
			{
			"fieldname": "oee",
			"fieldtype": "Float",
			"label": "OEE",
			},
	]


    
def get_data(filters):
	filter_dict1 = {}
	company_name=""
	machine_name=""
	to_date=""
	from_date=""
	total_days=0
 	
	company_name = filters.get('company')
	machine_name=filters.get('machine')
	to_date = filters.get('to_date')
	from_date = filters.get('from_date')
 
	if company_name:
		filter_dict1["company"]=company_name

	if machine_name:
		filter_dict1["name"]=machine_name
	
	if to_date and from_date:
		to_date = datetime.strptime(to_date, "%Y-%m-%d")
		from_date = datetime.strptime(from_date, "%Y-%m-%d")

		if from_date > to_date:
			frappe.throw("From date cannot be greater than To Date")
		else:
			total_days = (to_date-from_date).days+1
	
 
	report_data_li=[]
	machine_doc = frappe.get_all("Machine", filters=filter_dict1, fields=['name', 'machine_name'])
	for i in machine_doc:
		available,qty,performance=0,0,0
		available_qty_result = get_availability(i.name, from_date, to_date)
		if available_qty_result is not None:
			available, qty, performance = available_qty_result
		doc_elemet_item={}
		doc_elemet_item["machine_id"]=i.name
		doc_elemet_item["machine_name"]=i.machine_name
		doc_elemet_item["availability"]=available
		doc_elemet_item["performance"]=performance
		doc_elemet_item["quality"]=qty
		doc_elemet_item["oee"]=available*performance*qty
		report_data_li.append(doc_elemet_item)	
	return report_data_li

	
def get_availability(machinde_id,from_date,to_date):
	production_li = frappe.get_all("Production", filters={"docstatus": 1, "date": ['between', [from_date, to_date]]}, fields=["name","required_time"])
	stop_time=0
	total_count=0
	rejected_count=0
	good_count=0
	quality=0
	planned_production_time=0
	ideal_cycle_time=0
	perofrmance=0
	availability=0
	count=0
	for i in production_li:
		flag=True
		flag1=True
		downtime_reason_doc=frappe.get_all("Downtime Reason Details",{"parent":i.name,"machine":machinde_id},["time"])
		for j in downtime_reason_doc:
			stop_time+=j.time
   
		qty_details_doc=frappe.get_all("Qty Details",filters={"parent":i.name,"machine":machinde_id},fields=["total_qty","cr_qty","mr_qty","rw_qty"])
		for j in qty_details_doc:
			total_count+=j.total_qty
			if(flag):
				planned_production_time+=i.required_time
				flag=False
			rejected_count=rejected_count+(j.cr_qty+j.mr_qty+j.rw_qty)

		item_operation_doc=frappe.get_all("Item operations",filters={"parent":i.name,"machine":machinde_id},fields=["cycle_time"])
		for j in item_operation_doc:
			ideal_cycle_time+=j.cycle_time
			if(flag1):
				count+=1
				flag1=False
   
	good_count=total_count-rejected_count
	
	if(total_count):
		quality=(good_count/total_count)*100
	run_time=planned_production_time-stop_time
	if(count):
		ideal_cycle_time=ideal_cycle_time/count
	if(run_time):
		perofrmance=((ideal_cycle_time*total_count)/run_time)*100
	
	if(planned_production_time):
		availability=((run_time/planned_production_time)*100)
 
	return availability,quality,perofrmance
	