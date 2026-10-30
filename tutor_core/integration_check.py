"""Run against an isolated disposable Frappe site with bench execute."""
import frappe
from tutor_core.services import generate_lessons, complete_lesson


def run():
    frappe.set_user('Administrator')
    try:
        student = frappe.get_doc({'doctype':'Student','first_name':'CI Student','student_email_id':'ci-student@example.invalid'}).insert()
        teacher = frappe.get_doc({'doctype':'Instructor','instructor_name':'CI Teacher'}).insert()
        course = frappe.get_doc({'doctype':'Course','course_name':'CI Math'}).insert()
        contract = frappe.get_doc({'doctype':'Tutor Contract','student':student.name,'teacher':teacher.name,'course':course.name,'valid_from':'2026-10-01','valid_to':'2026-12-31'}).insert()
        rule = frappe.get_doc({'doctype':'Recurring Lesson','contract':contract.name,'weekday':2,'start_date':'2026-10-21','end_date':'2026-11-04','start_time':'18:00:00','duration_minutes':120}).insert()
        rate = frappe.get_doc({'doctype':'Tutor Rate','teacher':teacher.name,'student':student.name,'contract':contract.name,'course':course.name,'price':250,'unit':'hour','valid_from':'2026-10-01','valid_to':'2026-12-31'}).insert()
        first = generate_lessons(rule.name)
        assert first['count'] == 3, first
        assert generate_lessons(rule.name)['count'] == 0
        lesson = frappe.get_doc('Lesson Session', first['created'][0])
        outcome = complete_lesson(lesson.name)
        bill = frappe.get_doc('Billing Record', outcome['billing_record'])
        assert float(bill.amount) == 500 and float(bill.rate_snapshot) == 250
        assert complete_lesson(lesson.name)['already_completed']
        rate.price = 350
        rate.save()
        assert float(frappe.get_doc('Billing Record',bill.name).amount) == 500
        print('PASS recurrence idempotence; completion; snapshot; repeated completion')
    finally:
        frappe.db.rollback()
