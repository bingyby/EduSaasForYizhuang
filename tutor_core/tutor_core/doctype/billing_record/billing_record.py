import frappe
from frappe.model.document import Document

class BillingRecord(Document):
    def validate(self):
        if self.is_new() and not self.flags.get('tutor_create_bill'):
            frappe.throw('Billing records are created by the lesson completion service')
        if not self.is_new():
            frappe.throw('Billing snapshots are immutable')

    def on_trash(self):
        frappe.throw('Billing snapshots cannot be deleted')
