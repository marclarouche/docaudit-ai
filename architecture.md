docaudit-ai/
├── app.py                  # Streamlit interface
├── src/
│   └── docaudit/
│       ├── engine.py       # Independent audit orchestrator
│       ├── parser.py       # Document ingestion
│       ├── readability.py  # Readability analysis
│       ├── terminology.py  # Editorial rules
│       ├── models.py       # Data schemas
│       └── reports.py      # Report generation
├── config/
│   └── style_guide.yaml
├── samples/
├── tests/
├── pyproject.toml
└── README.md