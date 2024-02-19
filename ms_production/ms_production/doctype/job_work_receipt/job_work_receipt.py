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
			pass
		else:
			self.validate_items()

	@frappe.whitelist()
	def before_submit(self):
		if self.is_return:
			pass
		else:
			self.in_material_receipt()



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
# ======================================================================================= IS RETURN ===============================================================================
	
	@frappe.whitelist()
	def set_data_from_jwr(self):
		if self.is_return:
			return_jwr = self.get("return_against")
			for i in return_jwr:
				items = frappe.get_all("Job Work Receipt Item" , filters = {'parent':i.job_work_receipt} , fields = ['item_code','item_name','return_quantity','qty','reference_id'])
				for d in items:
					returnable_quantity =  d.qty - d.return_quantity
					self.append("return_items",
											{	'item_code': d.item_code ,
												'returnable_quantity': returnable_quantity ,
												'reference_id': d.reference_id,
												'item_name':d.item_name},),

	@frappe.whitelist()
	def finish_total_quentity_calculate(self):
		for j in self.get("return_items"):
			j.total_quantity = getVal(j.as_it_is) + getVal(j.cr_rejection) + getVal(j.mr_rejection) + getVal(j.other_rejection) + getVal(j.return_quantity)
	
			if j.total_quantity > j.returnable_quantity:
				frappe.throw(f'Total Quantity For Item {j.item_code}-{j.item_name} is Should Not Be Greater Than Actual Required Quantity ')


	@frappe.whitelist()
	def set_dat_in_rejected_items_reasons(self):
		for n in self.get("return_items"):
			if n.item_code:
				pass
			# for x in doc:
			# 	per_unit_finish =  x.get('required_quantity')
			# 	if n.cr_casting_rejection:
			# 		cr_qty = n.cr_casting_rejection * per_unit_finish
			# 		self.append("rejected_items_reasons",{
			# 					'item_code':  x.get('item_code'),
			# 					'item_name':x.get('item_name'),
			# 					'reference_id': n.get('reference_id'),
			# 					'rejection_type': "CR (Casting Rejection)",
			# 					'quantity': cr_qty,
			# 					'weight_per_unit': n.weight_per_unit,
			# 					'total_rejected_weight': n.weight_per_unit * cr_qty,
			# 					'target_warehouse':'',
			# 				},),
			# 	if n.mr_machine_rejection:
			# 		mr_qty = n.mr_machine_rejection * per_unit_finish
			# 		self.append("rejected_items_reasons",{
			# 					'item_code':  x.get('item_code'),
			# 					'item_name':x.get('item_name'),
			# 					'reference_id': n.get('reference_id'),
			# 					'rejection_type': "MR (Machine Rejection)",
			# 					'quantity': mr_qty,
			# 					'weight_per_unit': n.weight_per_unit,
			# 					'total_rejected_weight': n.weight_per_unit * mr_qty,
			# 					'target_warehouse':'',
			# 				},),
			# 	if n.rw_rework:
			# 		rw_qty = n.rw_rework * per_unit_finish
			# 		self.append("rejected_items_reasons",{
			# 					'item_code': x.get('item_code'),
			# 					'item_name':x.get('item_name'),
			# 					'reference_id': n.get('reference_id'),
			# 					'rejection_type': "RW (Rework)",
			# 					'quantity': rw_qty,
			# 					'weight_per_unit': n.weight_per_unit,
			# 					'total_rejected_weight': n.weight_per_unit * rw_qty,
			# 					'target_warehouse':'',
			# 				},),