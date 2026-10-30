import frappe
from frappe.model.document import Document

class TutorIdentity(Document):
    def validate(self):
        if (self.kind == 'Teacher' and (not self.teacher or self.student)) or (self.kind == 'Student' and (not self.student or self.teacher)):
            frappe.throw('Identity must link exactly one matching teacher or student')
