"""
locustfile.py
~~~~~~~~~~~~~
Performance test suite for the Employee REST API (http://localhost:8000).

Test types controlled via --tags or environment shape:
  Baseline   :  1 user,   5 min  -- establish reference metrics
  Load       : 50 users, 10 min  -- normal expected traffic
  Stress     :200 users, 10 min  -- above-normal / peak traffic
  Spike      :500 users,  2 min  -- sudden burst then drop
  Soak       : 20 users, 60 min  -- sustained endurance

Run examples (API server must be running on port 8000):
  # Load test - web UI at http://localhost:8089
  locust -f performance_testing/locustfile.py --host http://localhost:8000

  # Headless load test (50 users, 2 min ramp, 10 min run)
  locust -f performance_testing/locustfile.py --host http://localhost:8000 \
         --headless -u 50 -r 5 --run-time 10m \
         --html performance_testing/reports/load_test_report.html

  # Stress test
  locust -f performance_testing/locustfile.py --host http://localhost:8000 \
         --headless -u 200 -r 10 --run-time 10m \
         --html performance_testing/reports/stress_test_report.html \
         --csv  performance_testing/reports/stress

  # Soak test
  locust -f performance_testing/locustfile.py --host http://localhost:8000 \
         --headless -u 20 -r 2 --run-time 60m \
         --html performance_testing/reports/soak_test_report.html

KPI targets (see Section 4 of the Performance Test Plan PDF):
  P95 response time  < 500 ms
  P99 response time  < 1000 ms
  Error rate         < 1%
  Throughput (load)  > 100 RPS
"""

import random
import string
from locust import HttpUser, TaskSet, task, between, constant_pacing, tag, events

API_KEY = "secret123"
HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rand_str(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _employee_payload(department: str | None = None) -> dict:
    return {
        "name":       f"Perf {_rand_str(6)}",
        "email":      f"{_rand_str(6)}@example.com",
        "department": department or random.choice(["Engineering", "HR", "Finance", "QA"]),
        "position":   random.choice(["Engineer", "Manager", "Analyst", "Lead"]),
        "salary":     round(random.uniform(40_000, 120_000), 2),
    }


def _seeded_id() -> int:
    """One of the 5 seeded employees always present after server start."""
    return random.randint(1, 5)


# ---------------------------------------------------------------------------
# Task Sets — grouped by user behaviour profile
# ---------------------------------------------------------------------------

class ReadHeavyTasks(TaskSet):
    """80% reads, 20% targeted reads — simulates browser / dashboard traffic."""

    @task(5)
    def get_all_employees(self):
        self.client.get("/api/employees", headers=HEADERS, name="GET /api/employees")

    @task(3)
    def get_employee_by_id(self):
        emp_id = _seeded_id()
        self.client.get(
            f"/api/employees/{emp_id}", headers=HEADERS,
            name="GET /api/employees/{id}"
        )

    @task(1)
    def filter_by_department(self):
        dept = random.choice(["Engineering", "HR", "Finance"])
        self.client.get(
            "/api/employees", headers=HEADERS,
            params={"department": dept},
            name="GET /api/employees?department"
        )

    @task(1)
    def filter_by_name(self):
        self.client.get(
            "/api/employees", headers=HEADERS,
            params={"name": "a"},
            name="GET /api/employees?name"
        )


class WriteHeavyTasks(TaskSet):
    """Creates, updates, and deletes employees — simulates admin / import operations."""

    def on_start(self):
        self._created_id: int | None = None

    @task(3)
    def create_employee(self):
        with self.client.post(
            "/api/employees",
            json=_employee_payload(),
            headers=HEADERS,
            name="POST /api/employees",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                self._created_id = resp.json().get("id")
                resp.success()
            else:
                resp.failure(f"POST failed: {resp.status_code}")

    @task(2)
    def update_employee(self):
        emp_id = self._created_id or _seeded_id()
        with self.client.put(
            f"/api/employees/{emp_id}",
            json=_employee_payload(),
            headers=HEADERS,
            name="PUT /api/employees/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"PUT failed: {resp.status_code}")

    @task(1)
    def patch_employee(self):
        emp_id = self._created_id or _seeded_id()
        with self.client.patch(
            f"/api/employees/{emp_id}",
            json={"salary": round(random.uniform(50_000, 100_000), 2)},
            headers=HEADERS,
            name="PATCH /api/employees/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"PATCH failed: {resp.status_code}")

    @task(1)
    def create_via_department_path(self):
        dept = random.choice(["Engineering", "HR", "Finance"])
        with self.client.post(
            f"/api/departments/{dept}/employees",
            json=_employee_payload(department=dept),
            headers=HEADERS,
            name="POST /api/departments/{dept}/employees",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                resp.success()
            else:
                resp.failure(f"POST dept failed: {resp.status_code}")


class MixedCRUDTasks(TaskSet):
    """Mixed read/write — simulates realistic API traffic (60/40 split)."""

    def on_start(self):
        self._temp_id: int | None = None

    @task(4)
    def read_list(self):
        self.client.get("/api/employees", headers=HEADERS, name="GET /api/employees")

    @task(2)
    def read_single(self):
        emp_id = self._temp_id or _seeded_id()
        self.client.get(
            f"/api/employees/{emp_id}", headers=HEADERS,
            name="GET /api/employees/{id}"
        )

    @task(2)
    def create(self):
        with self.client.post(
            "/api/employees",
            json=_employee_payload(),
            headers=HEADERS,
            name="POST /api/employees",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                self._temp_id = resp.json().get("id")
                resp.success()
            else:
                resp.failure(f"POST failed: {resp.status_code}")

    @task(1)
    def update(self):
        emp_id = self._temp_id or _seeded_id()
        with self.client.put(
            f"/api/employees/{emp_id}",
            json=_employee_payload(),
            headers=HEADERS,
            name="PUT /api/employees/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"PUT failed: {resp.status_code}")

    @task(1)
    def delete_and_recreate(self):
        """Create a temp employee then immediately delete it."""
        with self.client.post(
            "/api/employees",
            json=_employee_payload(),
            headers=HEADERS,
            name="POST (for delete)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"Create for delete failed: {resp.status_code}")
                return
            emp_id = resp.json().get("id")
            resp.success()

        with self.client.delete(
            f"/api/employees/{emp_id}",
            headers=HEADERS,
            name="DELETE /api/employees/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code == 204:
                resp.success()
            else:
                resp.failure(f"DELETE failed: {resp.status_code}")


# ---------------------------------------------------------------------------
# User classes — one per test scenario
# ---------------------------------------------------------------------------

class BaselineUser(HttpUser):
    """
    Baseline test: 1 user, wait 1-2 s between tasks.
    Establishes reference latency with no concurrency pressure.

    Run:
        locust -f performance_testing/locustfile.py --host http://localhost:8000 \
               --headless -u 1 -r 1 --run-time 5m \
               --html performance_testing/reports/baseline_report.html
    """
    tasks = [ReadHeavyTasks]
    wait_time = between(1, 2)
    weight = 1


class LoadTestUser(HttpUser):
    """
    Load test: 50 concurrent users, ramp over 2 min, run 10 min.
    Models normal production traffic (read-heavy with some writes).

    Run:
        locust -f performance_testing/locustfile.py --host http://localhost:8000 \
               --headless -u 50 -r 5 --run-time 10m \
               --html performance_testing/reports/load_test_report.html \
               --csv  performance_testing/reports/load
    """
    tasks = [MixedCRUDTasks]
    wait_time = between(0.5, 2)
    weight = 10


class StressTestUser(HttpUser):
    """
    Stress test: 200 concurrent users, ramp over 5 min, run 10 min.
    Pushes API beyond normal capacity to find the breaking point.

    Run:
        locust -f performance_testing/locustfile.py --host http://localhost:8000 \
               --headless -u 200 -r 10 --run-time 10m \
               --html performance_testing/reports/stress_test_report.html \
               --csv  performance_testing/reports/stress
    """
    tasks = [MixedCRUDTasks]
    wait_time = between(0.1, 0.5)
    weight = 10


class SpikeTestUser(HttpUser):
    """
    Spike test: instantly jump to 500 users, hold 2 min, drop back to 0.
    Simulates sudden traffic burst (viral event, batch job trigger, etc.).

    Run:
        locust -f performance_testing/locustfile.py --host http://localhost:8000 \
               --headless -u 500 -r 500 --run-time 2m \
               --html performance_testing/reports/spike_test_report.html
    """
    tasks = [ReadHeavyTasks]
    wait_time = between(0, 0.2)
    weight = 10


class SoakTestUser(HttpUser):
    """
    Soak / endurance test: 20 users, constant throughput, 60 min.
    Detects memory leaks, ID counter drift, degradation over time.

    Run:
        locust -f performance_testing/locustfile.py --host http://localhost:8000 \
               --headless -u 20 -r 2 --run-time 60m \
               --html performance_testing/reports/soak_test_report.html \
               --csv  performance_testing/reports/soak
    """
    tasks = [MixedCRUDTasks]
    wait_time = constant_pacing(3)   # 1 request every 3 s per user = ~7 RPS steady
    weight = 5


# ---------------------------------------------------------------------------
# Event hooks — custom pass/fail logging
# ---------------------------------------------------------------------------

@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               exception, context, **kwargs):
    """Flag any response time breach so it shows in the log even on success."""
    if response_time > 1000 and exception is None:
        print(
            f"[SLOW] {request_type} {name} "
            f"took {response_time:.0f} ms (P99 threshold: 1000 ms)"
        )
