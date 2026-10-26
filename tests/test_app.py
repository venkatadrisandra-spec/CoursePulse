import importlib

import pytest

import config
from app import create_app, db
from app.analytics import build_summary
from app.models import Course, FeedbackQuestion, Feedback

@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "SECRET_KEY": "test-secret", "MIN_REPORT_RESPONSES": 2})
    with app.app_context():
        db.drop_all(); db.create_all()
        db.session.add_all([Course(course_name="Test Course"),
                            FeedbackQuestion(question_text="The course was clear.")])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove(); db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"anonymous" in response.data.lower()

def test_valid_submission(client, app):
    with app.app_context():
        c, q = Course.query.first(), FeedbackQuestion.query.first()
        cid, qid = c.course_id, q.question_id
    response = client.post("/submit", data={"course_id":str(cid), f"rating_{qid}":"5"}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Feedback.query.count() == 1
        assert Feedback.query.first().rating == 5

def test_sample_feedback_updates_question_averages_and_reports(client, app):
    with app.app_context():
        course = Course.query.first()
        first_question = FeedbackQuestion.query.first()
        second_question = FeedbackQuestion(question_text="The instructor explained concepts clearly.")
        db.session.add(second_question)
        db.session.commit()
        course_id = course.course_id
        first_question_id = first_question.question_id
        second_question_id = second_question.question_id

    sample_feedback = [(5, 3), (4, 4), (3, 5)]
    for index, (first_rating, second_rating) in enumerate(sample_feedback, start=1):
        response = client.post(
            "/submit",
            data={
                "course_id": str(course_id),
                f"rating_{first_question_id}": str(first_rating),
                f"rating_{second_question_id}": str(second_rating),
                "comment": f"Sample feedback {index}",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"feedback has been submitted" in response.data.lower()

    with app.app_context():
        assert Feedback.query.count() == 6
        assert {item.comment_optional for item in Feedback.query.all()} == {
            "Sample feedback 1", "Sample feedback 2", "Sample feedback 3"
        }

    summary_response = client.get("/api/summary")
    assert summary_response.status_code == 200
    summary = summary_response.get_json()
    assert summary["total_responses"] == 6
    assert summary["course_summaries"][0]["average_rating"] == 4.0
    assert summary["course_summaries"][0]["response_count"] == 6
    question_summaries = {
        item["question_id"]: item for item in summary["question_summaries"]
    }
    assert question_summaries[first_question_id]["average_rating"] == 4.0
    assert question_summaries[first_question_id]["response_count"] == 3
    assert question_summaries[second_question_id]["average_rating"] == 4.0
    assert question_summaries[second_question_id]["response_count"] == 3

    reports_response = client.get("/reports")
    assert reports_response.status_code == 200
    assert b"Average rating by question" in reports_response.data
    assert b"The instructor explained concepts clearly." in reports_response.data
    assert reports_response.data.count(b"4.00 / 5") >= 3

    csv_response = client.get("/reports/export.csv")
    assert csv_response.status_code == 200
    csv_content = csv_response.get_data(as_text=True)
    assert "The instructor explained concepts clearly." in csv_content
    assert "question,Test Course" in csv_content

def test_invalid_rating_is_rejected(client, app):
    with app.app_context():
        c, q = Course.query.first(), FeedbackQuestion.query.first()
        cid, qid = c.course_id, q.question_id
    client.post("/submit", data={"course_id":str(cid), f"rating_{qid}":"6"}, follow_redirects=True)
    with app.app_context():
        assert Feedback.query.count() == 0

def test_reports_api_and_chart(client):
    assert client.get("/reports").status_code == 200
    assert client.get("/api/summary").status_code == 200
    assert client.get("/api/courses").status_code == 200
    assert client.get("/charts/courses.png").mimetype == "image/png"


def test_question_summary_is_not_hidden_when_data_exists():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "SECRET_KEY": "test-secret", "MIN_REPORT_RESPONSES": 5})
    with app.app_context():
        course = Course.query.first()
        question = FeedbackQuestion.query.first()
        db.session.add_all([
            Feedback(course_id=course.course_id, question_id=question.question_id, rating=4),
            Feedback(course_id=course.course_id, question_id=question.question_id, rating=5),
            Feedback(course_id=course.course_id, question_id=question.question_id, rating=3),
            Feedback(course_id=course.course_id, question_id=question.question_id, rating=4),
            Feedback(course_id=course.course_id, question_id=question.question_id, rating=5),
        ])
        db.session.commit()
        summary = build_summary()
        assert len(summary["question_summaries"]) >= 1
        assert any(item["question_text"] == question.question_text for item in summary["question_summaries"])


def test_create_app_seeds_default_courses_and_questions():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "SECRET_KEY": "test-secret", "MIN_REPORT_RESPONSES": 2})
    with app.app_context():
        assert Course.query.count() >= 1
        assert FeedbackQuestion.query.count() >= 1
        assert Feedback.query.count() > 0


def test_invalid_min_report_responses_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("MIN_REPORT_RESPONSES", "not-a-number")
    importlib.reload(config)
    assert config.Config.MIN_REPORT_RESPONSES == 5
    monkeypatch.delenv("MIN_REPORT_RESPONSES", raising=False)
    importlib.reload(config)


def test_submission_rejected_when_no_questions_are_active():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "SECRET_KEY": "test-secret", "MIN_REPORT_RESPONSES": 2})
    with app.app_context():
        db.drop_all(); db.create_all()
        db.session.add(Course(course_name="No Question Course"))
        db.session.commit()
        course_id = Course.query.first().course_id

    client = app.test_client()
    response = client.post("/submit", data={"course_id": str(course_id), "comment": "Test comment"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"no active questions" in response.data.lower()
    with app.app_context():
        assert Feedback.query.count() == 0
