from __future__ import unicode_literals
import os
import frappe
import io
from frappe import _
from pyqrcode import create as qrcreate


def set_invoice_qr(invoice_name, method):

	invoice = frappe.get_doc("POS Invoice", str(invoice_name)[11:-1]) # ?
	
	invoice.flags.ignore_validate_update_after_submit = True
	invoice.flags.ignore_validate = True
			
	if invoice.einvoice_status == "Pending":
		tax_id = frappe.get_value("Company", invoice.company, "tax_id")

		if not tax_id:
			frappe.throw("Set your Tax ID in <b> Company > {0} > Tax ID </b>".format(invoice.company))

		# str(invoice.posting_date) + " " + str(invoice.posting_time)
			
		invoice.signed_qr_code = """
Seller Name: {0}
VAT Number: {1}
Timestamp: {2}
VAT Amount: {3}
Invoice Total: {4}""".format(invoice.company, tax_id, invoice.modified, invoice.total_taxes_and_charges, invoice.base_grand_total)

		qrcode = invoice.signed_qr_code
		doctype = invoice.doctype
		docname = invoice.name

		filename = 'QRCode_{}.png'.format(docname).replace(os.path.sep, "__")

		qr_image = io.BytesIO()
		url = qrcreate(qrcode, error='L')
		url.png(qr_image, scale=2, quiet_zone=1)
		_file = frappe.get_doc({
			"doctype": "File",
			"file_name": filename,
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
			"attached_to_field": "qrcode_image",
			"is_private": 1,
			"content": qr_image.getvalue()})
		_file.save()

		invoice.db_set('qr_code_file', _file.file_url)
		invoice.db_set('einvoice_status', "Generated")
		invoice.db_set('signed_qr_code', qrcode)
		frappe.db.commit()



def set_sales_invoice_qr(invoice, method):	
	invoice.flags.ignore_validate_update_after_submit = True
	invoice.flags.ignore_validate = True

	if invoice.einvoice_status == "Pending":
		tax_id = frappe.get_value("Company", invoice.company, "tax_id")

		if not tax_id:
			frappe.throw("Set your Tax ID in <b> Company > {0} > Tax ID </b>".format(invoice.company))

		# str(invoice.posting_date) + " " + str(invoice.posting_time)
			
		invoice.signed_qr_code = """
Seller Name: {0}
VAT Number: {1}
Timestamp: {2}
VAT Amount: {3}
Invoice Total: {4}""".format(invoice.company, tax_id, invoice.modified, invoice.total_taxes_and_charges, invoice.base_grand_total)

		qrcode = invoice.signed_qr_code
		doctype = invoice.doctype
		docname = invoice.name

		filename = 'QRCode_{}.png'.format(docname).replace(os.path.sep, "__")

		qr_image = io.BytesIO()
		url = qrcreate(qrcode, error='L')
		url.png(qr_image, scale=2, quiet_zone=1)
		_file = frappe.get_doc({
			"doctype": "File",
			"file_name": filename,
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
			"attached_to_field": "qrcode_image",
			"is_private": 1,
			"content": qr_image.getvalue()})
		_file.save()

		invoice.db_set('qr_code_file', _file.file_url)
		invoice.db_set('einvoice_status', "Generated")
		invoice.db_set('signed_qr_code', qrcode)
		frappe.db.commit()