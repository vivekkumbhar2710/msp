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
		frappe.msgprint('🙄😵 NO RECORD FOUND 😵🙄')
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
			"fieldname": "actual_hours",
			"fieldtype": "Float",
			"label": "Actual Hours",
			},
			{
			"fieldname": "working_hours",
			"fieldtype": "Float",
			"label": "Working Hours",
			},
   			{
			"fieldname": "eared_hours",
			"fieldtype": "Float",
			"label": "Eared Hours",
			},
			{
			"fieldname": "machine_utilization_per",
			"fieldtype": "Float",
			"label": "Machine Utilizatioin %",
			},
			{
			"fieldname": "eared_hours_per",
			"fieldtype": "Float",
			"label": "Eared Hours %",
			},
			{
			"fieldname": "oee_per",
			"fieldtype": "Float",
			"label": "OEE %",
			},
	]
    
def get_data(filters):
	filter_dict1 = {}
	filter_dict2 = {}
	company_name=""
	machine_name=""
	to_date=""
	from_date=""
 
	company_name = filters.get('company')
	machine_name=filters.get('machine')
	to_date = filters.get('to_date')
	from_date = filters.get('from_date')
 
	if company_name:
		filter_dict1["company"] = company_name
	
	if machine_name:
		filter_dict1["name"] = machine_name
  
	filter_dict2["docstatus"]=1
	if from_date or to_date:
		filter_dict2["date"]=['between',[from_date ,to_date]]
  
	total_days=0
	if to_date and from_date:
		to_date = datetime.strptime(to_date, "%Y-%m-%d")
		from_date = datetime.strptime(from_date, "%Y-%m-%d")

		if from_date > to_date:
			frappe.throw("From date cannot be greater than To Date")
		else:
			total_days = (to_date-from_date).days+1

  
	doc1 = frappe.get_all("Machine", filters=filter_dict1, fields=['name', 'machine_name'])
	doc2 = frappe.get_doc("Report Prerequisites")
	doc3= frappe.get_all("Production",filters=filter_dict2,fields=["name"])
	updated_doc=[]
	for i in doc1:
		doc_elemet_item={}
		doc_elemet_item["machine_id"]=i.name
		doc_elemet_item["machine_name"]=i.machine_name
		doc_elemet_item["actual_hours"]=total_days*doc2.available_time_per_day
		doc_elemet_item["working_hours"]=get_working_hours(doc3,i.machine_name)
		doc_elemet_item["eared_hours"]=get_eared_hours(doc3,i.machine_name)
		if(doc_elemet_item["actual_hours"]):
			doc_elemet_item["machine_utilization_per"]=doc_elemet_item["working_hours"]/doc_elemet_item["actual_hours"]*100
		if(doc_elemet_item["working_hours"]):
			doc_elemet_item["eared_hours_per"]=doc_elemet_item["eared_hours"]/doc_elemet_item["working_hours"]*100
		updated_doc.append(doc_elemet_item)	
	return updated_doc

def get_eared_hours(doc3,machine_name):
	total_eared_hours=0
	if(doc3):
		for i in doc3:
			doc4=frappe.get_all("Qty Details",filters={"parent":i.name,"machine":machine_name},fields=["earned_min"])
			for j in doc4:
				total_eared_hours=total_eared_hours+j.earned_min
	return total_eared_hours/60

def get_working_hours(doc3,machine_name):
	total_working_hours=0
	if(doc3):
		for i in doc3:
			doc4=frappe.get_all("Item operations",filters={"parent":i.name,"machine":machine_name},fields=["item"])
			if(doc4):
				for j in doc4:
					doc4=frappe.get_all("Raw Items Production",filters={"parent":i.name,"item":j.item},fields=["required_time"])
					for k in doc4:
						total_working_hours=total_working_hours+k.required_time
	return total_working_hours/60