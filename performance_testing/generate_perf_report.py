"""
generate_perf_report.py
~~~~~~~~~~~~~~~~~~~~~~~
Generates the Employee REST API Performance Testing Plan as a PDF.

Usage:
    cd ApiTestsPython
    python performance_testing/generate_perf_report.py

Output:
    performance_testing/Employee_API_Performance_Test_Plan.pdf
"""

from fpdf import FPDF, XPos, YPos
from datetime import date
import os

# -- Colour palette -----------------------------------------------------------
BLUE_DARK   = (0,   70,  127)
BLUE_MID    = (0,  102,  179)
BLUE_LIGHT  = (220, 235, 248)
GREEN_DARK  = (0,   90,   50)
GREEN_MID   = (0,  140,   80)
GREEN_LIGHT = (220, 245, 230)
WHITE       = (255, 255, 255)
GREY_LIGHT  = (245, 245, 245)
GREY_MED    = (100, 100, 100)
RED         = (192,   0,   0)
ORANGE      = (210, 100,   0)
AMBER       = (160, 120,   0)
GREEN_OK    = ( 30, 130,  60)

PAGE_W  = 190   # A4 usable width (210 - 2*10 mm margins)
L_MARGIN = 10


# -- Custom PDF class ---------------------------------------------------------

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GREY_MED)
        self.cell(0, 5, "Employee REST API - Performance Testing Plan", align="L")
        self.set_xy(L_MARGIN, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")
        self.ln(3)
        self.set_draw_color(*GREEN_DARK)
        self.line(L_MARGIN, self.get_y(), L_MARGIN + PAGE_W, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY_MED)
        self.cell(0, 8, "Employee REST API - Performance Testing Plan  |  Internal Use", align="C")
        self.set_text_color(0, 0, 0)


# -- Helpers ------------------------------------------------------------------

def section_header(pdf: PDF, text: str):
    pdf.ln(3)
    pdf.set_fill_color(*GREEN_DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(PAGE_W, 8, f"  {text}", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def sub_header(pdf: PDF, text: str):
    pdf.ln(2)
    pdf.set_fill_color(*GREEN_MID)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(PAGE_W, 6, f"  {text}", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def body(pdf: PDF, text: str, indent: int = 0):
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(L_MARGIN + indent)
    pdf.multi_cell(PAGE_W - indent, 5, text)


def bullet(pdf: PDF, text: str, indent: int = 4):
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(L_MARGIN + indent)
    pdf.multi_cell(PAGE_W - indent - 2, 5, f"  {text}")


def kv(pdf: PDF, label: str, value: str):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(L_MARGIN + 4)
    pdf.cell(45, 5, label)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(PAGE_W - 49, 5, value)


def _line_count(pdf: PDF, text: str, width: float) -> int:
    words = text.split()
    lines, line_w = 1, 0.0
    for word in words:
        w = pdf.get_string_width(word + " ")
        if line_w + w > width:
            lines += 1
            line_w = w
        else:
            line_w += w
    return max(lines, 1)


def table_header(pdf: PDF, cols: list[tuple[str, float]]):
    pdf.set_fill_color(*GREEN_MID)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for label, w in cols:
        pdf.cell(w, 6, f" {label}", border=1, fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


def table_row(pdf: PDF, cols: list[tuple[str, float]], shade: bool = False):
    row_h = 5
    # estimate height
    max_lines = 1
    for val, w in cols:
        n = _line_count(pdf, str(val), w - 2)
        if n > max_lines:
            max_lines = n
    row_h_total = row_h * max_lines

    if pdf.get_y() + row_h_total > pdf.h - pdf.b_margin:
        pdf.add_page()
        return  # caller re-draws header if needed

    y0 = pdf.get_y()
    if shade:
        pdf.set_fill_color(*GREEN_LIGHT)
    else:
        pdf.set_fill_color(*WHITE)
    pdf.set_font("Helvetica", "", 8)
    x = L_MARGIN
    for val, w in cols:
        pdf.set_xy(x, y0)
        pdf.multi_cell(w, row_h, f" {val}", border=1, fill=True)
        x += w
    pdf.set_y(y0 + row_h_total)


def scenario_card(pdf: PDF, sid: str, name: str, users: int | str,
                  ramp: str, duration: str, wait: str, kpi: str,
                  task_set: str, cmd: str):
    """Render a single scenario block with coloured title bar."""
    card_top = pdf.get_y()
    if card_top + 52 > pdf.h - pdf.b_margin:
        pdf.add_page()
        card_top = pdf.get_y()

    # Title bar
    pdf.set_fill_color(*GREEN_DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(PAGE_W, 7, f"  {sid}  -  {name}", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    # Detail rows
    rows = [
        ("Concurrent users",  str(users)),
        ("Ramp-up",           ramp),
        ("Duration",          duration),
        ("Wait time",         wait),
        ("Task set",          task_set),
        ("KPI target",        kpi),
    ]
    for i, (label, val) in enumerate(rows):
        bg = GREEN_LIGHT if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(40, 5, f"  {label}", border="LTB", fill=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(PAGE_W - 40, 5, f"  {val}", border="RTB", fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Command block
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 7)
    pdf.multi_cell(PAGE_W, 4, cmd, border=1, fill=True)
    pdf.ln(3)


# -- Cover page ---------------------------------------------------------------

def cover_page(pdf: PDF):
    pdf.add_page()
    pdf.ln(40)

    pdf.set_fill_color(*GREEN_DARK)
    pdf.rect(L_MARGIN, pdf.get_y(), PAGE_W, 32, "F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(L_MARGIN, pdf.get_y() + 5)
    pdf.cell(PAGE_W, 12, "Employee REST API", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(PAGE_W, 10, "Performance Testing Plan", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(14)

    meta = [
        ("API Base URL",   "http://localhost:8000"),
        ("Tool",           "Locust 2.32.3 (Python)"),
        ("Version",        "1.0"),
        ("Date",           date.today().strftime("%d %B %Y")),
        ("Prepared for",   "ApiTestsPython Project"),
        ("Classification", "Internal Use"),
    ]
    for label, value in meta:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 7, f"  {label}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(100, 7, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    pdf.set_fill_color(*GREEN_LIGHT)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(PAGE_W, 6,
        "  This document defines the performance testing strategy, test scenarios, "
        "acceptance criteria, tooling, and run commands for the Employee REST API. "
        "All tests use Locust running headless against a locally hosted FastAPI server.",
        fill=True)


# -- Section 1: Overview & Objectives -----------------------------------------

def section_overview(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 1 - Overview & Objectives")

    body(pdf,
        "Performance testing verifies that the Employee REST API meets its non-functional "
        "requirements under realistic and extreme load conditions. This plan covers five "
        "test types that together assess throughput, latency, stability, and resource limits.")
    pdf.ln(3)

    sub_header(pdf, "1.1  Goals")
    goals = [
        "Establish a latency baseline for all endpoints with a single user.",
        "Verify the API sustains acceptable response times at 50 concurrent users (normal load).",
        "Identify the stress threshold where error rates exceed 1% (stress test).",
        "Confirm the API recovers correctly from a sudden traffic spike (500 users).",
        "Detect memory leaks, ID counter overflow, or response degradation over 60 minutes (soak).",
        "Produce an HTML report and CSV data for trend analysis after each run.",
    ]
    for g in goals:
        bullet(pdf, f"- {g}")

    pdf.ln(3)
    sub_header(pdf, "1.2  Scope")
    body(pdf, "All 7 REST endpoints are exercised during tests:")
    endpoints = [
        ("GET",    "/api/employees",                    "List / filter employees"),
        ("GET",    "/api/employees/{id}",               "Retrieve single employee"),
        ("POST",   "/api/employees",                    "Create employee"),
        ("POST",   "/api/departments/{dept}/employees", "Create employee via department path"),
        ("PUT",    "/api/employees/{id}",               "Full update"),
        ("PATCH",  "/api/employees/{id}",               "Partial update"),
        ("DELETE", "/api/employees/{id}",               "Delete employee"),
    ]
    cols = [("Method", 20), ("Endpoint", 90), ("Purpose", 80)]
    table_header(pdf, cols)
    for i, (m, ep, p) in enumerate(endpoints):
        table_row(pdf, [(m, 20), (ep, 90), (p, 80)], shade=(i % 2 == 0))

    pdf.ln(3)
    sub_header(pdf, "1.3  Out of Scope")
    oos = [
        "Browser-level performance (no UI).",
        "Database persistence (API uses in-memory store - resets on restart).",
        "Network latency simulation (all tests run on localhost).",
        "HTTPS / TLS overhead (API runs on plain HTTP).",
    ]
    for o in oos:
        bullet(pdf, f"- {o}")


# -- Section 2: Environment ---------------------------------------------------

def section_environment(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 2 - Test Environment")

    sub_header(pdf, "2.1  Server Under Test")
    rows = [
        ("Framework",      "FastAPI 0.115.5 + Uvicorn 0.32.1"),
        ("Host",           "localhost"),
        ("Port",           "8000"),
        ("Data store",     "In-memory Python dict (resets on restart)"),
        ("Auth",           "X-API-Key header, value: secret123"),
        ("Start command",  "uvicorn main:app --reload --port 8000"),
        ("Seeded data",    "5 employees (IDs 1-5) on every start"),
    ]
    for label, val in rows:
        kv(pdf, label + ":", val)

    pdf.ln(4)
    sub_header(pdf, "2.2  Load Generator")
    rows2 = [
        ("Tool",       "Locust 2.32.3"),
        ("Language",   "Python 3.11"),
        ("Script",     "performance_testing/locustfile.py"),
        ("Host",       "Same machine as server (localhost)"),
        ("Reports",    "performance_testing/reports/ (HTML + CSV)"),
        ("Web UI",     "http://localhost:8089  (interactive mode)"),
    ]
    for label, val in rows2:
        kv(pdf, label + ":", val)

    pdf.ln(4)
    sub_header(pdf, "2.3  Prerequisites")
    prereqs = [
        "Python venv activated: .venv/Scripts/activate (Windows) or source .venv/bin/activate (Linux/Mac)",
        "Dependencies installed: pip install -r requirements.txt",
        "API server running: uvicorn main:app --reload --port 8000",
        "Reports directory created: mkdir -p performance_testing/reports",
        "No other services bound to port 8000 or 8089.",
    ]
    for p in prereqs:
        bullet(pdf, f"- {p}")

    pdf.ln(4)
    sub_header(pdf, "2.4  Known Environment Constraints")
    body(pdf,
        "Because both the load generator and the API server run on the same machine, "
        "CPU and memory are shared. Results will be more conservative than production "
        "deployments where the generator runs on a separate host. Treat the numbers as "
        "relative indicators rather than absolute production figures.")


# -- Section 3: KPIs ----------------------------------------------------------

def section_kpis(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 3 - KPIs & Acceptance Criteria")

    body(pdf,
        "Each test run is evaluated against the following key performance indicators (KPIs). "
        "A test PASSES only when ALL applicable criteria are met.")
    pdf.ln(3)

    cols = [("Metric", 50), ("Threshold", 40), ("Applies to", 60), ("Severity if breached", 40)]
    table_header(pdf, cols)
    kpis = [
        ("P50 response time",   "< 200 ms",  "All test types",          "LOW"),
        ("P95 response time",   "< 500 ms",  "All test types",          "HIGH"),
        ("P99 response time",   "< 1000 ms", "All test types",          "HIGH"),
        ("Max response time",   "< 5000 ms", "Load, Stress, Spike",     "MEDIUM"),
        ("Error rate",          "< 1%",      "All test types",          "CRITICAL"),
        ("Throughput (RPS)",    "> 100 RPS", "Load test (50 users)",    "MEDIUM"),
        ("Throughput (RPS)",    "> 300 RPS", "Stress test (200 users)", "MEDIUM"),
        ("P95 - soak drift",    "< 20%",     "Soak test (60 min)",      "HIGH"),
        ("Memory (process)",    "< 500 MB",  "Soak test",               "HIGH"),
        ("No 5xx errors",       "0 allowed", "Baseline, Load",          "CRITICAL"),
    ]
    for i, row in enumerate(kpis):
        table_row(pdf, [(row[0], 50), (row[1], 40), (row[2], 60), (row[3], 40)],
                  shade=(i % 2 == 0))

    pdf.ln(4)
    sub_header(pdf, "3.1  Severity Definitions")
    sevs = [
        ("CRITICAL", RED,    "Test must stop. Blocking defect. Fix before next run."),
        ("HIGH",     ORANGE, "Significant degradation. Must be investigated and resolved."),
        ("MEDIUM",   AMBER,  "Noteworthy gap. Should be addressed in the next sprint."),
        ("LOW",      GREEN_OK, "Minor deviation. Log for awareness; no immediate action needed."),
    ]
    for label, colour, desc in sevs:
        pdf.set_fill_color(*colour)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(22, 5, f"  {label}", fill=True)
        pdf.set_fill_color(*WHITE)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(PAGE_W - 22, 5, f"  {desc}", border="TB")
        pdf.ln()

    pdf.ln(4)
    sub_header(pdf, "3.2  Metrics Captured by Locust")
    metrics = [
        "Request count and failure count per endpoint",
        "Median, P90, P95, P99, and max response times (ms)",
        "Requests per second (RPS) throughput",
        "Failure rate (%) per endpoint",
        "Response size (bytes) statistics",
        "User count over time (ramp graph in HTML report)",
        "Charts: RPS over time, response time over time, user count over time",
    ]
    for m in metrics:
        bullet(pdf, f"- {m}")


# -- Section 4: Scenarios -----------------------------------------------------

def section_scenarios(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 4 - Test Scenarios")

    body(pdf,
        "Five standard scenarios cover the full performance risk profile. Run them in order: "
        "Baseline -> Load -> Stress -> Spike -> Soak. "
        "Each scenario maps to a Locust user class in locustfile.py.")
    pdf.ln(3)

    scenario_card(
        pdf,
        sid="PERF-01", name="Baseline Test",
        users=1, ramp="Instant (1 user)",
        duration="5 minutes",
        wait="1-2 s between tasks",
        task_set="ReadHeavyTasks (GET endpoints only)",
        kpi="P95 < 200 ms, 0 errors",
        cmd=(
            "locust -f performance_testing/locustfile.py --host http://localhost:8000 \\\n"
            "       --headless -u 1 -r 1 --run-time 5m \\\n"
            "       --html performance_testing/reports/baseline_report.html"
        ),
    )

    scenario_card(
        pdf,
        sid="PERF-02", name="Load Test (Normal Traffic)",
        users=50, ramp="5 users/sec over 10 s (reach 50 in ~10 s)",
        duration="10 minutes",
        wait="0.5-2 s between tasks",
        task_set="MixedCRUDTasks (60% read / 40% write)",
        kpi="P95 < 500 ms, error rate < 1%, RPS > 100",
        cmd=(
            "locust -f performance_testing/locustfile.py --host http://localhost:8000 \\\n"
            "       --headless -u 50 -r 5 --run-time 10m \\\n"
            "       --html performance_testing/reports/load_test_report.html \\\n"
            "       --csv  performance_testing/reports/load"
        ),
    )

    scenario_card(
        pdf,
        sid="PERF-03", name="Stress Test (Peak / Overload)",
        users=200, ramp="10 users/sec over 20 s (reach 200 in ~20 s)",
        duration="10 minutes",
        wait="0.1-0.5 s between tasks",
        task_set="MixedCRUDTasks",
        kpi="P95 < 500 ms until breaking point; record exact failure threshold",
        cmd=(
            "locust -f performance_testing/locustfile.py --host http://localhost:8000 \\\n"
            "       --headless -u 200 -r 10 --run-time 10m \\\n"
            "       --html performance_testing/reports/stress_test_report.html \\\n"
            "       --csv  performance_testing/reports/stress"
        ),
    )

    scenario_card(
        pdf,
        sid="PERF-04", name="Spike Test (Sudden Burst)",
        users=500, ramp="500 users/sec (all users spawn at once)",
        duration="2 minutes",
        wait="0-0.2 s between tasks",
        task_set="ReadHeavyTasks (GET-heavy to maximise concurrency pressure)",
        kpi="Error rate < 5% during spike; full recovery within 30 s after drop",
        cmd=(
            "locust -f performance_testing/locustfile.py --host http://localhost:8000 \\\n"
            "       --headless -u 500 -r 500 --run-time 2m \\\n"
            "       --html performance_testing/reports/spike_test_report.html"
        ),
    )

    scenario_card(
        pdf,
        sid="PERF-05", name="Soak Test (Endurance / 60 min)",
        users=20, ramp="2 users/sec over 10 s",
        duration="60 minutes",
        wait="Constant pacing: 1 request / 3 s per user (~7 RPS total)",
        task_set="MixedCRUDTasks",
        kpi="P95 drift < 20% vs baseline, error rate < 1%, no process memory growth > 500 MB",
        cmd=(
            "locust -f performance_testing/locustfile.py --host http://localhost:8000 \\\n"
            "       --headless -u 20 -r 2 --run-time 60m \\\n"
            "       --html performance_testing/reports/soak_test_report.html \\\n"
            "       --csv  performance_testing/reports/soak"
        ),
    )

    sub_header(pdf, "4.1  Task Sets Summary")
    cols = [("Task Set", 48), ("Endpoints Exercised", 80), ("Read/Write Split", 40), ("User Class", 22)]
    table_header(pdf, cols)
    rows = [
        ("ReadHeavyTasks",  "GET /api/employees, GET /api/employees/{id}, GET ?dept, GET ?name",
         "100% read",  "Baseline, Spike"),
        ("WriteHeavyTasks", "POST /api/employees, PUT, PATCH, POST /departments/{dept}/employees",
         "100% write", "Standalone stress"),
        ("MixedCRUDTasks",  "All 7 endpoints including DELETE with pre-created employee",
         "60/40",      "Load, Stress, Soak"),
    ]
    for i, row in enumerate(rows):
        table_row(pdf, [(row[0], 48), (row[1], 80), (row[2], 40), (row[3], 22)],
                  shade=(i % 2 == 0))


# -- Section 5: Locust Setup --------------------------------------------------

def section_setup(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 5 - Locust Setup & Run Guide")

    sub_header(pdf, "5.1  Install & Activate")
    cmds = [
        "# From ApiTestsPython directory",
        "python -m venv .venv",
        ".venv/Scripts/activate          # Windows",
        "# source .venv/bin/activate     # Linux / Mac",
        "pip install -r requirements.txt",
        "",
        "# Verify locust installed",
        "locust --version                # Expected: locust 2.32.3",
    ]
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(PAGE_W, 4, "\n".join(cmds), border=1, fill=True)

    pdf.ln(4)
    sub_header(pdf, "5.2  Start API Server (separate terminal)")
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(PAGE_W, 4,
        "cd ApiTestsPython\n"
        ".venv/Scripts/activate\n"
        "uvicorn main:app --reload --port 8000",
        border=1, fill=True)

    pdf.ln(4)
    sub_header(pdf, "5.3  Create Reports Directory")
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(PAGE_W, 4,
        "mkdir -p performance_testing/reports   # Linux/Mac\n"
        "mkdir performance_testing\\reports      # Windows",
        border=1, fill=True)

    pdf.ln(4)
    sub_header(pdf, "5.4  Interactive Mode (Web UI)")
    body(pdf,
        "Start Locust without --headless to open the web UI at http://localhost:8089. "
        "Enter the number of users, ramp rate, and host in the browser, then start/stop "
        "the test interactively. Charts update in real time.")
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(PAGE_W, 4,
        "locust -f performance_testing/locustfile.py --host http://localhost:8000\n"
        "# Then open: http://localhost:8089",
        border=1, fill=True)

    pdf.ln(4)
    sub_header(pdf, "5.5  Custom User Class Selection")
    body(pdf,
        "By default all user classes are active. To isolate a single scenario, "
        "pass the class name to --class-picker in the web UI or use the class name directly:")
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(PAGE_W, 4,
        "# Run only the SoakTestUser class\n"
        "locust -f performance_testing/locustfile.py SoakTestUser \\\n"
        "       --host http://localhost:8000 --headless -u 20 -r 2 --run-time 60m",
        border=1, fill=True)

    pdf.ln(4)
    sub_header(pdf, "5.6  Locust CLI Reference")
    cols = [("Flag", 45), ("Description", 100), ("Example", 45)]
    table_header(pdf, cols)
    flags = [
        ("-f FILE",          "Locust file path",                        "-f performance_testing/locustfile.py"),
        ("--host URL",       "Base URL of the system under test",        "--host http://localhost:8000"),
        ("--headless",       "Run without web UI",                       "--headless"),
        ("-u N",             "Peak number of concurrent users",          "-u 50"),
        ("-r N",             "Users spawned per second (ramp rate)",     "-r 5"),
        ("--run-time T",     "Stop after time (e.g. 10m, 1h)",           "--run-time 10m"),
        ("--html FILE",      "Save HTML report to file",                 "--html reports/load.html"),
        ("--csv PREFIX",     "Save CSV stats, failures, history files",  "--csv reports/load"),
        ("--logfile FILE",   "Write log to file",                        "--logfile reports/run.log"),
        ("--loglevel LEVEL", "Log verbosity (DEBUG/INFO/WARNING)",       "--loglevel INFO"),
        ("--stop-timeout N", "Wait N sec for users to finish on stop",   "--stop-timeout 30"),
    ]
    for i, row in enumerate(flags):
        table_row(pdf, [(row[0], 45), (row[1], 100), (row[2], 45)], shade=(i % 2 == 0))


# -- Section 6: Test Cases (per endpoint) -------------------------------------

def section_test_cases(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 6 - Per-Endpoint Test Cases")

    body(pdf,
        "The table below lists individual endpoint-level performance checks within "
        "the load test scenario (PERF-02, 50 users, 10 min). Results are captured "
        "in the CSV files per endpoint name as configured in locustfile.py.")
    pdf.ln(3)

    cols = [("TC ID", 20), ("Endpoint", 68), ("Task", 52), ("Expected P95", 30), ("Expected Err%", 20)]
    table_header(pdf, cols)
    cases = [
        ("PT-01", "GET /api/employees",                       "List all employees",               "< 500 ms", "< 1%"),
        ("PT-02", "GET /api/employees?department",            "Filter by department param",        "< 500 ms", "< 1%"),
        ("PT-03", "GET /api/employees?name",                  "Filter by name param",              "< 500 ms", "< 1%"),
        ("PT-04", "GET /api/employees/{id}",                  "Get single employee by ID",         "< 300 ms", "< 1%"),
        ("PT-05", "POST /api/employees",                      "Create employee",                   "< 500 ms", "< 1%"),
        ("PT-06", "POST /api/departments/{dept}/employees",   "Create via department path",        "< 500 ms", "< 1%"),
        ("PT-07", "PUT /api/employees/{id}",                  "Full update (seeded + created IDs)","< 500 ms", "< 1%"),
        ("PT-08", "PATCH /api/employees/{id}",                "Partial update salary only",        "< 500 ms", "< 1%"),
        ("PT-09", "DELETE /api/employees/{id}",               "Delete temp employee (create first)","< 500 ms","< 1%"),
        ("PT-10", "POST (for delete)",                        "Pre-create for DELETE test",        "< 500 ms", "< 1%"),
    ]
    for i, row in enumerate(cases):
        table_row(pdf,
                  [(row[0], 20), (row[1], 68), (row[2], 52), (row[3], 30), (row[4], 20)],
                  shade=(i % 2 == 0))

    pdf.ln(4)
    sub_header(pdf, "6.1  Auth & Header Validation Under Load")
    body(pdf,
        "All Locust tasks send X-API-Key: secret123 and Accept: application/json. "
        "Any 401 or 406 response is counted as an error by Locust and will push the "
        "error rate above the 1% threshold, causing the test to fail the KPI criteria. "
        "This means header validation correctness is implicitly tested on every request.")

    pdf.ln(4)
    sub_header(pdf, "6.2  404 Handling")
    body(pdf,
        "PUT and PATCH tasks may target a previously-deleted or non-existent ID. "
        "The Locust tasks treat both 200 and 404 as success (catch_response=True) to "
        "avoid false-positive error counts. This isolates latency measurement from "
        "application-level not-found responses.")


# -- Section 7: Results template ----------------------------------------------

def section_results(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 7 - Results Log (Fill After Each Run)")

    body(pdf,
        "Complete one row per test run. Attach the HTML report and CSV files to the "
        "test record. Mark Pass (P) or Fail (F) against each KPI column.")
    pdf.ln(3)

    cols = [
        ("Run #",     12), ("Scenario",  32), ("Date",     22),
        ("Users",     15), ("RPS",       15), ("P95 ms",   18),
        ("P99 ms",    18), ("Err %",     18), ("P/F",      10), ("Notes", 30),
    ]
    table_header(pdf, cols)
    for i in range(10):
        shade = (i % 2 == 0)
        table_row(pdf,
                  [("", 12), ("", 32), ("", 22), ("", 15), ("", 15),
                   ("", 18), ("", 18), ("", 18), ("", 10), ("", 30)],
                  shade=shade)

    pdf.ln(5)
    sub_header(pdf, "7.1  Soak Test Drift Checklist")
    soak_checks = [
        ("Check",                             "Minute 5", "Minute 30", "Minute 60", "Pass/Fail"),
        ("P95 response time (ms)",            "",         "",          "",          ""),
        ("Error rate (%)",                    "",         "",          "",          ""),
        ("Active user count (should be 20)",  "",         "",          "",          ""),
        ("Process memory (MB)",               "",         "",          "",          ""),
        ("Employee count (GET /api/employees)", "",       "",          "",          ""),
    ]
    cols2 = [("Check", 75), ("Min 5", 25), ("Min 30", 25), ("Min 60", 25), ("Pass/Fail", 40)]
    table_header(pdf, cols2)
    for i, row in enumerate(soak_checks[1:]):
        table_row(pdf,
                  [(row[0], 75), (row[1], 25), (row[2], 25), (row[3], 25), (row[4], 40)],
                  shade=(i % 2 == 0))


# -- Section 8: Analysis guide ------------------------------------------------

def section_analysis(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 8 - Reading & Analysing Results")

    sub_header(pdf, "8.1  HTML Report Sections")
    items = [
        ("Charts tab",         "RPS over time, response time percentiles over time, user count "
                               "ramp. Look for flat lines (stable) vs rising trends (degradation)."),
        ("Statistics tab",     "Per-endpoint breakdown of request count, failure count, "
                               "median / P90 / P95 / P99 / max response times, avg size, RPS."),
        ("Failures tab",       "Lists all unique failure messages with counts. "
                               "5xx errors indicate server-side crashes; 4xx indicate logic issues."),
        ("Exceptions tab",     "Python exceptions from the Locust workers (e.g., connection refused). "
                               "These count as failures and appear in the error rate."),
        ("Download Data tab",  "Export CSV for post-processing in Excel or pandas."),
    ]
    for label, desc in items:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(L_MARGIN + 4)
        pdf.cell(42, 5, label)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(PAGE_W - 46, 5, desc)

    pdf.ln(3)
    sub_header(pdf, "8.2  Common Failure Patterns")
    patterns = [
        ("Error rate spikes at N users",
         "N is the concurrency breaking point. The in-memory store has no locking, "
         "so race conditions on the ID counter may produce duplicate IDs under very "
         "high write concurrency."),
        ("P99 rises while P50 stays flat",
         "Indicates occasional slow outliers (GIL contention, OS scheduling). "
         "Not a systemic issue unless P99 > 1000 ms."),
        ("Steady RPS drop over time (soak)",
         "Memory pressure from growing in-memory store (unbounded POST creates). "
         "The locustfile creates employees and only deletes them in delete_and_recreate "
         "tasks - the store grows throughout a long run."),
        ("Connection refused / timeout",
         "Uvicorn default worker limit reached. "
         "Try: uvicorn main:app --reload --port 8000 --workers 4"),
        ("401 errors in results",
         "Locust task bug - check HEADERS dict in locustfile.py. "
         "All tasks should send X-API-Key: secret123."),
    ]
    for pattern, explanation in patterns:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(L_MARGIN + 4)
        pdf.multi_cell(PAGE_W - 4, 5, pattern)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(L_MARGIN + 8)
        pdf.multi_cell(PAGE_W - 8, 5, explanation)
        pdf.ln(1)

    pdf.ln(3)
    sub_header(pdf, "8.3  Recommended Tuning Commands")
    tuning = [
        "# Increase Uvicorn workers to reduce GIL bottleneck",
        "uvicorn main:app --port 8000 --workers 4",
        "",
        "# Run Locust with a custom CSV history interval (default 1 s)",
        "locust ... --csv-full-history",
        "",
        "# Print real-time stats to stdout every 10 s",
        "locust ... --print-stats",
        "",
        "# Stop test automatically if error rate exceeds 5%",
        "# (set in locustfile.py via @events.quitting.add_listener)",
    ]
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_font("Courier", "", 7)
    pdf.multi_cell(PAGE_W, 4, "\n".join(tuning), border=1, fill=True)


# -- Section 9: Remediation ---------------------------------------------------

def section_remediation(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 9 - Performance Risks & Recommended Fixes")

    body(pdf,
        "The following risks are inherent to the current Employee API implementation. "
        "They are expected to appear during performance testing and should be addressed "
        "to improve production readiness.")
    pdf.ln(3)

    risks = [
        ("RISK-01", "HIGH",
         "No rate limiting - API accepts unlimited requests",
         "All endpoints, especially POST",
         "Add slowapi middleware:\n"
         "  pip install slowapi\n"
         "  from slowapi import Limiter\n"
         "  @limiter.limit('100/minute')"),

        ("RISK-02", "HIGH",
         "In-memory store grows unbounded under POST load",
         "POST /api/employees",
         "Add max employee count check in router:\n"
         "  if len(employees) >= MAX_EMPLOYEES: raise HTTPException(503)"),

        ("RISK-03", "HIGH",
         "No request body size limit - large payloads accepted",
         "POST, PUT, PATCH",
         "Add ASGI middleware:\n"
         "  app.add_middleware(ContentSizeLimitMiddleware, max_content_size=65536)"),

        ("RISK-04", "MEDIUM",
         "GIL limits single-process throughput under high concurrency",
         "All endpoints",
         "Run multiple Uvicorn workers:\n"
         "  uvicorn main:app --workers 4 --port 8000\n"
         "  (note: in-memory store is NOT shared across workers)"),

        ("RISK-05", "MEDIUM",
         "Sequential integer IDs are predictable and enumerable",
         "GET, PUT, PATCH, DELETE /{id}",
         "Switch to UUID v4 for employee IDs:\n"
         "  import uuid\n"
         "  new_id = str(uuid.uuid4())"),

        ("RISK-06", "MEDIUM",
         "No concurrency control on shared in-memory dict",
         "All write endpoints under concurrent load",
         "Add threading.Lock() around all reads/writes to employees dict "
         "in data/store.py to prevent race conditions."),

        ("RISK-07", "LOW",
         "No connection keep-alive tuning or response compression",
         "GET /api/employees (large lists)",
         "Add GZip middleware for large responses:\n"
         "  from fastapi.middleware.gzip import GZipMiddleware\n"
         "  app.add_middleware(GZipMiddleware, minimum_size=1000)"),
    ]

    for rid, severity, description, affected, fix in risks:
        if pdf.get_y() + 38 > pdf.h - pdf.b_margin:
            pdf.add_page()

        # Title bar
        sev_colour = {"CRITICAL": RED, "HIGH": ORANGE, "MEDIUM": AMBER,
                      "LOW": GREEN_OK}.get(severity, GREY_MED)
        pdf.set_fill_color(*GREEN_DARK)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(PAGE_W - 22, 6, f"  {rid}  -  {description}", fill=True)
        pdf.set_fill_color(*sev_colour)
        pdf.cell(22, 6, f"  {severity}", fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        # Detail rows
        for i, (label, val) in enumerate([("Affected", affected), ("Recommended fix", fix)]):
            bg = GREEN_LIGHT if i % 2 == 0 else WHITE
            pdf.set_fill_color(*bg)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(30, 5, f"  {label}", border="LTB", fill=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(PAGE_W - 30, 5, f"  {val}", border="RTB", fill=True)

        pdf.ln(3)


# -- Main ---------------------------------------------------------------------

def main():
    pdf = PDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(L_MARGIN, 10, L_MARGIN)

    cover_page(pdf)
    section_overview(pdf)
    section_environment(pdf)
    section_kpis(pdf)
    section_scenarios(pdf)
    section_setup(pdf)
    section_test_cases(pdf)
    section_results(pdf)
    section_analysis(pdf)
    section_remediation(pdf)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "Employee_API_Performance_Test_Plan.pdf")
    pdf.output(out_path)
    print(f"PDF saved to: {out_path}")


if __name__ == "__main__":
    main()
