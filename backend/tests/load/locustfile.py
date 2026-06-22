from __future__ import annotations

import os

from locust import HttpUser, between, events, task

TURF_SPORT_ID = os.environ.get("LOAD_TURF_SPORT_ID", "")
SLOT_ID = os.environ.get("LOAD_SLOT_ID", "")
PASSWORD = os.environ.get("LOAD_PASSWORD", "password123")

_results = {"confirmed_orders": 0, "conflicts": 0}


@events.test_stop.add_listener
def _report(environment, **_kwargs):
    print(f"\nBooking contention results: {_results}")


class BookingContentionUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        email = f"loadtest_{self.environment.runner.user_count}_{id(self)}@turf.in"
        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "phone": f"+9190000{id(self) % 100000:05d}",
                "password": PASSWORD,
                "role": "player",
                "name": "Load Tester",
            },
        )
        response = self.client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        token = response.json().get("data", {}).get("access_token")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    @task
    def book_same_slot(self) -> None:
        with self.client.post(
            "/api/v1/bookings",
            json={"turf_sport_id": TURF_SPORT_ID, "slot_ids": [SLOT_ID]},
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201):
                _results["confirmed_orders"] += 1
                response.success()
            elif response.status_code == 409:
                _results["conflicts"] += 1
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")
