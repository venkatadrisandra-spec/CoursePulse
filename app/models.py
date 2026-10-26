from datetime import datetime, timezone
from app import db

class Course(db.Model):
    __tablename__ = "courses"
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(160), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    feedback = db.relationship("Feedback", back_populates="course", cascade="all, delete-orphan")

class FeedbackQuestion(db.Model):
    __tablename__ = "feedback_questions"
    question_id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(300), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    feedback = db.relationship("Feedback", back_populates="question", cascade="all, delete-orphan")

class Feedback(db.Model):
    __tablename__ = "feedback"
    feedback_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("feedback_questions.question_id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment_optional = db.Column(db.String(1000))
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    course = db.relationship("Course", back_populates="feedback")
    question = db.relationship("FeedbackQuestion", back_populates="feedback")
    __table_args__ = (db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_1_5"),)
