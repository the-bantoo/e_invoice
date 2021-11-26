import io
import os

import frappe
from frappe import _
from pyqrcode import create as qr_create

from erpnext import get_region


def create_sales_invoice_qr(doc, method):
	"""Create QR Code after inserting Sales Inv
	"""
	frappe.errprint("1")

	region = get_region(doc.company)
	#if region not in ['Saudi Arabia']:
		#return

	# if QR Code field not present, do nothing
	if not hasattr(doc, 'qr_code'):
		frappe.msgprint(_("qr_code field needs to be added first"))

	# Don't create QR Code if it already exists
	qr_code = doc.get("qr_code")
	if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
		return

	meta = frappe.get_meta('Sales Invoice')

	for field in meta.get_image_fields():
		if field.fieldname == 'qr_code':
			from urllib.parse import urlencode

			# Creating public url to print format
			default_print_format = frappe.db.get_value('Property Setter', dict(property='default_print_format', doc_type=doc.doctype), "value")

			# System Language
			language = frappe.get_system_settings('language')

			params = urlencode({
				'format': default_print_format or 'Standard',
				'_lang': language,
				'key': doc.get_signature()
			})

			# creating qr code for the url
			url = f"{ frappe.utils.get_url() }/{ 'Sales%20Invoice' }/{ doc.name }?{ params }"
			qr_image = io.BytesIO()
			url = qr_create(url, error='L')
			url.png(qr_image, scale=2, quiet_zone=1)

			# making file
			filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"is_private": 0,
				"content": qr_image.getvalue(),
				"attached_to_doctype": doc.get("doctype"),
				"attached_to_name": doc.get("name"),
				"attached_to_field": "qr_code"
			})

			_file.save()

			# assigning to document
			doc.db_set('qr_code', _file.file_url)
			doc.notify_update()

			break

def create_pos_invoice_qr(doc, method):
	"""Create QR Code after inserting Sales Inv
	"""
	invoice = frappe.get_doc("POS Invoice", str(doc)[11:-1]) # ?
	
	invoice.flags.ignore_validate_update_after_submit = True
	invoice.flags.ignore_validate = True

	title = "Simplified Tax Invoice"
	if invoice.is_return == 1:
		title = "Return Sales Invoice"
			
	#if invoice.einvoice_status == "Pending" or invoice.is_return == 1:
	tax_id = frappe.get_value("Company", invoice.company, "tax_id")

	if not tax_id:
		frappe.throw( _("Set your Tax ID in <b> Company > {0} > Tax ID </b>".format(invoice.company)) )

	# str(invoice.posting_date) + " " + str(invoice.posting_time)


	from urllib.parse import urlencode

	# Creating public url to print format
	default_print_format = frappe.db.get_value('Property Setter', dict(property='default_print_format', doc_type=invoice.doctype), "value")

	# System Language
	language = frappe.get_system_settings('language')

	params = urlencode({
		'format': "E-Invoice Saudi" or 'Standard',
		'_lang': language,
		'key': invoice.get_signature()
	})

	# creating qr code for the url
	url = f"{ frappe.utils.get_url() }/{ 'POS%20Invoice' }/{ invoice.name }?{ params }"

	invoice.signed_qr_code = url

	qrcode = invoice.signed_qr_code
	doctype = invoice.doctype
	docname = invoice.name

	filename = 'QR-Code-{}.png'.format(docname).replace(os.path.sep, "__")

	qr_image = io.BytesIO()
	url = qr_create(qrcode, error='L')
	url.png(qr_image, scale=2, quiet_zone=1)
	_file = frappe.get_doc({
		"doctype": "File",
		"file_name": filename,
		"attached_to_doctype": doctype,
		"attached_to_name": docname,
		"attached_to_field": "qrcode_image",
		"is_private": 0,
		"content": qr_image.getvalue()})

	# remove old file first
	if hasattr(invoice, 'qr_code_file'):
		if invoice.get('qr_code_file'):
			file_doc = frappe.get_list('File', {
				'file_url': invoice.get('qr_code_file')
			})
			if len(file_doc):
				frappe.delete_doc('File', file_doc[0].name)
	_file.save()

	#invoice.db_set('qr_code_file', _file.file_url)
	#invoice.db_set('einvoice_status', "Generated")
	#invoice.db_set('signed_qr_code', qrcode)
	frappe.db.set_value('POS Invoice', invoice.name, 
	{
		'signed_qr_code': qrcode,
		'einvoice_status': "Generated",
		'qr_code_file': _file.file_url
	}, update_modified=False)
	#frappe.db.commit()
	invoice.notify_update()


def delete_qr_code_file(doc, method):
	"""Delete QR Code on deleted sales invoice"""

	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	if hasattr(doc, 'qr_code'):
		if doc.get('qr_code'):
			file_doc = frappe.get_list('File', {
				'file_url': doc.get('qr_code')
			})
			if len(file_doc):
				frappe.delete_doc('File', file_doc[0].name)

def delete_vat_settings_for_company(doc, method):
	if doc.country != 'Saudi Arabia':
		return

	settings_doc = frappe.get_doc('KSA VAT Setting', {'company': doc.name})
	settings_doc.delete()