# Inserts fictional ratings for local demonstration only.
import random
from app import create_app, db
from app.models import Course, FeedbackQuestion, Feedback

COURSES = ["Introduction to Programming", "Database Management Systems", "Discrete Mathematics"]
QUESTIONS = [
    "The course objectives were clear.",
    "Learning materials helped me understand the topics.",
    "Assessments matched the topics taught.",
    "I could ask questions and get useful clarification.",
    "Overall, this course supported my learning.",
]
app = create_app()
random.seed(2026)
with app.app_context():
    for name in COURSES:
        if not Course.query.filter_by(course_name=name).first():
            db.session.add(Course(course_name=name))
    for question in QUESTIONS:
        if not FeedbackQuestion.query.filter_by(question_text=question).first():
            db.session.add(FeedbackQuestion(question_text=question))
    db.session.commit()
    courses = Course.query.filter(Course.course_name.in_(COURSES)).all()
    questions = FeedbackQuestion.query.filter(FeedbackQuestion.question_text.in_(QUESTIONS)).all()
    inserted = 0
    for course in courses:
        for _ in range(12):
            base = random.choice([2,3,3,4,4,5])
            for question in questions:
                rating = max(1, min(5, base + random.choice([-1,0,0,0,1])))
                db.session.add(Feedback(course_id=course.course_id, question_id=question.question_id,
                                        rating=rating, comment_optional=None))
                inserted += 1
    db.session.commit()
    print(f"Inserted {inserted} fictional ratings; these are not real student opinions.")
