"""Run against an isolated disposable Frappe site with bench execute."""
import frappe
from tutor_core.services import generate_lessons, complete_lesson
from tutor_core.portal import lessons, reschedule


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
        other_student = frappe.get_doc({'doctype':'Student','first_name':'Other Student','student_email_id':'other-student@example.invalid'}).insert()
        other_teacher = frappe.get_doc({'doctype':'Instructor','instructor_name':'Other Teacher'}).insert()
        other_contract = frappe.get_doc({'doctype':'Tutor Contract','student':other_student.name,'teacher':other_teacher.name,'course':course.name,'valid_from':'2026-10-01','valid_to':'2026-12-31'}).insert()
        other_lesson = frappe.get_doc({'doctype':'Lesson Session','contract':other_contract.name,'student':other_student.name,'teacher':other_teacher.name,'course':course.name,'starts_at':'2026-11-18 18:00:00','ends_at':'2026-11-18 20:00:00','status':'Scheduled'}).insert()
        teacher_user = frappe.get_doc({'doctype':'User','email':'teacher-ci@example.invalid','first_name':'Teacher CI','user_type':'Website User','send_welcome_email':0}).insert()
        teacher_user.add_roles('Tutor Teacher')
        student_user = frappe.get_doc({'doctype':'User','email':'student-ci@example.invalid','first_name':'Student CI','user_type':'Website User','send_welcome_email':0}).insert()
        student_user.add_roles('Tutor Student')
        frappe.get_doc({'doctype':'Tutor Identity','user':teacher_user.name,'kind':'Teacher','teacher':teacher.name}).insert()
        frappe.get_doc({'doctype':'Tutor Identity','user':student_user.name,'kind':'Student','student':student.name}).insert()
        frappe.set_user(teacher_user.name)
        assert len(lessons()['lessons']) == 3
        assert not frappe.has_permission('Lesson Session','read',other_lesson)
        try:
            reschedule(other_lesson.name,'2026-11-19 18:00:00','2026-11-19 20:00:00')
            raise AssertionError('teacher rescheduled another teacher lesson')
        except frappe.PermissionError:
            pass
        own = first['created'][1]
        reschedule(own,'2026-10-29 18:00:00','2026-10-29 20:00:00')
        assert frappe.db.count('Lesson Change', {'lesson':own}) == 1
        assert str(frappe.get_doc('Lesson Session',first['created'][2]).starts_at).startswith('2026-11-04')
        frappe.set_user(student_user.name)
        student_rows = lessons()['lessons']
        assert len(student_rows) == 3 and all(x['student']==student.name for x in student_rows)
        assert not frappe.has_permission('Lesson Session','read',other_lesson)
        try:
            reschedule(own,'2026-11-01 18:00:00','2026-11-01 20:00:00')
            raise AssertionError('student was allowed to reschedule')
        except frappe.PermissionError:
            pass
        frappe.set_user('Administrator')
        print('PASS recurrence, billing, scoped portal, denied cross-user access and rescheduling')
    finally:
        frappe.db.rollback()


def seed_http():
    """Seed disposable CI-only accounts and records for HTTP smoke tests."""
    frappe.set_user('Administrator')
    course = frappe.get_doc({'doctype':'Course','course_name':'HTTP Math'}).insert()
    for i in (1, 2):
        student = frappe.get_doc({'doctype':'Student','first_name':f'HTTP Student {i}','student_email_id':f'http-student-{i}@example.invalid'}).insert()
        teacher = frappe.get_doc({'doctype':'Instructor','instructor_name':f'HTTP Teacher {i}'}).insert()
        contract = frappe.get_doc({'doctype':'Tutor Contract','student':student.name,'teacher':teacher.name,'course':course.name,'valid_from':'2026-01-01','valid_to':'2027-12-31'}).insert()
        frappe.get_doc({'doctype':'Lesson Session','contract':contract.name,'student':student.name,'teacher':teacher.name,'course':course.name,'starts_at':'2026-11-18 18:00:00','ends_at':'2026-11-18 20:00:00','status':'Scheduled'}).insert()
        for kind, link in [('Teacher',teacher.name), ('Student',student.name)]:
            email = f'http-{kind.lower()}-{i}@example.invalid'
            user = frappe.get_doc({'doctype':'User','email':email,'first_name':f'HTTP {kind} {i}','user_type':'Website User','send_welcome_email':0,'new_password':'ci-only-password-123'}).insert()
            user.add_roles('Tutor '+kind)
            frappe.get_doc({'doctype':'Tutor Identity','user':user.name,'kind':kind,kind.lower():link}).insert()
    frappe.db.commit()
