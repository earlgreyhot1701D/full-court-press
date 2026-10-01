"""Block 5.2: the hunter, run offline with the golden fixtures, a fake model, fake Polly and a local store."""
from datetime import date


from zine import hunter, state
from zine.store import LocalStore
from zine.fixture_feed import FakeBDL
from test_fact_lock import CLEAN
from test_facts_gotn import needs_golden

ENV = {"MAX_MODEL_CALLS_PER_RUN": "60", "MAX_AUDIO_PER_RUN": "30", "LEAGUES": "wnba"}


def fake_write(system, messages):
    return None  # every voice passes: the pipeline must still publish (writers' room)


def fake_speak(text):
    return b"ID3fake" + text.encode()[:10]


@needs_golden
def test_dates_to_check():
    assert hunter.dates_to_check(None, date(2026, 9, 22)) == [date(2026, 9, 21)]
    assert hunter.dates_to_check("2026-09-19", date(2026, 9, 22)) == [date(2026, 9, 20), date(2026, 9, 21)]
    assert len(hunter.dates_to_check("2026-01-01", date(2026, 9, 22))) == hunter.LOOKBACK_DAYS + 1


@needs_golden
def test_run_builds_the_west_coast_night_on_the_right_date(tmp_path):
    # 25071 tips 02:00 UTC Sep 22 but is an Sep 21 (US Eastern) game
    store = LocalStore(str(tmp_path))
    s = hunter.run(store, FakeBDL(), fake_write, fake_speak, date(2026, 9, 22), ENV)
    assert 25071 in s["built"] and not s["failed"]
    assert s["marker"]["wnba"] == "2026-09-21"
    assert store.exists("site/wnba/2026-09-21/25071/PHX/index.html")
    assert store.exists("site/wnba/2026-09-21/25071/PHX/film-room/index.html")
    assert store.exists("site/wnba/2026-09-21/25071/DAL/card.png")
    assert store.exists("site/wnba/2026-09-21/25071/DAL/recap.mp3")
    assert store.exists("site/index.html") and store.exists("site/static/styles.css")
    assert s["audio"] == 2


@needs_golden
def test_rerun_makes_no_new_calls(tmp_path):
    store = LocalStore(str(tmp_path))
    calls = []
    def counting_write(system, messages):
        calls.append(1)
        return None
    hunter.run(store, FakeBDL(), counting_write, None, date(2026, 9, 22), ENV)
    first = len(calls)
    state.write_marker(store, {})  # force the same night again
    hunter.run(store, FakeBDL(), counting_write, None, date(2026, 9, 22), ENV)
    assert first > 0 and len(calls) == first  # night already built: nothing rebuilt, no model calls


@needs_golden
def test_failed_game_holds_the_marker(tmp_path):
    store = LocalStore(str(tmp_path))
    s = hunter.run(store, FakeBDL(fail_plays_for={25071}), fake_write, None, date(2026, 9, 22), ENV)
    assert {"game_id": 25071, "error": "RuntimeError"} in s["failed"]
    assert s["marker"]["wnba"] is None


@needs_golden
def test_not_final_is_left_for_next_run(tmp_path):
    store = LocalStore(str(tmp_path))
    s = hunter.run(store, FakeBDL(final=False), fake_write, None, date(2026, 9, 22), ENV)
    assert s["built"] == [] and s["pending_nights"] == ["2026-09-21"] and s["marker"]["wnba"] is None


@needs_golden
def test_model_budget_is_respected(tmp_path):
    store = LocalStore(str(tmp_path))
    n = []
    def w(system, messages):
        n.append(1)
        return dict(CLEAN)
    s = hunter.run(store, FakeBDL(), w, None, date(2026, 9, 22), dict(ENV, MAX_MODEL_CALLS_PER_RUN="3"))
    assert len(n) == 3 and s["model_calls"] == 3


@needs_golden
def test_logs_carry_no_model_text(tmp_path, caplog):
    store = LocalStore(str(tmp_path))
    caplog.set_level("INFO", logger="fcp.hunter")
    planted = dict(CLEAN, recap="Kahleah Copper scored 33 points.")
    hunter.run(store, FakeBDL(), lambda s, m: dict(planted), None, date(2026, 9, 22), ENV)
    text = caplog.text
    assert "33 points" not in text and "Mercury hold on" not in text and "Copper" not in text


def test_local_date_formats():
    # real probe values, Sep 26: the API returns UTC tip times
    assert hunter.local_date({"date": "2026-09-25T00:00:00.000Z"}) == "2026-09-24"   # 8pm Eastern, Sep 24
    assert hunter.local_date({"date": "2026-09-25T02:00:00.000Z"}) == "2026-09-24"   # 10pm Eastern, Sep 24
    assert hunter.local_date({"date": "2026-09-22T02:00:00.000Z"}) == "2026-09-21"   # golden 25071
    assert hunter.local_date({"date": "2026-09-25T23:00:00.000Z"}) == "2026-09-25"   # 7pm Eastern, Sep 25
    assert hunter.local_date({"date": "2026-09-25"}) == "2026-09-25"


@needs_golden
def test_quiet_night_is_not_a_failure(tmp_path):
    # UTC Sep 22 returns 25071, an Eastern Sep 21 game; Eastern Sep 22 itself has no golden game
    store = LocalStore(str(tmp_path))
    s = hunter.run(store, FakeBDL(), fake_write, None, date(2026, 9, 23), ENV)
    assert s["built"] == [] and s["failed"] == [] and s["marker"]["wnba"] == "2026-09-22"
    assert s["nights"]["2026-09-22"]["asked"] >= 1 and s["nights"]["2026-09-22"]["matched"] == 0


@needs_golden
def test_unmatched_games_hold_the_marker(tmp_path, monkeypatch):
    store = LocalStore(str(tmp_path))
    monkeypatch.setattr(hunter, "local_date", lambda g: "1999-01-01")  # a date no UTC query could return
    s = hunter.run(store, FakeBDL(), fake_write, None, date(2026, 9, 23), ENV)   # night 2026-09-22 has games by UTC day
    assert {"night": "2026-09-22", "error": "UnmatchedGames"} in s["failed"]
    assert s["marker"]["wnba"] is None


@needs_golden
def test_forced_nights_rebuild_without_moving_the_marker_back(tmp_path):
    store = LocalStore(str(tmp_path))
    state.write_marker(store, {"wnba": "2026-09-25"})
    s = hunter.run(store, FakeBDL(), fake_write, None, date(2026, 9, 26), ENV, nights=["2026-09-21"])
    assert 25071 in s["built"] and s["marker"]["wnba"] == "2026-09-25"


@needs_golden
def test_failed_game_is_not_recorded_as_built_and_forced_night_rebuilds(tmp_path, monkeypatch):
    from zine import site_build
    store = LocalStore(str(tmp_path))
    real = site_build.issue_files
    def boom(f, *a, **k):
        if f["game_id"] == 25071:
            raise RuntimeError("render")
        return real(f, *a, **k)
    monkeypatch.setattr(site_build, "issue_files", boom)
    s = hunter.run(store, FakeBDL(), fake_write, None, date(2026, 9, 22), ENV)
    assert s["built"] == [] and not state.load_night(store, "wnba", "2026-09-21")
    monkeypatch.setattr(site_build, "issue_files", real)
    s = hunter.run(store, FakeBDL(), fake_write, None, date(2026, 9, 22), ENV, nights=["2026-09-21"])
    assert s["built"] == [25071] and [r["game_id"] for r in state.load_night(store, "wnba", "2026-09-21")] == [25071]
