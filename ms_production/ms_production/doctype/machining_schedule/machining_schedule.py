# Copyright (c) 2024, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from datetime import datetime

class MachiningSchedule(Document):

	def get_month_dates(self ,year, month_name):
		month_number = datetime.strptime(month_name, "%B").month
		_, last_day = calendar.monthrange(year, month_number)

		start_date = datetime(year, month_number, 1)
		end_date = datetime(year, month_number, last_day)

		return start_date, end_date

	@frappe.whitelist()
	def method_after_item_group(self):
		self.set_items_in_IMS()
		self.set_items_in_MSD()
	
	@frappe.whitelist()
	def set_items_in_IMS(self):
		if self.item_group:
			if self.item_group == 'All Item Groups':
				filters = {'custom_company': self.company ,'disabled': 0}
			else:
				filters ={ "item_group" : self.item_group ,'custom_company': self.company , 'disabled': 0}

			doc = frappe.get_all( "Item" ,filters = filters ,fields = ["name" , "item_name"])
			for d in doc:
				vtl=set_data_machine_types(d.name,self.company ,"VTL")
				cnc=set_data_machine_types(d.name,self.company ,"CNC")
				vmc=set_data_machine_types(d.name,self.company,'VMC')
				sgm=set_data_machine_types(d.name,self.company ,"SGM")
				self.append("item_machining_schedule",{
													'item_code': d.name,
													'item_name': d.item_name,
													'opening_stock':get_all_available_quantity(d.name,),
													'vtl':vtl,
													'cnc':cnc,
													'vmc':vmc,
													'sgm':sgm,
													},),
	
	@frappe.whitelist()
	def set_items_in_MSD(self):
		if self.item_group:
			doc = frappe.get_all( "Machine Type"  ,fields = ["name",])
			for d in doc:
				self.append("machining_schedule_details",{
													'machine_type': d.name,
													},),
	@frappe.whitelist()
	def method_on_refresh(self):
		self.set_estimated_cycle_time()
		self.set_data_in_MSD()
	
	@frappe.whitelist()
	def set_estimated_cycle_time(self):
		item_machining_schedule = self.get("item_machining_schedule")
		for i in item_machining_schedule:
			i.vtl = set_data_machine_types(i.item_code,self.company ,"VTL")
			i.cnc = set_data_machine_types(i.item_code,self.company ,"CNC")
			i.vmc = set_data_machine_types(i.item_code,self.company,'VMC')
			i.sgm = set_data_machine_types(i.item_code,self.company ,"SGM")

			if i.schedule_quantity:
				

				i.vtl_time_in_min = i.vtl * i.schedule_quantity
				i.cnc_time_in_min = i.cnc * i.schedule_quantity
				i.vmc_time_in_min = i.vmc * i.schedule_quantity
				i.sgm_time_in_min = i.sgm * i.schedule_quantity


	@frappe.whitelist()
	def set_data_in_MSD(self):
		machining_schedule_details = self.get("machining_schedule_details")
		for d in machining_schedule_details:
			booked = self.calculating_total_weight("item_machining_schedule" ,str(d.machine_type.lower()))
			d.booked = ((booked/60)/4)/22.50
			if d.booked and d.total_working_days:
				d.percentage=(d.booked/d.total_working_days)*100

	@frappe.whitelist()
	def calculating_total_weight(self,child_table ,total_field):
		casting_details = self.get(child_table)
		total_pouring_weight = 0
		for i in casting_details:
			field_data = i.get(total_field)
			if field_data:
				total_pouring_weight = total_pouring_weight + field_data
		return total_pouring_weight
			

		# frappe.msgprint(str(p))


		# frappe.msgprint(str(total_qty_of_items))
		# mct =frappe.get_value('Material Cycle Time',{'item':item_code ,'company':company} ,'name', order_by='from_date desc')
		# if mct:
		# 	mtable = frappe.get_all("Machine Item", filters={"parent": mct,}, fields=["machine_type","cycle_time"])
		# 	frappe.msgprint(str(mtable))


	# def before_save(self):
	# 	start_date , end_date = self.get_month_dates( int(self.year),self.month)
	# 	frappe.msgprint(str(start_date) +"====="+str(end_date))

def get_all_available_quantity(item_code):
	result = frappe.get_all("Bin", filters={"item_code": item_code,}, fields=["actual_qty"])
	return sum(r.actual_qty for r in result) if result else 0

def set_data_machine_types(item_code , company ,machine_type):
	total_qty_of_items = frappe.db.sql("""
											SELECT b.machine_type, SUM(b.cycle_time) 'cycle_time'
											FROM `tabMaterial Cycle Time` a
											LEFT JOIN `tabMachine Item` b ON a.name = b.parent
											WHERE a.item = %s AND a.company = %s AND b.machine_type = %s
											
										""",(item_code ,company ,machine_type ),as_dict="True")


	# frappe.msgprint(str(total_qty_of_items[0].cycle_time ))

	return total_qty_of_items[0].cycle_time if total_qty_of_items[0].cycle_time else 0