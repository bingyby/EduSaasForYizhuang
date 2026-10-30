import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime

class LessonSession(Document):
    def validate(self):
        if self.starts_at and self.ends_at and get_datetime(self.ends_at) <= get_datetime(self.starts_at):
            frappe.throw('End must be after start')
        old = self.get_doc_before_save()
        if self.status == 'Completed' and (not old or old.status != 'Completed') and not self.flags.get('tutor_completion'):
            frappe.throw('Complete lessons through the billing service')
        if old and old.status == 'Completed' and self.has_value_changed('status'):
            frappe.throw('Completed lessons cannot change status in this prototype')
        if old and old.status == 'Completed' and any(self.has_value_changed(k) for k in ('starts_at','ends_at','teacher','student','course','contract')):
            frappe.throw('Completed lesson billing facts cannot be changed')
