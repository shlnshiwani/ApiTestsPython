"""
generate_report.py
~~~~~~~~~~~~~~~~~~
Generates the Employee REST API Security & Penetration Testing Plan as a PDF.

Usage:
    cd ApiTestsPython
    python security_testing/generate_report.py

Output:
    security_testing/Employee_API_Security_Test_Plan.pdf
"""

from fpdf import FPDF, XPos, YPos
from datetime import date
import os

# -- Colour palette -------------------------------------------------------------
BLUE_DARK   = (0,   70,  127)   # section header background
BLUE_MID    = (0,  102,  179)   # table column header background
BLUE_LIGHT  = (220, 235, 248)   # alternating row tint
WHITE       = (255, 255, 255)
GREY_LIGHT  = (245, 245, 245)
RED         = (192,  0,   0)
ORANGE      = (210, 100,   0)
AMBER       = (160, 120,   0)
GREEN       = ( 30, 130,  60)
GREY_MED    = (100, 100, 100)

PAGE_W      = 190   # usable width (A4 210mm - 2×10mm margins)
L_MARGIN    = 10


# -- Custom PDF class -----------------------------------------------------------

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return                          # cover page has its own layout
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GREY_MED)
        self.cell(0, 5, "Employee REST API  -  Security & Penetration Testing Plan", align="L")
        self.set_xy(L_MARGIN, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")
        self.ln(3)
        self.set_draw_color(*BLUE_DARK)
        self.line(L_MARGIN, self.get_y(), L_MARGIN + PAGE_W, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY_MED)
        self.cell(0, 8, "CONFIDENTIAL  -  Authorised Security Testing Use Only", align="C")
        self.set_text_color(0, 0, 0)


# -- Helper utilities -----------------------------------------------------------

def section_header(pdf: PDF, text: str):
    """Bold coloured band with white section title."""
    pdf.ln(3)
    pdf.set_fill_color(*BLUE_DARK)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(PAGE_W, 8, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def sub_header(pdf: PDF, text: str):
    """Smaller tinted sub-section label."""
    pdf.set_fill_color(*BLUE_LIGHT)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(PAGE_W, 6, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def body(pdf: PDF, text: str, indent: int = 0):
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(L_MARGIN + indent)
    pdf.multi_cell(PAGE_W - indent, 5, text)


def bullet(pdf: PDF, text: str, indent: int = 4):
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(L_MARGIN + indent)
    pdf.cell(4, 5, "\u2022")
    pdf.multi_cell(PAGE_W - indent - 4, 5, text)


def _line_count(pdf: PDF, text: str, width: float, font_size: int = 8) -> int:
    """Estimate how many wrapped lines `text` needs inside `width` mm."""
    pdf.set_font("Helvetica", "", font_size)
    words = str(text).split()
    lines, cur = 1, 0.0
    for word in words:
        w = pdf.get_string_width(word + " ")
        if cur + w > width - 2 and cur > 0:
            lines += 1
            cur = w
        else:
            cur += w
    return max(lines, 1)


def table_header(pdf: PDF, headers: list[str], widths: list[float], row_h: float = 6):
    """Draw the column-header row of a table."""
    pdf.set_fill_color(*BLUE_MID)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for text, w in zip(headers, widths):
        pdf.cell(w, row_h, f" {text}", border=1, fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


def table_row(pdf: PDF, cells: list[str], widths: list[float],
              fill: bool = False, line_h: float = 5):
    """Draw one data row, handling multi-line text and page breaks."""
    fill_color = BLUE_LIGHT if fill else WHITE
    pdf.set_fill_color(*fill_color)
    pdf.set_font("Helvetica", "", 8)

    x0, y0 = L_MARGIN, pdf.get_y()

    # Calculate the tallest cell in this row
    max_lines = max(_line_count(pdf, c, w) for c, w in zip(cells, widths))
    row_h_total = max_lines * line_h

    # Page break if needed
    if y0 + row_h_total > pdf.h - pdf.b_margin - 5:
        pdf.add_page()
        x0, y0 = L_MARGIN, pdf.get_y()

    x = x0
    for text, w in zip(cells, widths):
        pdf.set_xy(x, y0)
        pdf.multi_cell(w, line_h, f" {text}", border=1, fill=True, align="L",
                       max_line_height=line_h)
        x += w

    pdf.set_y(y0 + row_h_total)


def severity_badge(pdf: PDF, level: str):
    colours = {
        "CRITICAL": RED, "HIGH": ORANGE,
        "MEDIUM": AMBER, "LOW": GREEN, "INFO": GREY_MED,
    }
    c = colours.get(level.upper(), GREY_MED)
    pdf.set_fill_color(*c)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(22, 5, f" {level}", border=0, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(*WHITE)


def test_card(pdf: PDF, tid: str, severity: str, title: str,
              endpoint: str, steps: str, payload: str, expected: str):
    """Render one test case as a self-contained bordered card."""
    card_h_est = 40
    if pdf.get_y() + card_h_est > pdf.h - pdf.b_margin:
        pdf.add_page()

    y_top = pdf.get_y()
    pdf.set_fill_color(*GREY_LIGHT)
    pdf.set_draw_color(*BLUE_DARK)
    pdf.set_line_width(0.3)

    # Card title bar
    pdf.set_fill_color(*BLUE_LIGHT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(22, 6, f" {tid}", border="TLB", fill=True)
    severity_badge(pdf, severity)
    pdf.set_fill_color(*BLUE_LIGHT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(PAGE_W - 22 - 22, 6, f"  {title}", border="TRB", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Detail rows
    label_w, val_w = 28, PAGE_W - 28

    def detail_row(label, value):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(label_w, 5, f"  {label}:", border="LR", fill=False)
        pdf.set_font("Helvetica", "", 8)
        lines = _line_count(pdf, value, val_w)
        y_before = pdf.get_y()
        pdf.multi_cell(val_w, 5, f" {value}", border="R", fill=False,
                       max_line_height=5)
        pdf.set_y(max(pdf.get_y(), y_before + 5))

    detail_row("Endpoint", endpoint)
    detail_row("Steps", steps)
    detail_row("Payload", payload)
    detail_row("Expected", expected)

    # Result + Pass/Fail row
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(label_w, 5, "  Actual Result:", border="LRB", fill=False)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(val_w - 38, 5, "", border="B", fill=False)
    pdf.cell(38, 5, "  Pass / Fail: _____", border="RB", fill=False, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.ln(2)


# -- Section builders -----------------------------------------------------------

def cover_page(pdf: PDF):
    pdf.add_page()
    pdf.ln(40)

    # Big title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*BLUE_DARK)
    pdf.cell(PAGE_W, 12, "Employee REST API", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(PAGE_W, 10, "Security & Penetration Testing Plan", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Coloured rule
    pdf.ln(4)
    pdf.set_draw_color(*BLUE_DARK)
    pdf.set_line_width(1)
    pdf.line(L_MARGIN + 20, pdf.get_y(), L_MARGIN + PAGE_W - 20, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(8)

    # Meta block
    pdf.set_text_color(*GREY_MED)
    pdf.set_font("Helvetica", "", 11)
    meta = [
        ("Target API",  "http://localhost:8000"),
        ("Framework",   "FastAPI (Python)"),
        ("Methodology", "OWASP API Security Top 10 (2023)"),
        ("Document",    "Version 1.0"),
        ("Date",        date.today().strftime("%B %d, %Y")),
        ("Status",      "DRAFT - Fill results during execution"),
    ]
    for label, value in meta:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(L_MARGIN + 30)
        pdf.cell(40, 7, label + ":", align="R")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(100, 7, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(16)
    pdf.set_fill_color(255, 230, 230)
    pdf.set_draw_color(192, 0, 0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*RED)
    pdf.cell(PAGE_W, 7,
             "  CONFIDENTIAL - Authorised Security Testing Use Only",
             border=1, fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)


def section_api_under_test(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 1 - API Under Test")

    body(pdf, "Base URL:  http://localhost:8000\n"
              "Authentication:  X-API-Key header  (value: secret123)\n"
              "Accept header:   application/json  (or */*)\n"
              "Data store:      In-memory Python dict - resets on server restart\n"
              "Swagger UI:      http://localhost:8000/docs")
    pdf.ln(3)

    sub_header(pdf, "1.1  Endpoints")
    hdrs = ["Method", "Path", "Query Params", "Path Var", "Auth?", "Responses"]
    wids = [16, 62, 38, 20, 13, 41]
    table_header(pdf, hdrs, wids)
    rows = [
        ["GET",   "/api/employees",                       "department, position, name", "-",          "Yes", "200, 401, 406"],
        ["GET",   "/api/employees/{id}",                  "-",                          "employee_id", "Yes", "200, 401, 404, 406"],
        ["POST",  "/api/employees",                       "-",                          "-",           "Yes", "201, 401, 406, 422"],
        ["POST",  "/api/departments/{dept}/employees",    "-",                          "department",  "Yes", "201, 401, 406, 422"],
        ["PUT",   "/api/employees/{id}",                  "-",                          "employee_id", "Yes", "200, 401, 404, 406, 422"],
        ["PATCH", "/api/employees/{id}",                  "-",                          "employee_id", "Yes", "200, 401, 404, 406, 422"],
        ["DELETE","/api/employees/{id}",                  "-",                          "employee_id", "Yes", "204, 401, 404, 406"],
    ]
    for i, row in enumerate(rows):
        table_row(pdf, row, wids, fill=(i % 2 == 0))
    pdf.ln(4)

    sub_header(pdf, "1.2  Seeded Test Data (5 employees pre-loaded)")
    hdrs2 = ["ID", "Name", "Email", "Department", "Position", "Salary"]
    wids2 = [10, 38, 48, 30, 38, 26]
    table_header(pdf, hdrs2, wids2)
    seeds = [
        ["1", "Alice Johnson",  "alice@example.com",  "Engineering", "Senior Engineer",    "$95,000"],
        ["2", "Bob Smith",      "bob@example.com",    "Marketing",   "Marketing Manager",  "$75,000"],
        ["3", "Carol White",    "carol@example.com",  "Engineering", "Junior Engineer",    "$65,000"],
        ["4", "David Brown",    "david@example.com",  "HR",          "HR Specialist",      "$60,000"],
        ["5", "Eva Martinez",   "eva@example.com",    "Finance",     "Finance Analyst",    "$70,000"],
    ]
    for i, row in enumerate(seeds):
        table_row(pdf, row, wids2, fill=(i % 2 == 0))


def section_static_findings(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 2 - Static Analysis Findings")
    body(pdf, "The following vulnerabilities were identified by reading the source code "
              "before executing any tests. These are confirmed issues requiring remediation.")
    pdf.ln(3)

    findings = [
        ("CRITICAL", "SEC-F01", "Hardcoded API Key in Source Code",
         "VALID_API_KEY = \"secret123\" is hardcoded in dependencies/headers.py. "
         "Anyone with source access knows the key. Fix: load from environment variable."),
        ("HIGH",     "SEC-F02", "Wildcard CORS Configuration",
         "allow_origins=[\"*\"] in main.py permits any domain to call the API from a browser, "
         "enabling cross-site request forgery-style attacks from malicious websites."),
        ("HIGH",     "SEC-F03", "No Rate Limiting or Brute-Force Protection",
         "Unlimited requests are accepted per second. An attacker can enumerate all employee "
         "IDs, brute-force API keys, or exhaust server resources with no throttling."),
        ("HIGH",     "SEC-F04", "Predictable Sequential Integer IDs",
         "Employee IDs start at 1 and auto-increment (1, 2, 3...). An attacker can enumerate "
         "all valid IDs and access any employee record without authorisation."),
        ("MEDIUM",   "SEC-F05", "No Request Body Size Limit",
         "FastAPI/uvicorn default accepts unlimited body sizes. A POST with a megabyte-sized "
         "name field will be accepted, risking memory exhaustion."),
        ("MEDIUM",   "SEC-F06", "No Concurrency Control on In-Memory Store",
         "The employees dict is mutated directly without locks. Concurrent POST requests "
         "may trigger race conditions leading to ID collisions or corrupted state."),
        ("MEDIUM",   "SEC-F07", "No Input Length Validation on department / position",
         "These fields have no max_length constraint. Arbitrarily long strings are accepted "
         "and stored, which can bloat memory and skew search results."),
        ("LOW",      "SEC-F08", "Missing HTTP Security Response Headers",
         "Responses lack: X-Content-Type-Options, X-Frame-Options, Content-Security-Policy, "
         "and Strict-Transport-Security. These are defence-in-depth controls."),
        ("LOW",      "SEC-F09", "Server Version Disclosed in Response Headers",
         "uvicorn adds a 'server: uvicorn' header, revealing the server software and version "
         "to attackers who can then target known vulnerabilities for that version."),
        ("INFO",     "SEC-F10", "API Key Hint Visible in Swagger UI",
         "The OpenAPI description contains '(value: secret123)' in the security scheme "
         "description, advertising the valid API key to anyone who opens /docs."),
    ]

    hdrs = ["ID", "Severity", "Finding", "Description"]
    wids = [18, 20, 48, 104]
    table_header(pdf, hdrs, wids)
    for i, (sev, fid, title, desc) in enumerate(findings):
        table_row(pdf, [fid, sev, title, desc], wids, fill=(i % 2 == 0))


def section_methodology(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 3 - Testing Methodology (OWASP API Security Top 10, 2023)")

    body(pdf, "All test cases in this document are mapped to the OWASP API Security Top 10 "
              "(2023 edition). Each category identifies the most critical API security risks "
              "and the corresponding test approach for this Employee API.")
    pdf.ln(4)

    owasp = [
        ("API1",  "Broken Object Level Authorization (BOLA / IDOR)",
         "Test whether any authenticated user can access or modify any employee by ID, "
         "regardless of ownership. The API has no per-user scoping."),
        ("API2",  "Broken Authentication",
         "Test weak/missing API key enforcement: missing header, wrong value, brute force, "
         "key in query string, SQLi in key value."),
        ("API3",  "Broken Object Property Level Authorization",
         "Test whether mass assignment or over-posting allows setting fields that "
         "should be server-controlled (e.g. setting id directly in POST body)."),
        ("API4",  "Unrestricted Resource Consumption",
         "Test for rate limiting absence, large payload acceptance, and repeated POST "
         "to fill in-memory store (memory exhaustion / DoS)."),
        ("API5",  "Broken Function Level Authorization",
         "Test whether DELETE and PUT operations are accessible to all valid API key "
         "holders with no role separation (any key can destroy any record)."),
        ("API6",  "Unrestricted Access to Sensitive Business Flows",
         "Test business logic: duplicate emails accepted, no uniqueness constraint, "
         "no audit trail for deletions, no soft-delete protection."),
        ("API7",  "Server-Side Request Forgery (SSRF)",
         "Low risk for this API (no URL-accepting fields), but test if the department "
         "or position fields accepting URLs could trigger outbound requests."),
        ("API8",  "Security Misconfiguration",
         "Test CORS wildcard, missing security headers, Swagger UI exposure, HTTP (no TLS), "
         "stack trace leakage, and server version disclosure."),
        ("API9",  "Improper Inventory Management",
         "Verify that Swagger (/docs) and ReDoc (/redoc) are discoverable and whether "
         "they expose more than intended (e.g. internal API key hints)."),
        ("API10", "Unsafe Consumption of APIs",
         "Test that input from external sources (query params, path vars, body) is "
         "properly validated and does not cause unintended behaviour when malformed."),
    ]

    hdrs = ["OWASP ID", "Category", "Test Approach for This API"]
    wids = [18, 58, 114]
    table_header(pdf, hdrs, wids)
    for i, (oid, cat, approach) in enumerate(owasp):
        table_row(pdf, [oid, cat, approach], wids, fill=(i % 2 == 0))


def section_test_cases(pdf: PDF):
    # -- 4.1 Authentication ----------------------------------------------------
    pdf.add_page()
    section_header(pdf, "Section 4 - Test Cases")
    sub_header(pdf, "4.1  Authentication & Authorization  (OWASP API2)")

    auth_tests = [
        ("AUTH-01", "CRITICAL", "Missing X-API-Key Header",
         "ALL endpoints",
         "Send a valid request with no X-API-Key header",
         "No X-API-Key header",
         "HTTP 401 Unauthorized"),
        ("AUTH-02", "CRITICAL", "Wrong API Key Value",
         "GET /api/employees/1",
         "Send request with X-API-Key: wrongvalue",
         "X-API-Key: wrongvalue",
         "HTTP 401 Unauthorized"),
        ("AUTH-03", "HIGH", "Empty API Key",
         "GET /api/employees/1",
         "Send request with X-API-Key header set to empty string",
         "X-API-Key: (empty string)",
         "HTTP 401 Unauthorized"),
        ("AUTH-04", "HIGH", "API Key Passed as Query Parameter",
         "GET /api/employees?api_key=secret123",
         "Omit X-API-Key header; pass key in query string instead",
         "?api_key=secret123 (no header)",
         "HTTP 401 - query param must not substitute for header"),
        ("AUTH-05", "MEDIUM", "SQLi Payload in API Key",
         "GET /api/employees/1",
         "Send X-API-Key with a SQL injection string",
         "X-API-Key: ' OR '1'='1",
         "HTTP 401 - injection must not bypass auth check"),
        ("AUTH-06", "HIGH", "Brute-Force API Key (No Lockout)",
         "GET /api/employees/1",
         "Send 20 requests with sequential wrong keys, then correct key",
         "X-API-Key: aaa, bbb, ... secret123",
         "All 401 until correct key - confirm no lockout mechanism exists"),
    ]
    for t in auth_tests:
        test_card(pdf, *t)

    # -- 4.2 BOLA / IDOR -------------------------------------------------------
    sub_header(pdf, "4.2  BOLA / IDOR - Broken Object Level Authorization  (OWASP API1)")
    bola_tests = [
        ("BOLA-01", "HIGH", "Enumerate All Employee IDs",
         "GET /api/employees/{id}",
         "Sequentially request IDs 1 through 10; record which exist",
         "IDs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10",
         "IDs 1-5 return 200; confirms enumeration is trivially possible"),
        ("BOLA-02", "HIGH", "Predict Next Created Employee ID",
         "POST /api/employees then GET /api/employees/{n+1}",
         "Create an employee; note returned ID; GET id+1 immediately",
         "POST body: valid employee JSON",
         "Consecutive ID returned - predictable ID sequence confirmed"),
        ("BOLA-03", "HIGH", "Delete Any Employee Without Ownership Check",
         "DELETE /api/employees/1",
         "Delete employee ID 1 using any valid API key",
         "Valid X-API-Key: secret123",
         "204 No Content - no ownership or role check exists"),
        ("BOLA-04", "HIGH", "Modify Any Employee Without Ownership Check",
         "PUT /api/employees/1",
         "Replace all fields of employee ID 1 with arbitrary data",
         "Full EmployeeUpdate JSON body",
         "200 - anyone with API key can overwrite any record"),
    ]
    for t in bola_tests:
        test_card(pdf, *t)

    # -- 4.3 Input Validation & Injection --------------------------------------
    pdf.add_page()
    sub_header(pdf, "4.3  Input Validation & Injection  (OWASP API3, API10)")
    inj_tests = [
        ("INJ-01", "MEDIUM", "XSS Payload in name Field",
         "POST /api/employees",
         "Send a POST body with a script tag in the name field",
         'name: "<script>alert(1)</script>"',
         "Accepted (201) and echoed unescaped - confirms no sanitisation"),
        ("INJ-02", "MEDIUM", "HTML Injection in department Field",
         "POST /api/employees",
         "Send HTML tags in the department field",
         'department: "<h1>Injected</h1>"',
         "Accepted and stored - output encoding not applied"),
        ("INJ-03", "LOW", "SQL Injection in name Field",
         "POST /api/employees",
         "Send classic SQL injection string in name",
         "name: \"'; DROP TABLE employees;--\"",
         "201 - in-memory store, no SQL; confirm no crash or exception"),
        ("INJ-04", "LOW", "SQL Injection in Query Parameter",
         "GET /api/employees?department=Engineering' OR '1'='1",
         "Inject SQL operator into department query param",
         "?department=Engineering' OR '1'='1",
         "200 empty list - in-memory filter, no SQL; confirm no data leak"),
        ("INJ-05", "MEDIUM", "Null Byte Injection in name",
         "POST /api/employees",
         "Send a name containing a null byte character",
         'name: "Alice\\x00Admin"',
         "422 or 201 - document actual behaviour"),
        ("INJ-06", "LOW", "Unicode / Emoji in name Field",
         "POST /api/employees",
         "Send a name containing emoji and multi-byte unicode characters",
         'name: "\\U0001F468\\u200D\\U0001F4BB Employee"',
         "201 - accepted; confirm no encoding error or crash"),
        ("INJ-07", "LOW", "Maximum Length name (boundary: 100 chars)",
         "POST /api/employees",
         "Send name exactly 100 characters long (max_length=100)",
         "name: 'A' * 100",
         "201 Created - boundary accepted"),
        ("INJ-08", "MEDIUM", "Oversized name (101 chars - exceeds max_length)",
         "POST /api/employees",
         "Send name with 101 characters",
         "name: 'A' * 101",
         "422 Unprocessable Entity - Pydantic rejects over-length field"),
        ("INJ-09", "MEDIUM", "Zero Salary (violates gt=0 constraint)",
         "POST /api/employees",
         "Send salary = 0 in the request body",
         "salary: 0",
         "422 Unprocessable Entity - gt=0 violated"),
        ("INJ-10", "MEDIUM", "Negative Salary",
         "POST /api/employees",
         "Send a negative value for salary",
         "salary: -5000",
         "422 Unprocessable Entity - negative violates gt=0"),
        ("INJ-11", "HIGH", "Extremely Large Salary (no upper bound)",
         "POST /api/employees",
         "Send salary = 1e308 (max float)",
         "salary: 1e308",
         "201 Created - no upper bound exists (VULNERABILITY)"),
        ("INJ-12", "LOW", "Invalid Email Format",
         "POST /api/employees",
         "Send a non-email string in the email field",
         'email: "notanemail"',
         "422 Unprocessable Entity - Pydantic EmailStr rejects it"),
        ("INJ-13", "MEDIUM", "Path Traversal in department Path Variable",
         "POST /api/departments/../admin/employees",
         "Use ../ in the department path variable to attempt traversal",
         "department path var: '../admin'",
         "404 or 422 - traversal must not affect routing or file access"),
        ("INJ-14", "MEDIUM", "Very Long department Path Variable",
         "POST /api/departments/{10000_chars}/employees",
         "Send a department name of 10,000 characters in the URL path",
         "path var: 'A' * 10000",
         "201 or 414 URI Too Long - server must not crash"),
    ]
    for t in inj_tests:
        test_card(pdf, *t)

    # -- 4.4 Security Misconfiguration -----------------------------------------
    pdf.add_page()
    sub_header(pdf, "4.4  Security Misconfiguration  (OWASP API8)")
    conf_tests = [
        ("CONF-01", "HIGH", "CORS - Any Origin Allowed",
         "OPTIONS /api/employees",
         "Send a preflight OPTIONS request with Origin: https://evil.com",
         "Origin: https://evil.com",
         "Response: Access-Control-Allow-Origin: * - wildcard CORS confirmed"),
        ("CONF-02", "HIGH", "CORS - All Methods Allowed",
         "OPTIONS /api/employees",
         "Send preflight with Access-Control-Request-Method: DELETE",
         "Access-Control-Request-Method: DELETE",
         "Response allows DELETE from any origin - CSRF-like risk"),
        ("CONF-03", "MEDIUM", "Sensitive API Key Hint in Swagger Spec",
         "GET /openapi.json",
         "Fetch the raw OpenAPI JSON and search for 'secret123'",
         "No auth required for /openapi.json",
         "String 'secret123' appears in the security scheme description"),
        ("CONF-04", "HIGH", "Stack Trace Leaked in Error Response",
         "POST /api/employees",
         "Send a malformed JSON body (e.g. truncated JSON string)",
         'Body: {"name": "test"',
         "422 with validation detail - confirm no Python traceback in body"),
        ("CONF-05", "HIGH", "Transport - Plain HTTP (No TLS)",
         "GET http://localhost:8000/api/employees",
         "Confirm server is running on plain HTTP, not HTTPS",
         "Curl to http:// URL",
         "Connection succeeds - data transmitted in cleartext (no TLS)"),
        ("CONF-06", "MEDIUM", "Missing Security Response Headers",
         "GET /api/employees/1",
         "Inspect all response headers for security controls",
         "X-API-Key: secret123",
         "None of X-Content-Type-Options, X-Frame-Options, CSP, HSTS present"),
        ("CONF-07", "LOW", "Server Version Disclosed in Headers",
         "GET /api/employees/1",
         "Inspect 'server' response header for version information",
         "X-API-Key: secret123",
         "Header 'server: uvicorn' reveals server software name"),
    ]
    for t in conf_tests:
        test_card(pdf, *t)

    # -- 4.5 DoS / Resource Consumption ----------------------------------------
    pdf.add_page()
    sub_header(pdf, "4.5  Unrestricted Resource Consumption / DoS  (OWASP API4)")
    dos_tests = [
        ("DOS-01", "HIGH", "Oversized Request Body (No Size Limit)",
         "POST /api/employees",
         "Send a POST body where the 'name' value is 10 MB of 'A' characters",
         'name: "A" * 10_000_000  (10 MB string)',
         "Request accepted - no body size limit enforced (VULNERABILITY)"),
        ("DOS-02", "HIGH", "Rapid Sequential Requests (No Rate Limiting)",
         "GET /api/employees",
         "Send 100 GET requests in rapid succession using a loop",
         "100x GET with valid X-API-Key",
         "All 100 return 200 - no rate limiting or throttling exists"),
        ("DOS-03", "HIGH", "Memory Exhaustion via Mass POST",
         "POST /api/employees",
         "Create 1,000 employees in a loop; monitor server memory usage",
         "1000x valid POST bodies",
         "All accepted - in-memory dict grows unbounded (VULNERABILITY)"),
        ("DOS-04", "LOW", "Single-Character Substring Search Returns All",
         "GET /api/employees?name=a",
         "Search with a very common single character that matches all employees",
         "?name=a",
         "Returns all employees - no result limit or pagination"),
    ]
    for t in dos_tests:
        test_card(pdf, *t)

    # -- 4.6 Information Disclosure --------------------------------------------
    sub_header(pdf, "4.6  Information Disclosure")
    info_tests = [
        ("INFO-01", "MEDIUM", "404 Response Confirms Employee ID Exists/Not",
         "GET /api/employees/99999",
         "Request an employee ID known not to exist; read the error detail",
         "employee_id: 99999",
         "404 with detail confirming ID 99999 not found - aids enumeration"),
        ("INFO-02", "LOW", "Error Messages Reveal Internal Detail",
         "PUT /api/employees/99999",
         "Send PUT to non-existent ID; inspect the 'detail' field",
         "Valid PUT body to ID 99999",
         "Detail message exposes implementation wording; assess information value"),
        ("INFO-03", "MEDIUM", "OpenAPI Spec Accessible Without Auth",
         "GET /openapi.json",
         "Fetch the OpenAPI spec without any X-API-Key header",
         "No X-API-Key header",
         "200 - full API schema returned without authentication"),
        ("INFO-04", "LOW", "Response Timing Difference (Auth vs No Auth)",
         "GET /api/employees/1",
         "Time 50 requests with wrong key; time 50 with no key; compare averages",
         "50x wrong key / 50x no key",
         "Similar timing expected; large difference could indicate timing oracle"),
    ]
    for t in info_tests:
        test_card(pdf, *t)

    # -- 4.7 Business Logic ----------------------------------------------------
    pdf.add_page()
    sub_header(pdf, "4.7  Business Logic Flaws  (OWASP API6)")
    bl_tests = [
        ("BL-01", "MEDIUM", "Duplicate Email Accepted (No Uniqueness Check)",
         "POST /api/employees (x2)",
         "Create two employees with identical email addresses",
         'email: "duplicate@example.com" (both POSTs)',
         "Both return 201 - no uniqueness constraint on email (VULNERABILITY)"),
        ("BL-02", "LOW", "PUT With Empty Name String",
         "PUT /api/employees/1",
         "Send a PUT body with name set to empty string",
         'name: ""',
         "422 - min_length=1 prevents empty name"),
        ("BL-03", "MEDIUM", "PATCH With Explicit null Salary",
         "PATCH /api/employees/1",
         "Send a PATCH body with salary explicitly set to null/None",
         'salary: null',
         "422 or salary unchanged - null must not overwrite valid salary"),
        ("BL-04", "MEDIUM", "Mass Assignment - Set ID via POST Body",
         "POST /api/employees",
         "Include an 'id' field in the POST body attempting to set the ID",
         '{"id": 999, "name": "Test", ...}',
         "201 with server-assigned ID ignoring the sent id - confirm id not overridden"),
        ("BL-05", "HIGH", "Race Condition on Concurrent Employee Creation",
         "POST /api/employees (10 concurrent)",
         "Send 10 simultaneous POST requests using Python threading",
         "10 concurrent valid POST bodies",
         "All 10 should receive unique IDs - duplicate IDs indicate thread safety issue"),
    ]
    for t in bl_tests:
        test_card(pdf, *t)


def section_tools(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 5 - Tools & Setup")

    tools = [
        ("curl / HTTPie",         "Manual endpoint testing from the command line. "
                                  "Use curl for precise header/body control."),
        ("OWASP ZAP",             "Dynamic Application Security Testing (DAST). "
                                  "Run the Active Scan against http://localhost:8000 "
                                  "with the API key configured as a persistent header."),
        ("Burp Suite Community",  "Intercept, inspect, and replay HTTP requests. "
                                  "Use Intruder to fuzz field values and Repeater for "
                                  "manual exploration of edge cases."),
        ("Postman",               "Build and save a collection of all 7 endpoints. "
                                  "Add X-API-Key as a collection-level header variable. "
                                  "Use the Runner for sequential test execution."),
        ("locust / k6",           "Load and stress testing. Use to execute DOS-02 "
                                  "(100 req/s) and DOS-03 (1,000 concurrent POSTs) "
                                  "while monitoring memory usage on the server."),
        ("pytest + requests",     "Automate the test cases in this document as a "
                                  "regression suite. Run after any code change."),
        ("sqlmap",                "Automated SQL injection scanner. Run against query "
                                  "parameters (department, name) - expect false negatives "
                                  "since the store is in-memory, but confirm no crash."),
        ("nikto",                 "Web server misconfiguration scanner. Run as: "
                                  "nikto -h http://localhost:8000 to check headers, "
                                  "exposed paths, and known vulnerabilities."),
    ]

    hdrs = ["Tool", "Purpose & Usage"]
    wids = [40, 150]
    table_header(pdf, hdrs, wids)
    for i, (tool, purpose) in enumerate(tools):
        table_row(pdf, [tool, purpose], wids, fill=(i % 2 == 0))


def section_curl_examples(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 6 - Ready-to-Run curl Examples")

    examples = [
        ("AUTH-01  Missing API Key",
         'curl -i http://localhost:8000/api/employees'),
        ("AUTH-02  Wrong API Key",
         'curl -i -H "X-API-Key: wrongkey" http://localhost:8000/api/employees'),
        ("BOLA-01  Enumerate IDs 1-10",
         'for i in $(seq 1 10); do\n'
         '  echo -n "ID $i: "\n'
         '  curl -s -o /dev/null -w "%{http_code}" \\\n'
         '       -H "X-API-Key: secret123" \\\n'
         '       http://localhost:8000/api/employees/$i\n'
         '  echo\n'
         'done'),
        ("INJ-01  XSS in name field",
         'curl -i -X POST http://localhost:8000/api/employees \\\n'
         '  -H "X-API-Key: secret123" \\\n'
         '  -H "Content-Type: application/json" \\\n'
         '  -d \'{"name":"<script>alert(1)</script>","email":"x@x.com",\\\n'
         '        "department":"IT","position":"Dev","salary":50000}\''),
        ("INJ-11  Extreme salary (no upper bound)",
         'curl -i -X POST http://localhost:8000/api/employees \\\n'
         '  -H "X-API-Key: secret123" \\\n'
         '  -H "Content-Type: application/json" \\\n'
         '  -d \'{"name":"Test","email":"t@t.com","department":"X",\\\n'
         '        "position":"Y","salary":1e308}\''),
        ("CONF-01  CORS preflight from evil origin",
         'curl -i -X OPTIONS http://localhost:8000/api/employees \\\n'
         '  -H "Origin: https://evil.com" \\\n'
         '  -H "Access-Control-Request-Method: DELETE"'),
        ("CONF-03  Fetch OpenAPI spec without auth",
         'curl -i http://localhost:8000/openapi.json'),
        ("DOS-01  10 MB request body",
         'python3 -c "\n'
         'import requests, json\n'
         'huge = {"name": "A"*10_000_000,"email":"x@x.com",\n'
         '        "department":"T","position":"T","salary":1}\n'
         'r = requests.post(\"http://localhost:8000/api/employees\",\n'
         '    json=huge, headers={\"X-API-Key\":\"secret123\"})\n'
         'print(r.status_code)"'),
        ("BL-05  Race condition - 10 concurrent POSTs",
         'python3 -c "\n'
         'import requests, threading\n'
         'results = []\n'
         'def post():\n'
         '    r = requests.post(\"http://localhost:8000/api/employees\",\n'
         '        json={\"name\":\"Race\",\"email\":\"r@r.com\",\n'
         '              \"department\":\"T\",\"position\":\"T\",\"salary\":1},\n'
         '        headers={\"X-API-Key\":\"secret123\"})\n'
         '    results.append(r.json().get(\"id\"))\n'
         'threads = [threading.Thread(target=post) for _ in range(10)]\n'
         '[t.start() for t in threads]\n'
         '[t.join() for t in threads]\n'
         'print(\"IDs:\", results)\n'
         'print(\"Unique:\", len(set(results)) == len(results))"'),
    ]

    for label, cmd in examples:
        sub_header(pdf, label)
        pdf.set_fill_color(*GREY_LIGHT)
        pdf.set_font("Courier", "", 8)
        pdf.multi_cell(PAGE_W, 4.5, cmd, border=1, fill=True)
        pdf.ln(2)


def section_severity_guide(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 7 - Severity Rating Guide")

    levels = [
        ("CRITICAL", RED,
         "Immediate exploitation possible. Data breach, full auth bypass, or complete "
         "service takedown achievable by any attacker. Patch before the server accepts "
         "any external traffic."),
        ("HIGH",     ORANGE,
         "Significant business impact likely. Exploitable with minimal effort or knowledge. "
         "Examples: ID enumeration, no rate limiting, CORS wildcard. Fix within 1 sprint."),
        ("MEDIUM",   AMBER,
         "Moderate risk requiring some preconditions (e.g. valid API key needed first). "
         "Examples: XSS stored in responses, missing security headers. Plan fix in current "
         "release cycle."),
        ("LOW",      GREEN,
         "Limited direct impact. Defensive hardening or best-practice improvements. "
         "Examples: server version disclosure, minor input boundary issues. "
         "Address in next maintenance window."),
        ("INFO",     GREY_MED,
         "Informational finding - no direct exploitability, but awareness is recommended. "
         "Examples: Swagger UI publicly accessible, API key hint in description text."),
    ]

    for sev, colour, desc in levels:
        pdf.set_fill_color(*colour)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(PAGE_W, 7, f"  {sev}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        body(pdf, desc, indent=4)
        pdf.ln(2)


def section_execution_log(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 8 - Test Execution Log (Fill During Testing)")

    body(pdf, "Record results here as each test is executed. "
              "Attach screenshots or response bodies as evidence in appendix.")
    pdf.ln(3)

    hdrs = ["Test ID", "Date", "Tester", "Result", "Notes / Evidence"]
    wids = [20, 22, 30, 22, 96]
    table_header(pdf, hdrs, wids)

    all_ids = [
        "AUTH-01","AUTH-02","AUTH-03","AUTH-04","AUTH-05","AUTH-06",
        "BOLA-01","BOLA-02","BOLA-03","BOLA-04",
        "INJ-01","INJ-02","INJ-03","INJ-04","INJ-05","INJ-06",
        "INJ-07","INJ-08","INJ-09","INJ-10","INJ-11","INJ-12","INJ-13","INJ-14",
        "CONF-01","CONF-02","CONF-03","CONF-04","CONF-05","CONF-06","CONF-07",
        "DOS-01","DOS-02","DOS-03","DOS-04",
        "INFO-01","INFO-02","INFO-03","INFO-04",
        "BL-01","BL-02","BL-03","BL-04","BL-05",
    ]
    for i, tid in enumerate(all_ids):
        table_row(pdf, [tid, "", "", "Pass / Fail", ""], wids, fill=(i % 2 == 0))


def section_remediation(pdf: PDF):
    pdf.add_page()
    section_header(pdf, "Section 9 - Remediation Recommendations")

    recs = [
        ("SEC-F01", "CRITICAL", "Move API Key to Environment Variable",
         "Replace VALID_API_KEY = \"secret123\" with:\n"
         "  import os\n"
         "  VALID_API_KEY = os.environ[\"API_KEY\"]\n"
         "Set the variable in the deployment environment, never in source code."),
        ("SEC-F02", "HIGH", "Restrict CORS to Known Origins",
         "Replace allow_origins=[\"*\"] with an explicit allowlist:\n"
         "  allow_origins=[\"https://app.example.com\", \"http://localhost:3000\"]\n"
         "Never use wildcard in production."),
        ("SEC-F03", "HIGH", "Add Rate Limiting with slowapi",
         "Install slowapi and apply limits per endpoint:\n"
         "  pip install slowapi\n"
         "  from slowapi import Limiter\n"
         "  @router.get(\"/employees\", dependencies=[Depends(limit(\"60/minute\"))]))"),
        ("SEC-F04", "HIGH", "Replace Sequential IDs with UUIDs",
         "Change the store key to uuid.uuid4():\n"
         "  import uuid\n"
         "  new_id = str(uuid.uuid4())\n"
         "This eliminates ID enumeration and prediction attacks."),
        ("SEC-F05", "MEDIUM", "Enforce Request Body Size Limit",
         "Add a middleware to reject oversized payloads:\n"
         "  from starlette.middleware import Middleware\n"
         "  from starlette.middleware.base import BaseHTTPMiddleware\n"
         "  Limit body to e.g. 64 KB for this API."),
        ("SEC-F06", "MEDIUM", "Add Threading Lock to In-Memory Store",
         "Wrap all dict mutations with a threading.Lock():\n"
         "  import threading\n"
         "  _lock = threading.Lock()\n"
         "  with _lock:\n"
         "      employees[new_id] = employee"),
        ("SEC-F07", "MEDIUM", "Add max_length to department and position",
         "In EmployeeBase, add field constraints:\n"
         "  department: str = Field(..., max_length=100)\n"
         "  position:   str = Field(..., max_length=100)"),
        ("SEC-F08", "LOW", "Add Security Response Headers via Middleware",
         "Add a middleware that injects security headers:\n"
         "  X-Content-Type-Options: nosniff\n"
         "  X-Frame-Options: DENY\n"
         "  Content-Security-Policy: default-src 'none'\n"
         "  Strict-Transport-Security: max-age=31536000"),
        ("SEC-F09", "LOW", "Suppress Server Header",
         "Pass server_header=False to uvicorn:\n"
         "  uvicorn.run(app, server_header=False)\n"
         "Or via CLI: --no-server-header"),
        ("SEC-F10", "INFO", "Remove API Key Hint from Swagger Description",
         "Remove the '(value: secret123)' text from the OpenAPI security scheme "
         "description in main.py. In production, disable /docs and /redoc entirely."),
    ]

    hdrs = ["ID", "Severity", "Recommendation", "Implementation"]
    wids = [18, 20, 52, 100]
    table_header(pdf, hdrs, wids)
    for i, (fid, sev, title, impl) in enumerate(recs):
        table_row(pdf, [fid, sev, title, impl], wids, fill=(i % 2 == 0))


# -- Main -----------------------------------------------------------------------

def main():
    pdf = PDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(L_MARGIN, 15, L_MARGIN)

    cover_page(pdf)
    section_api_under_test(pdf)
    section_static_findings(pdf)
    section_methodology(pdf)
    section_test_cases(pdf)
    section_tools(pdf)
    section_curl_examples(pdf)
    section_severity_guide(pdf)
    section_execution_log(pdf)
    section_remediation(pdf)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "Employee_API_Security_Test_Plan.pdf")
    pdf.output(out_path)
    print(f"PDF saved to: {out_path}")


if __name__ == "__main__":
    main()
