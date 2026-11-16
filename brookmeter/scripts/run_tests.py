"""Run the pytest suite and record the result in the drill log."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import drill_config, drill_log
import pytest


class Tally:
    def __init__(self):
        self.passed = self.failed = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call" and report.passed:
            self.passed += 1
        elif report.failed:
            self.failed += 1


tally = Tally()
os.chdir(ROOT)
code = pytest.main([drill_config.TESTS_DIR, "-q", "-rf", "--tb=short", *sys.argv[1:]], plugins=[tally])
try:
    drill_log.append_run("test", {"passed": tally.passed, "failed": tally.failed})
except Exception:
    pass
sys.exit(int(code))
