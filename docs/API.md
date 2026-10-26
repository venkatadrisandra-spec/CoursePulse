# API reference

- `GET /api/courses`: active course IDs and names.
- `GET /api/summary`: aggregated course/question averages, counts, rating distribution and suppression notice. Small groups are suppressed.
- `GET /reports/export.csv`: downloads aggregated CSV; no individual records/comments.
- `GET /charts/courses.png`: average course ratings chart.
- `GET /charts/distribution.png`: rating distribution chart.
- `POST /submit`: HTML form submission with `course_id`, one `rating_<question_id>` integer from 1–5 for every active question, and optional `comment` up to 1000 characters.
