def pytest_addoption(parser):
    parser.addoption(
        "--run-llm-evals",
        action="store_true",
        default=False,
        help="Run Layer 3 LLM-as-judge evals (spends real tokens).",
    )
