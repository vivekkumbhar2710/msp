# Copyright (c) 2023, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def getVal(val):
	return val if val is not None else 0

class JobWorkReceipt(Document):
	
	@frappe.whitelist()
	def before_save(self):
		if self.is_return:
			self.calculating_total_return()
		else:
			self.validate_items()
			self.calculating_total_inword()

	@frappe.whitelist()
	def before_submit(self):
		if self.is_return:
			self.updated_item_before_submit()
			self.in_delivery_note()
		else:
			self.in_material_receipt()

	@frappe.whitelist()
	def before_cancel(self):
		if self.is_return:
			self.updated_item_before_cancel()
		else:
			pass



# ======================================================================================= INWORD ===============================================================================

	@frappe.whitelist()
	def set_data_in_items(self):
		if not self.is_return:
			order_type , order_no   = self.order_type , self.order_no
			if order_type and order_no:
				doctype = 'Blanket Order Item' if order_type == 'Blanket Order' else 'Sales Order Item'
				item_data = frappe.get_all(doctype , filters = {'parent' : order_no} , fields = ['item_code'])
				for i in item_data:
					if i.item_code:
						self.append("items",
											{'item_code': i.item_code,},),
		
			self.set_data_in_raw_items()

	@frappe.whitelist()
	def set_data_in_raw_items(self):
		if not self.is_return:
			items = self.get("items")
			for j in items:
				if j.item_code:
					bom_exist = frappe.get_value("Job Work Receipt BOM",j.item_code,'name')
					
					if bom_exist :
						bom = frappe.get_doc("Job Work Receipt BOM",j.item_code)
						child_bom = bom.get("job_work_bom_details")
						for k in child_bom:
							self.append("raw_items",
										{	'finished_item_code': j.item_code ,
											'raw_item_code'	: k.item_code,
											'quantity_per_finished_item': k.required_quantity,},),
					else:
						raw_item_code = frappe.get_value("Item",j.item_code,'raw_material')
						if raw_item_code:
							self.append("raw_items",
											{	'finished_item_code': j.item_code ,
												'raw_item_code'	: raw_item_code ,
												'quantity_per_finished_item':1,},),
						else:
							frappe.msgprint(f"There is no 'Raw Material'defined at Item master of Item {j.item_code}")

	@frappe.whitelist()
	def set_req_qty_in_raw_table(self):
		if not self.is_return:
			items = self.get("items")
			for j in items:
				if j.qty:
					raw_items = self.get("raw_items" , filters ={'finished_item_code': j.item_code})
					for l in raw_items:
						if l.quantity_per_finished_item:
							l.required_qty = l.quantity_per_finished_item * j.qty

			self.calculating_total_inword()

	@frappe.whitelist()
	def in_material_receipt(self):
		if not self.is_return:
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Receipt"
			se.company = self.company
			se.posting_date = self.posting_date
			se.posting_time = self.posting_time
			for p in self.get("items"):
				raw_items = self.get("raw_items" , filters ={'finished_item_code': p.item_code})
				for k in raw_items:
					se.append(
							"items",
							{
								"item_code": k.raw_item_code,
								"qty": k.required_qty,
								"t_warehouse": k.accepted_warehouse,
								"allow_zero_valuation_rate": 1
							},)
							

			se.job_work_receipt = self.name		
			se.insert()
			se.save()
			se.submit()

	@frappe.whitelist()
	def validate_items(self):
		if not self.is_return:
			for p in self.get("items"):
				p.reference_id = p.name
				raw_items = self.get("raw_items" , filters ={'finished_item_code': p.item_code})
				if raw_items:
					for d  in raw_items:
						d.reference_id = p.name
				else:
					frappe.throw(f'It Is Mandatory To Define Raw Item For Item Code "{p.item_code}".')


	@frappe.whitelist()
	def calculating_total_inword(self):
		self.finished_item_total_quantity = self.calculating_total('items','qty')
		self.raw_item_total_quantity = self.calculating_total('raw_items','required_qty')
# ======================================================================================= IS RETURN ===============================================================================
	@frappe.whitelist()
	def calculating_total_return(self):
		self.finished_item_total_quantity = self.calculating_total('return_items','return_quantity')
		self.raw_item_total_quantity = self.calculating_total('return_raw_items_details','quantity')

	@frappe.whitelist()
	def set_data_from_jwr(self):
		if self.is_return:
			return_jwr = self.get("return_against")
			for i in return_jwr:
				items = frappe.get_all("Job Work Receipt Item" , filters = {'parent':i.job_work_receipt} , fields = ['item_code','item_name','return_quantity','qty','reference_id'])
				for d in items:
					returnable_quantity =  d.qty - d.return_quantity
					self.append("return_items",
											{	'challan_reference': i.job_work_receipt ,
												'item_code': d.item_code ,
												'returnable_quantity': returnable_quantity ,
												'reference_id': d.reference_id,
												'item_name':d.item_name},),
	
	

	@frappe.whitelist()
	def finish_total_quentity_calculate(self):
		for j in self.get("return_items"):
			j.total_quantity = getVal(j.as_it_is) + getVal(j.cr_rejection) + getVal(j.mr_rejection) + getVal(j.other_rejection) + getVal(j.return_quantity)

			
			if getVal(j.total_quantity) > getVal(j.returnable_quantity):
				frappe.throw(f'Total Quantity For Item {j.item_code}-{j.item_name} is Should Not Be Greater Than Actual Required Quantity ')
		self.set_dat_in_raw_return_items_reasons()
		self.calculating_total_return()

	@frappe.whitelist()
	def set_dat_in_raw_return_items_reasons(self):
		for n in self.get("return_items"):
			if n.item_code:
				raw_items_table = frappe.get_all("Job Work Receipt Raw Item" , filters = {'reference_id' : n.reference_id }, fields = ['finished_item_code','raw_item_code','quantity_per_finished_item'])
				for i in raw_items_table:
					if n.as_it_is:
						return_type = 'As It Is (As It Is Transfer)'
						quantity = i.quantity_per_finished_item * n.as_it_is
						self.append("return_raw_items_details",
												{	'return_type' : return_type,
													'item_code': i.finished_item_code ,
													'raw_item_code': i.raw_item_code ,
													'quantity': quantity ,
													'reference_id': n.reference_id,},),
						
					if n.cr_rejection:
						return_type = 'CR (Casting Rejection)'
						quantity = i.quantity_per_finished_item * n.cr_rejection
						self.append("return_raw_items_details",
												{	'return_type' : return_type,
													'item_code': i.finished_item_code ,
													'raw_item_code': i.raw_item_code ,
													'quantity': quantity ,
													'reference_id': n.reference_id,},),
					if n.mr_rejection:
						return_type = 'MR (Machine Rejection)'
						quantity = i.quantity_per_finished_item * n.mr_rejection
						self.append("return_raw_items_details",
												{	'return_type' : return_type,
													'item_code': i.finished_item_code ,
													'raw_item_code': i.raw_item_code ,
													'quantity': quantity ,
													'reference_id': n.reference_id,},),
					if n.other_rejection:
						return_type = 'Other (Other Rejection)'
						quantity = i.quantity_per_finished_item * n.other_rejection
						self.append("return_raw_items_details",
												{	'return_type' : return_type,
													'item_code': i.finished_item_code ,
													'raw_item_code': i.raw_item_code ,
													'quantity': quantity ,
													'reference_id': n.reference_id,},),
	@frappe.whitelist()
	def updated_item_before_submit(self):
		if self.is_return:
			for n in self.get("return_items"):
				if n.item_code:
					total_quantity = getVal(n.as_it_is) + getVal(n.cr_rejection) + getVal(n.mr_rejection) + getVal(n.other_rejection) + getVal(n.return_quantity)
					return_quantity = frappe.get_value('Job Work Receipt Item', n.reference_id , 'return_quantity')
					updated_qty = return_quantity + total_quantity
					frappe.set_value('Job Work Receipt Item', n.reference_id , 'return_quantity' , updated_qty )

	@frappe.whitelist()
	def updated_item_before_cancel(self):
		if self.is_return:
			for n in self.get("return_items"):
				if n.item_code:
					total_quantity = getVal(n.as_it_is) + getVal(n.cr_rejection) + getVal(n.mr_rejection) + getVal(n.other_rejection) + getVal(n.return_quantity)
					return_quantity = frappe.get_value('Job Work Receipt Item', n.reference_id , 'return_quantity')
					updated_qty = return_quantity - total_quantity
					frappe.set_value('Job Work Receipt Item', n.reference_id , 'return_quantity' , updated_qty )



	@frappe.whitelist()
	def in_delivery_note(self):
		if self.is_return:
			se = frappe.new_doc("Delivery Note")
			se.customer = self.customer
			se.company = self.company
			se.posting_date = self.posting_date
			se.posting_time = self.posting_time
			for p in self.get("return_items" , filters = {'return_quantity':['not in', [0,None]]}):
				se.append(
						"items",
						{
							"item_code": p.item_code,
							"qty": p.return_quantity,
							"warehouse": p.source_warehouse,
						},)

			for m in self.get("return_raw_items_details" , filters = {'quantity':['not in', [0,None]]}):
				se.append(
						"items",
						{
							"item_code": m.raw_item_code,
							"qty": m.quantity,
							"warehouse": m.source_warehouse,
						},)
			p = se.items
			# frappe.throw(str(p))
			if p:
				se.custom_job_work_receipt = self.name		
				se.insert()
				se.save()
				se.submit()

# ======================================================================================= Both ===============================================================================

	@frappe.whitelist()
	def set_warehouse_in_child_table(self,source_warehouse , child_table , warehouse_in_table):
		for tn in self.get(child_table):
			setattr(tn, warehouse_in_table, source_warehouse)
	

	@frappe.whitelist()
	def calculating_total(self,child_table ,total_field):
		casting_details = self.get(child_table)
		total_pouring_weight = 0
		for i in casting_details:
			field_data = i.get(total_field)
			total_pouring_weight = getVal(total_pouring_weight) + getVal(field_data)
		return total_pouring_weight
