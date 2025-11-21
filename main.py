"""Minimal entrypoint to smoke-test the code review agent."""

from pprint import pprint

from app.crew.crew_factory import run_file_diff_review


def _sample_diff_context() -> dict[str, str]:
    return {
        "file_path": "src/example.py",
        "language": "python",
        "diff": """@@ -1,3 +1,5 @@\n- print(\"Hello\")\n+ def hello():\n+     print(\"Hello, world!\")\n""",
        "old_code": 'print("Hello")\n',
        "new_code": 'def hello():\n    print("Hello, world!\")\n',
    }


def main():
    findings = run_file_diff_review(_sample_diff_context())
    print("\n=== Agent findings ===\n")
    pprint(findings)


if __name__ == "__main__":
    main()
