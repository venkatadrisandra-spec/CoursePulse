import random

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()

DEFAULT_COURSES = [
    "Introduction to Programming",
    "Database Management Systems",
    "Discrete Mathematics",
]

DEFAULT_QUESTIONS = [
    "The course objectives were clear.",
    "Learning materials helped me understand the topics.",
    "Assessments matched the topics taught.",
    "I could ask questions and get useful clarification.",
    "Overall, this course supported my learning.",
]


def seed_default_data(app):
    with app.app_context():
        from app.models import Course, FeedbackQuestion

        if Course.query.count() == 0:
            db.session.add_all(Course(course_name=name) for name in DEFAULT_COURSES)

        if FeedbackQuestion.query.count() == 0:
            db.session.add_all(
                FeedbackQuestion(question_text=text)
                for text in DEFAULT_QUESTIONS
            )

        db.session.commit()


def seed_demo_feedback(app):
    with app.app_context():
        from app.models import Course, Feedback, FeedbackQuestion

        courses = Course.query.order_by(Course.course_name).all()
        questions = FeedbackQuestion.query.order_by(FeedbackQuestion.question_id).all()
        target_feedback = max(12, int(app.config.get("MIN_REPORT_RESPONSES", 5))) * len(courses) * len(questions)

        if Feedback.query.count() >= target_feedback:
            return

        random.seed(2026)
        for course in courses:
            for _ in range(12):
                base = random.choice([2, 3, 3, 4, 4, 5])
                for question in questions:
                    rating = max(1, min(5, base + random.choice([-1, 0, 0, 0, 1])))
                    db.session.add(
                        Feedback(
                            course_id=course.course_id,
                            question_id=question.question_id,
                            rating=rating,
                            comment_optional=None,
                        )
                    )

        db.session.commit()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    from app.routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
        seed_default_data(app)
        seed_demo_feedback(app)
    return app
