"""Integration tests for all API endpoints via TestClient."""

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from src.main import app


def _make_client(db_path: str) -> TestClient:
    from src.infrastructure.settings import Settings, set_settings

    set_settings(Settings(DB_PATH=db_path))
    return TestClient(app)


class TestUsersAPI:
    def test_health(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_create_user(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.post("/api/users", json={"name": "Alice", "color": "#FF0000"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Alice"
        assert data["color"] == "#FF0000"
        assert data["id"] >= 1

    def test_create_duplicate_user(self, db_path: str) -> None:
        client = _make_client(db_path)
        client.post("/api/users", json={"name": "Alice", "color": "#FF0000"})
        resp = client.post("/api/users", json={"name": "alice", "color": "#00FF00"})
        assert resp.status_code == 409
        body = resp.json()
        detail = body.get("detail", body.get("error", {}))
        assert isinstance(detail, dict)
        assert detail.get("code") == "conflict"

    def test_list_users(self, db_path: str) -> None:
        client = _make_client(db_path)
        client.post("/api/users", json={"name": "A", "color": "#FF0000"})
        client.post("/api/users", json={"name": "B", "color": "#00FF00"})
        resp = client.get("/api/users")
        assert resp.status_code == 200
        assert len(resp.json()["users"]) == 2

    def test_list_active_users(self, db_path: str) -> None:
        client = _make_client(db_path)
        client.post("/api/users", json={"name": "A", "color": "#FF0000"})
        u2 = client.post("/api/users", json={"name": "B", "color": "#00FF00"})
        client.patch(f"/api/users/{u2.json()['id']}", json={"active": False})
        resp = client.get("/api/users/active")
        assert resp.status_code == 200
        assert len(resp.json()["users"]) == 1

    def test_update_user(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "A", "color": "#FF0000"}).json()["id"]
        resp = client.patch(f"/api/users/{uid}", json={"name": "NewName"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewName"

    def test_deactivate_user(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "A", "color": "#FF0000"}).json()["id"]
        resp = client.patch(f"/api/users/{uid}", json={"active": False})
        assert resp.status_code == 200
        assert resp.json()["active"] is False

    def test_delete_user(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "A", "color": "#FF0000"}).json()["id"]
        resp = client.delete(f"/api/users/{uid}")
        assert resp.status_code == 204
        resp = client.get("/api/users")
        assert len(resp.json()["users"]) == 0

    def test_user_invalid_color(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.post("/api/users", json={"name": "A", "color": "red"})
        assert resp.status_code in {400, 422}


class TestTemplatesAPI:
    def test_create_template(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.post(
            "/api/templates",
            json={
                "title": "Dishes",
                "description": "Wash the dishes",
                "sp_cost": 3,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": None,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Dishes"
        assert data["sp_cost"] == 3

    def test_create_weekly_template(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.post(
            "/api/templates",
            json={
                "title": "Trash",
                "sp_cost": 2,
                "recurrence_type": "weekly",
                "recurrence_params": {"weekday": 0},
                "default_assignee_id": None,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["recurrence_type"] == "weekly"

    def test_list_templates(self, db_path: str) -> None:
        client = _make_client(db_path)
        client.post(
            "/api/templates", json={"title": "A", "sp_cost": 1, "recurrence_type": "none", "recurrence_params": {}}
        )
        client.post(
            "/api/templates", json={"title": "B", "sp_cost": 2, "recurrence_type": "none", "recurrence_params": {}}
        )
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        assert len(resp.json()["templates"]) == 2

    def test_update_template(self, db_path: str) -> None:
        client = _make_client(db_path)
        tid = client.post(
            "/api/templates",
            json={
                "title": "Old",
                "sp_cost": 1,
                "recurrence_type": "none",
                "recurrence_params": {},
            },
        ).json()["id"]
        resp = client.patch(f"/api/templates/{tid}", json={"title": "NewTitle", "sp_cost": 5})
        assert resp.status_code == 200
        assert resp.json()["title"] == "NewTitle"
        assert resp.json()["sp_cost"] == 5

    def test_deactivate_template(self, db_path: str) -> None:
        client = _make_client(db_path)
        tid = client.post(
            "/api/templates",
            json={
                "title": "Test",
                "sp_cost": 1,
                "recurrence_type": "none",
                "recurrence_params": {},
            },
        ).json()["id"]
        resp = client.delete(f"/api/templates/{tid}")
        assert resp.status_code == 204
        active = client.get("/api/templates/active")
        assert len(active.json()["templates"]) == 0

    def test_template_negative_sp_rejected(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.post(
            "/api/templates",
            json={
                "title": "Bad",
                "sp_cost": -1,
                "recurrence_type": "none",
                "recurrence_params": {},
            },
        )
        assert resp.status_code in {400, 422}


def _today_calendar_url() -> str:
    today = datetime.now(tz=timezone.utc).date()
    return f"/api/calendar?year={today.year}&month={today.month}"


class TestInstancesAPI:
    def _setup(self, db_path: str) -> tuple[TestClient, int, int, str]:
        client = _make_client(db_path)
        u_resp = client.post("/api/users", json={"name": "User1", "color": "#FF0000"})
        user_id = u_resp.json()["id"]

        today = datetime.now(tz=timezone.utc).date()
        target = date(today.year, today.month, min(today.day + 1, 28))

        t_resp = client.post(
            "/api/templates",
            json={
                "title": "Daily Task",
                "sp_cost": 2,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": user_id,
            },
        )

        return client, user_id, t_resp.json()["id"], target.isoformat()

    def test_reassign_instance(self, db_path: str) -> None:
        client, _, _, date_key = self._setup(db_path)
        uid2 = client.post("/api/users", json={"name": "User2", "color": "#00FF00"}).json()["id"]

        cal = client.get(_today_calendar_url()).json()
        insts = cal["days"].get(date_key, [])
        assert len(insts) > 0, f"No instances on {date_key}. Days: {list(cal['days'].keys())[:5]}"
        inst_id = insts[0]["id"]

        resp = client.post(f"/api/instances/{inst_id}/reassign", json={"to_user_id": uid2})
        assert resp.status_code == 200
        assert resp.json()["assignee"]["id"] == uid2

    def test_complete_instance(self, db_path: str) -> None:
        client, uid1, _, date_key = self._setup(db_path)

        cal = client.get(_today_calendar_url()).json()
        insts = cal["days"].get(date_key, [])
        assert len(insts) > 0, f"No instances on {date_key}. Days: {list(cal['days'].keys())[:5]}"
        inst_id = insts[0]["id"]

        resp = client.post(f"/api/instances/{inst_id}/complete", json={"completed_by_id": uid1})
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
        assert resp.json()["completed_by"]["id"] == uid1

    def test_complete_twice_fails(self, db_path: str) -> None:
        client, uid1, _, date_key = self._setup(db_path)

        cal = client.get(_today_calendar_url()).json()
        inst_id = cal["days"][date_key][0]["id"]

        client.post(f"/api/instances/{inst_id}/complete", json={"completed_by_id": uid1})
        resp = client.post(f"/api/instances/{inst_id}/complete", json={"completed_by_id": uid1})
        assert resp.status_code == 409

    def test_reassign_not_found(self, db_path: str) -> None:
        client, uid1, _, _ = self._setup(db_path)
        resp = client.post("/api/instances/99999/reassign", json={"to_user_id": uid1})
        assert resp.status_code == 404

    def test_transfers_history(self, db_path: str) -> None:
        client, _, _, date_key = self._setup(db_path)
        uid2 = client.post("/api/users", json={"name": "User2", "color": "#00FF00"}).json()["id"]

        cal = client.get(_today_calendar_url()).json()
        inst_id = cal["days"][date_key][0]["id"]

        client.post(f"/api/instances/{inst_id}/reassign", json={"to_user_id": uid2})
        resp = client.get(f"/api/instances/{inst_id}/transfers")
        assert resp.status_code == 200
        assert len(resp.json()["transfers"]) == 1


class TestCalendarAPI:
    def test_calendar_returns_structure(self, db_path: str) -> None:
        client = _make_client(db_path)
        today = datetime.now(tz=timezone.utc).date()
        resp = client.get(f"/api/calendar?year={today.year}&month={today.month}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == today.year
        assert data["month"] == today.month
        assert "days" in data
        assert "users" in data

    def test_calendar_materializes_instances(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "U", "color": "#FF0000"}).json()["id"]
        client.post(
            "/api/templates",
            json={
                "title": "Daily Ch",
                "sp_cost": 1,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": uid,
            },
        )
        today = datetime.now(tz=timezone.utc).date()
        resp = client.get(f"/api/calendar?year={today.year}&month={today.month}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["days"]) > 0

    def test_calendar_range_returns_structure(self, db_path: str) -> None:
        client = _make_client(db_path)
        today = datetime.now(tz=timezone.utc).date()
        from datetime import timedelta

        end = today + timedelta(days=6)
        resp = client.get(f"/api/calendar/range?start={today.isoformat()}&end={end.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert "days" in data
        assert "users" in data
        assert "year" not in data
        assert "month" not in data

    def test_calendar_range_materializes(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "U", "color": "#FF0000"}).json()["id"]
        client.post(
            "/api/templates",
            json={
                "title": "Daily Ch",
                "sp_cost": 1,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": uid,
            },
        )
        today = datetime.now(tz=timezone.utc).date()
        from datetime import timedelta

        end = today + timedelta(days=6)
        resp = client.get(f"/api/calendar/range?start={today.isoformat()}&end={end.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["days"]) > 0
        for date_str, instances in data["days"].items():
            date_obj = date.fromisoformat(date_str)
            assert today <= date_obj <= end

    def test_calendar_range_single_day(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "U", "color": "#FF0000"}).json()["id"]
        client.post(
            "/api/templates",
            json={
                "title": "Daily Ch",
                "sp_cost": 1,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": uid,
            },
        )
        today = datetime.now(tz=timezone.utc).date()
        resp = client.get(f"/api/calendar/range?start={today.isoformat()}&end={today.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert today.isoformat() in data["days"]
        assert len(data["days"]) == 1

    def test_calendar_month_still_works(self, db_path: str) -> None:
        client = _make_client(db_path)
        today = datetime.now(tz=timezone.utc).date()
        resp = client.get(f"/api/calendar?year={today.year}&month={today.month}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == today.year
        assert data["month"] == today.month
        assert "days" in data
        assert "users" in data


class TestDashboardAPI:
    def test_dashboard_returns_structure(self, db_path: str) -> None:
        client = _make_client(db_path)
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance_30d" in data
        assert "balance_current_month" in data
        assert "overdue" in data
        assert "recent_done" in data
        assert "summary" in data
        assert "pending" in data["summary"]
        assert "overdue" in data["summary"]
        assert "done_this_month" in data["summary"]

    def test_dashboard_shows_balance(self, db_path: str) -> None:
        client = _make_client(db_path)
        uid = client.post("/api/users", json={"name": "U", "color": "#FF0000"}).json()["id"]

        t_resp = client.post(
            "/api/templates",
            json={
                "title": "Task",
                "sp_cost": 5,
                "recurrence_type": "none",
                "recurrence_params": {},
                "default_assignee_id": uid,
            },
        )
        tpl_id = t_resp.json()["id"]

        now = datetime.now(tz=timezone.utc)

        from src.infrastructure.db.connection import get_connection

        conn = get_connection()
        conn.execute(
            "INSERT INTO task_instance "
            "(template_id, title, scheduled_date, assignee_id, "
            "completed_at, completed_by_id, sp_cost_at_completion, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (tpl_id, "Task", now.date().isoformat(), uid, now.isoformat(), uid, 5, now.isoformat()),
        )
        conn.commit()
        conn.close()

        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        user_balances = [b for b in data["balance_30d"] if b["user"]["id"] == uid]
        assert len(user_balances) == 1
        assert user_balances[0]["sp_sum"] == 5
        assert user_balances[0]["tasks_count"] == 1


class TestFullLifecycle:
    def test_create_reassign_complete_balance(self, db_path: str) -> None:
        client = _make_client(db_path)

        u1 = client.post("/api/users", json={"name": "Иван", "color": "#FF0000"}).json()
        u2 = client.post("/api/users", json={"name": "Мария", "color": "#00FF00"}).json()

        today = datetime.now(tz=timezone.utc).date()
        target = date(today.year, today.month, min(today.day + 1, 28))
        date_key = target.isoformat()

        client.post(
            "/api/templates",
            json={
                "title": "Мусор",
                "sp_cost": 3,
                "recurrence_type": "daily",
                "recurrence_params": {},
                "default_assignee_id": u1["id"],
            },
        )

        cal = client.get(_today_calendar_url()).json()
        insts = cal["days"].get(date_key, [])
        assert len(insts) > 0, f"No instances on {date_key}. Days: {list(cal['days'].keys())[:5]}"
        inst = insts[0]

        resp = client.post(f"/api/instances/{inst['id']}/reassign", json={"to_user_id": u2["id"]})
        assert resp.status_code == 200
        assert resp.json()["assignee"]["id"] == u2["id"]

        resp = client.post(f"/api/instances/{inst['id']}/complete", json={"completed_by_id": u2["id"]})
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
        assert resp.json()["sp_cost_at_completion"] == 3
