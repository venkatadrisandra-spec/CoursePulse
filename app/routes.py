from io import BytesIO
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Course, FeedbackQuestion, Feedback
from app.analytics import build_summary, csv_bytes, chart_png

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    courses = Course.query.filter_by(is_active=True).order_by(Course.course_name).all()
    questions = FeedbackQuestion.query.filter_by(is_active=True).order_by(FeedbackQuestion.question_id).all()
    return render_template("index.html", courses=courses, questions=questions)

@bp.post("/submit")
def submit_feedback():
    course_id = request.form.get("course_id", type=int)
    course = Course.query.filter_by(course_id=course_id, is_active=True).first() if course_id else None
    questions = FeedbackQuestion.query.filter_by(is_active=True).all()
    if not course:
        flash("Please select a valid course.", "error"); return redirect(url_for("main.index"))
    if not questions:
        flash("No active questions are available for feedback right now.", "error")
        return redirect(url_for("main.index"))
    pending = []
    for q in questions:
        try:
            rating = int(request.form.get(f"rating_{q.question_id}", ""))
        except (ValueError, TypeError):
            flash("Please rate every question.", "error"); return redirect(url_for("main.index"))
        if not 1 <= rating <= 5:
            flash("Ratings must be between 1 and 5.", "error"); return redirect(url_for("main.index"))
        pending.append((q.question_id, rating))
    comment = (request.form.get("comment") or "").strip() or None
    if comment and len(comment) > 1000:
        flash("Comment must be 1000 characters or fewer.", "error"); return redirect(url_for("main.index"))
    try:
        for qid, rating in pending:
            db.session.add(Feedback(course_id=course.course_id, question_id=qid, rating=rating, comment_optional=comment))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback(); current_app.logger.exception("Feedback save failed")
        flash("Feedback could not be saved. Please try again.", "error")
        return redirect(url_for("main.index"))
    flash("Thank you. Your anonymous feedback has been submitted.", "success")
    return redirect(url_for("main.index"))

@bp.get("/reports")
def reports():
    return render_template("reports.html", summary=build_summary())

@bp.get("/api/courses")
def api_courses():
    return jsonify([{"course_id":c.course_id,"course_name":c.course_name}
                    for c in Course.query.filter_by(is_active=True).order_by(Course.course_name).all()])

@bp.get("/api/summary")
def api_summary():
    return jsonify(build_summary())

@bp.get("/reports/export.csv")
def export_csv():
    return send_file(BytesIO(csv_bytes()), mimetype="text/csv", as_attachment=True,
                     download_name="course-feedback-summary.csv")

@bp.get("/charts/<kind>.png")
def chart(kind):
    if kind not in {"courses","distribution"}:
        return jsonify({"error":"Chart type must be courses or distribution"}), 400
    return send_file(chart_png(kind), mimetype="image/png")
