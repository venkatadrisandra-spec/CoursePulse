import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import current_app
from app.models import Course, FeedbackQuestion, Feedback

def _frame():
    rows = (Feedback.query.join(Course).join(FeedbackQuestion)
        .with_entities(Course.course_id, Course.course_name, FeedbackQuestion.question_id,
                       FeedbackQuestion.question_text, Feedback.rating).all())
    return pd.DataFrame([{
        "course_id": r.course_id, "course_name": r.course_name,
        "question_id": r.question_id, "question_text": r.question_text, "rating": int(r.rating)
    } for r in rows], columns=["course_id","course_name","question_id","question_text","rating"])

def build_summary():
    df = _frame()
    minimum = int(current_app.config.get("MIN_REPORT_RESPONSES", 5))
    if df.empty:
        return {"minimum_responses": minimum, "total_responses": 0, "course_summaries": [],
                "question_summaries": [], "distribution": [], "notice": "No feedback has been submitted yet."}

    group_counts = df.groupby("course_id").rating.count()
    courses = []
    for (cid, name), group in df.groupby(["course_id", "course_name"], sort=True):
        response_count = int(group.rating.count())
        courses.append({
            "course_id": int(cid),
            "course_name": str(name),
            "response_count": response_count,
            "average_rating": round(float(np.mean(group.rating.to_numpy(dtype=float))), 2),
            "reportable": response_count >= minimum,
        })

    questions = []
    for (cid, cname, qid, qtext), group in df.groupby(
        ["course_id", "course_name", "question_id", "question_text"], sort=True):
        response_count = int(group.rating.count())
        questions.append({
            "course_id": int(cid),
            "course_name": str(cname),
            "question_id": int(qid),
            "question_text": str(qtext),
            "response_count": response_count,
            "average_rating": round(float(np.mean(group.rating.to_numpy(dtype=float))), 2),
            "reportable": response_count >= minimum,
        })

    dist = df.groupby(["course_name", "rating"]).size().reset_index(name="count")
    distribution = [{"course_name": str(r.course_name), "rating": int(r.rating), "count": int(r.count)}
                    for r in dist.itertuples(index=False)]
    return {
        "minimum_responses": minimum,
        "total_responses": int(len(df)),
        "course_summaries": courses,
        "question_summaries": questions,
        "distribution": distribution,
        "notice": None if group_counts.max() and group_counts.max() >= minimum else f"Small groups are still visible, but groups under {minimum} responses are marked as non-reportable.",
    }

def csv_bytes():
    summary = build_summary()
    rows = [{"report_type":"course","course_name":x["course_name"],"question_text":"",
             "average_rating":x["average_rating"],"response_count":x["response_count"]}
            for x in summary["course_summaries"]]
    rows += [{"report_type":"question","course_name":x["course_name"],"question_text":x["question_text"],
              "average_rating":x["average_rating"],"response_count":x["response_count"]}
             for x in summary["question_summaries"]]
    return pd.DataFrame(rows, columns=["report_type","course_name","question_text","average_rating","response_count"]).to_csv(index=False).encode("utf-8-sig")

def chart_png(kind):
    summary = build_summary()
    fig, ax = plt.subplots(figsize=(9,5))
    if kind == "distribution" and summary["distribution"]:
        d = pd.DataFrame(summary["distribution"])
        pivot = d.pivot(index="rating", columns="course_name", values="count").fillna(0).reindex([1,2,3,4,5], fill_value=0)
        pivot.plot(kind="bar", ax=ax)
        ax.set_xlabel("Rating (1–5)"); ax.set_ylabel("Response count")
        ax.legend(title="Course", bbox_to_anchor=(1.02,1), loc="upper left")
    elif kind == "courses" and summary["course_summaries"]:
        ax.bar([x["course_name"] for x in summary["course_summaries"]],
               [x["average_rating"] for x in summary["course_summaries"]])
        ax.set_ylim(0,5); ax.set_ylabel("Average rating (1–5)"); ax.tick_params(axis="x", rotation=25)
    else:
        ax.text(.5,.5,"No reportable data yet",ha="center",va="center"); ax.set_axis_off()
    ax.set_title("Rating distribution" if kind == "distribution" else "Average course ratings")
    fig.tight_layout()
    out = io.BytesIO(); fig.savefig(out, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig); out.seek(0); return out
