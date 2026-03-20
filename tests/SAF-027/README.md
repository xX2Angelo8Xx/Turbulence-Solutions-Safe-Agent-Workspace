# SAF-027 Tests — Location Note
#
# SAF-027 ("Tests for python -c inline code scanning") tests are implemented in
# tests/SAF-026/test_saf026_edge_cases.py because SAF-027 extends SAF-026's
# _scan_python_inline_code function and shares the same test fixtures.
#
# Run: .venv\Scripts\python -m pytest tests/SAF-026/ -v -k "scan_python_inline"
