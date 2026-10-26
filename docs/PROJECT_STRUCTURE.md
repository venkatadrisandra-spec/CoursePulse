# Folder structure

```text
course-feedback-analytics/
├── app/
│   ├── __init__.py
│   ├── analytics.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── reports.html
│   └── static/css/style.css
├── docs/
│   ├── API.md
│   └── PROJECT_STRUCTURE.md
├── scripts/
│   ├── init_db.py
│   └── seed_demo.py
├── tests/test_app.py
├── .env.example
├── .gitignore
├── config.py
├── README.md
├── requirements.txt
└── run.py
```

Tables: `courses`, `feedback_questions`, `feedback`. No student name, email, roll number, IP address or user-agent is collected.
