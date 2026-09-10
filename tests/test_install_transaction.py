"""Installation transactions retain recovery evidence and preserve later edits."""
import base64
import copy
import fcntl
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def api():
    from core_install import transaction
    return transaction


def ident(data, mode=0o644):
    return {"sha256": hashlib.sha256(data).hexdigest(), "mode": mode}


def fixture(tmp_path):
    tx = api()
    repo, target = tmp_path / "repo", tmp_path / "home"
    repo.mkdir()
    target.mkdir()
    (repo / "new").write_bytes(b"new")
    (repo / "new").chmod(0o755)
    (target / "old").write_bytes(b"old")
    plan = {"schema": 2, "repo": str(repo), "target": str(target), "actions": [
        {"op": "write", "path": "fresh", "before": None, "after": ident(b"new", 0o755), "source": "new"},
        {"op": "remove", "path": "old", "before": tx.identity(target / "old"), "after": None},
        {"op": "write", "path": ".core-prompts-state/installation.json", "before": None,
         "after": ident(b"{}\n"), "content": base64.b64encode(b"{}\n").decode()},
    ]}
    return tx, repo, target, plan


def test_apply_and_exact_rollback(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    receipt = tx.apply(repo, target, plan, lambda: copy.deepcopy(plan))
    assert receipt["status"] == "complete"
    assert tx.identity(target / "fresh") == plan["actions"][0]["after"]
    assert not (target / "old").exists()
    assert tx.rollback(target, receipt["transaction"], dry_run=True)["status"] == "rollback-ready"
    assert (target / "fresh").exists()
    result = tx.rollback(target, receipt["transaction"])
    assert result["status"] == "rolled-back"
    assert (target / "old").read_bytes() == b"old"
    assert not (target / "fresh").exists()
    assert not (target / ".core-prompts-state/installation.json").exists()


@pytest.mark.parametrize("drift", ["replan", "source", "target", "mode"])
def test_stale_plan_never_changes_installed_bytes(tmp_path, drift):
    tx, repo, target, plan = fixture(tmp_path)
    current = copy.deepcopy(plan)
    if drift == "replan":
        current["extra"] = True
    elif drift == "source":
        (repo / "new").write_bytes(b"changed")
    elif drift == "target":
        (target / "old").write_bytes(b"custom")
    else:
        (repo / "new").chmod(0o600)
    before = (target / "old").read_bytes()
    with pytest.raises(tx.InstallError):
        tx.apply(repo, target, plan, lambda: current)
    assert (target / "old").read_bytes() == before
    assert not (target / "fresh").exists()


def test_lock_is_shared_by_all_install_operations(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    state = target / ".core-prompts-state"
    state.mkdir()
    with (state / "installation.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(tx.InstallError, match="lock"):
            tx.apply(repo, target, plan, lambda: plan)
    assert (target / "old").exists()


@pytest.mark.parametrize("relative", ["../escape", "/absolute", "a/../b", "a//b", "./a", "a/", ""])
def test_paths_must_be_canonical(tmp_path, relative):
    with pytest.raises(api().InstallError):
        api().safe(tmp_path, relative)


def test_root_and_ancestor_symlinks_rejected(tmp_path):
    tx = api()
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)
    with pytest.raises(tx.InstallError):
        tx.safe(tmp_path / "alias" / "missing", "file")
    with pytest.raises(tx.InstallError):
        tx.safe(tmp_path, "alias/file")


def test_inventory_rejects_links_and_retains_empty_directories(tmp_path):
    tx = api()
    (tmp_path / "empty").mkdir()
    (tmp_path / "single").write_bytes(b"one")
    assert tx.inventory(tmp_path, ["empty", "single"]) == {"single": ident(b"one")}
    (tmp_path / "empty/link").symlink_to(tmp_path / "single")
    with pytest.raises(tx.InstallError):
        tx.inventory(tmp_path, ["empty"])
    assert (tmp_path / "empty").is_dir()


def test_later_edit_conflicts_before_any_rollback_write(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    result = tx.apply(repo, target, plan, lambda: plan)
    (target / "fresh").write_bytes(b"custom")
    with pytest.raises(tx.InstallError, match="conflict"):
        tx.rollback(target, result["transaction"])
    assert not (target / "old").exists()
    assert (target / "fresh").read_bytes() == b"custom"


def test_interrupted_apply_blocks_next_apply_and_can_restore(tmp_path, monkeypatch):
    tx, repo, target, plan = fixture(tmp_path)
    original = tx._replace
    count = 0
    def fail_second(path, data, mode):
        nonlocal count
        if path.name in {"fresh", "installation.json"}:
            count += 1
            if count == 2:
                raise OSError("simulated interruption")
        return original(path, data, mode)
    monkeypatch.setattr(tx, "_replace", fail_second)
    with pytest.raises(tx.InstallError, match="recoverable") as error:
        tx.apply(repo, target, plan, lambda: plan)
    assert error.value.transaction
    with pytest.raises(tx.InstallError, match="unfinished"):
        tx.apply(repo, target, plan, lambda: plan)
    monkeypatch.setattr(tx, "_replace", original)
    tx.rollback(target, error.value.transaction)
    assert (target / "old").read_bytes() == b"old"
    assert not (target / "fresh").exists()


def test_corrupt_backup_prevents_all_rollback_writes(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    result = tx.apply(repo, target, plan, lambda: plan)
    journal = target / ".core-prompts-state/install-transactions" / result["transaction"]
    (journal / "before/1").write_bytes(b"broken")
    with pytest.raises(tx.InstallError, match="backup"):
        tx.rollback(target, result["transaction"])
    assert (target / "fresh").exists()
    assert not (target / "old").exists()


def test_interrupted_rollback_is_resumable(tmp_path, monkeypatch):
    tx, repo, target, plan = fixture(tmp_path)
    result = tx.apply(repo, target, plan, lambda: plan)
    original = tx._replace
    def interrupted(path, data, mode):
        if path == target / "old":
            raise OSError("interrupted restore")
        return original(path, data, mode)
    monkeypatch.setattr(tx, "_replace", interrupted)
    with pytest.raises(tx.InstallError, match="recoverable"):
        tx.rollback(target, result["transaction"])
    monkeypatch.setattr(tx, "_replace", original)
    tx.rollback(target, result["transaction"])
    assert (target / "old").read_bytes() == b"old"


def test_all_sources_staged_for_self_update(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    (target / "source").write_bytes(b"original-source")
    plan["repo"] = str(target)
    plan["actions"] = [
        {"op": "write", "path": "source", "before": ident(b"original-source"),
         "after": ident(b"replacement"), "content": base64.b64encode(b"replacement").decode()},
        {"op": "write", "path": "destination", "before": None,
         "after": ident(b"original-source"), "source": "source"},
    ]
    tx.apply(target, target, plan, lambda: plan)
    assert (target / "destination").read_bytes() == b"original-source"


def test_failed_preparation_can_rollback_without_missing_backup(tmp_path, monkeypatch):
    tx, repo, target, plan = fixture(tmp_path)
    original = tx._replace
    def interrupted(path, data, mode):
        if path.parent.name == "before":
            raise OSError("backup storage failure")
        return original(path, data, mode)
    monkeypatch.setattr(tx, "_replace", interrupted)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: plan)
    assert error.value.transaction
    monkeypatch.setattr(tx, "_replace", original)
    tx.rollback(target, error.value.transaction)
    assert (target / "old").read_bytes() == b"old"
    assert not (target / "fresh").exists()


def test_installation_state_written_after_replacement_and_retirement(tmp_path, monkeypatch):
    tx, repo, target, plan = fixture(tmp_path)
    plan["actions"].reverse()
    original = tx._replace
    observations = []
    def observe(path, data, mode):
        if path == target / ".core-prompts-state/installation.json":
            observations.append(((target / "fresh").read_bytes(), (target / "old").exists()))
        return original(path, data, mode)
    monkeypatch.setattr(tx, "_replace", observe)
    tx.apply(repo, target, plan, lambda: plan)
    assert observations == [(b"new", False)]


def test_symlink_source_rejected_before_target_changes(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    (repo / "alias").symlink_to(repo / "new")
    plan["actions"][0]["source"] = "alias"
    with pytest.raises(tx.InstallError, match="symlink"):
        tx.apply(repo, target, plan, lambda: plan)
    assert (target / "old").exists()
    assert not (target / "fresh").exists()


def test_special_file_inventory_rejected_without_opening_fifo(tmp_path):
    import os
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(api().InstallError, match="regular file"):
        api().inventory(tmp_path, ["pipe"])


@pytest.mark.parametrize("name", [".core-prompts-state/installation.lock", ".core-prompts-state/install-transactions/attack", ".CORE-PROMPTS-STATE/installation.lock"])
def test_action_cannot_overwrite_transaction_metadata(tmp_path, name):
    tx, repo, target, plan = fixture(tmp_path)
    plan["actions"][0]["path"] = name
    with pytest.raises(tx.InstallError, match="reserved"):
        tx.apply(repo, target, plan, lambda: plan)
    assert (target / "old").exists()


def test_retention_is_advisory_and_excludes_unknown_files(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    first = tx.apply(repo, target, plan, lambda: plan)
    tx.rollback(target, first["transaction"])
    second = tx.apply(repo, target, plan, lambda: plan)
    tx.rollback(target, second["transaction"])
    third = tx.apply(repo, target, plan, lambda: plan)
    assert third["retention_candidates"] == [first["transaction"]]
    directory = target / ".core-prompts-state/install-transactions" / first["transaction"]
    assert (directory / "before/1").exists()
    (directory / "custom").write_text("preserve me")
    tx.rollback(target, third["transaction"])
    fourth = tx.apply(repo, target, plan, lambda: plan)
    assert first["transaction"] not in fourth["retention_candidates"]
    assert (directory / "custom").read_text() == "preserve me"


def test_release_watch_is_transactional_and_restored(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    state = target / ".core-prompts-state"
    state.mkdir()
    watch = state / "release-watch.json"
    watch.write_bytes(b'{"installed_version":"old"}\n')
    before = tx.identity(watch)
    updated = b'{"installed_version":"new"}\n'
    plan["actions"].append({"op": "write", "path": ".core-prompts-state/release-watch.json",
                            "before": before, "after": ident(updated),
                            "content": base64.b64encode(updated).decode()})
    result = tx.apply(repo, target, plan, lambda: plan)
    assert watch.read_bytes() == updated
    tx.rollback(target, result["transaction"])
    assert tx.identity(watch) == before
    assert not (state / "installation.json").exists()


@pytest.mark.parametrize("actions,preserved,status", [
    (True, True, "applied-with-preserved"),
    (False, True, "no-op-with-preserved"),
    (False, False, "no-op"),
])
def test_receipt_distinguishes_preserved_and_no_op(tmp_path, actions, preserved, status):
    tx, repo, target, plan = fixture(tmp_path)
    plan["preserved"] = [{"roots": ["custom"], "reason": "customized"}] if preserved else []
    if not actions:
        plan["actions"] = []
    receipt = tx.apply(repo, target, plan, lambda: plan)
    assert receipt["status"] == status
    assert receipt["preserved"] == plan["preserved"]
    if not actions:
        assert receipt["transaction"] is None
        assert not (target / ".core-prompts-state/install-transactions").exists()


def test_direct_apply_rejects_blockers_before_installation_changes(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    plan["blockers"] = [{"reason": "unresolved ownership"}]
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: plan)
    assert error.value.code == "blocked-plan"
    assert (target / "old").read_bytes() == b"old"
    assert not (target / "fresh").exists()
    assert not (target / ".core-prompts-state/install-transactions").exists()


def test_all_replacements_revalidated_before_any_retirement(tmp_path, monkeypatch):
    tx, repo, target, plan = fixture(tmp_path)
    plan["actions"].append({"op": "write", "path": "second", "before": None,
                            "after": ident(b"second"),
                            "content": base64.b64encode(b"second").decode()})
    original = tx._replace
    def concurrent_edit(path, data, mode):
        result = original(path, data, mode)
        if path == target / "second":
            (target / "fresh").write_bytes(b"later edit")
        return result
    monkeypatch.setattr(tx, "_replace", concurrent_edit)
    with pytest.raises(tx.InstallError, match="replacement drift"):
        tx.apply(repo, target, plan, lambda: plan)
    assert (target / "old").read_bytes() == b"old"
    assert (target / "fresh").read_bytes() == b"later edit"
    assert not (target / ".core-prompts-state/installation.json").exists()


def release_fixture(tmp_path):
    tx, repo, target, plan = fixture(tmp_path)
    watch = target / ".core-prompts-state/release-watch.json"
    watch.parent.mkdir()
    previous = {"installed_version": "v1.0.0", "latest_version": "v2.0.0", "pending_version": "v2.0.0",
                "status": "pending-install", "note": "before update", "last_checked_at": "before"}
    watch.write_bytes(tx.encoded(previous))
    after = {**previous, "installed_version": "v2.0.0", "pending_version": "", "status": "current"}
    payload = tx.encoded(after)
    plan["actions"].append({"op": "write", "path": tx.RELEASE_WATCH, "before": tx.identity(watch),
                            "after": ident(payload), "content": base64.b64encode(payload).decode()})
    receipt = tx.apply(repo, target, plan, lambda: plan)
    return tx, target, watch, receipt


@pytest.mark.parametrize('version',['v2.0.0','2.0.0'])
def test_release_polling_observations_survive_rollback_and_dry_run(tmp_path, version):
    tx, target, watch, receipt = release_fixture(tmp_path)
    observed = {"installed_version": version, "latest_version": "v3.0.0", "pending_version": "v3.0.0",
                "status": "pending-install", "note": "fresh remote observation", "last_checked_at": "later",
                "last_notified_at": "latest-notification", "verified_bundle_sha256": "observed-hash"}
    watch.write_bytes(tx.encoded(observed))
    journal = target / tx.TRANSACTIONS / receipt["transaction"] / "journal.json"
    journal_before = journal.read_bytes()
    assert tx.rollback(target, receipt["transaction"], dry_run=True)["status"] == "rollback-ready"
    assert json.loads(watch.read_bytes()) == observed
    assert journal.read_bytes() == journal_before
    assert tx.rollback(target, receipt["transaction"])["status"] == "rolled-back"
    restored = json.loads(watch.read_bytes())
    assert restored == {**observed, "installed_version": "v1.0.0"}
    assert not (target / ".core-prompts-state/installation.json").exists()
    assert (target / "old").read_bytes() == b"old"
    record = json.loads(journal.read_bytes())["release_restore"]
    assert record["after"] == tx.identity(watch)


@pytest.mark.parametrize("installed", ["v3.0.0", "v1.0.0"])
def test_another_installed_version_transition_blocks_release_rollback(tmp_path, installed):
    tx, target, watch, receipt = release_fixture(tmp_path)
    value = json.loads(watch.read_bytes())
    value.update(installed_version=installed, last_checked_at="later")
    watch.write_bytes(tx.encoded(value))
    with pytest.raises(tx.InstallError, match="installed.version"):
        tx.rollback(target, receipt["transaction"])
    assert (target / "fresh").exists()
    assert not (target / "old").exists()
    assert json.loads(watch.read_bytes()) == value


@pytest.mark.parametrize("corruption", ["before", "after", "live-json", "live-mode"])
def test_release_rollback_checks_both_retained_images_and_live_document(tmp_path, corruption):
    tx, target, watch, receipt = release_fixture(tmp_path)
    if corruption in ("before", "after"):
        retained = target / tx.TRANSACTIONS / receipt["transaction"] / corruption / "3"
        retained.write_bytes(b"corrupted image")
    elif corruption == "live-json":
        watch.write_bytes(b"not JSON")
    else:
        watch.chmod(0o600)
    with pytest.raises(tx.InstallError):
        tx.rollback(target, receipt["transaction"])
    assert (target / "fresh").exists()
    assert not (target / "old").exists()


def test_release_observation_restore_resumes_after_interruption_and_is_idempotent(tmp_path, monkeypatch):
    tx, target, watch, receipt = release_fixture(tmp_path)
    value = json.loads(watch.read_bytes())
    value.update(last_checked_at="poll before rollback", latest_version="v1.0.0")
    watch.write_bytes(tx.encoded(value))
    original = tx._remove
    def interrupted(path):
        if path == target / tx.INSTALLATION:
            raise OSError("interrupted after release observation restore")
        return original(path)
    monkeypatch.setattr(tx, "_remove", interrupted)
    with pytest.raises(tx.InstallError, match="recoverable"):
        tx.rollback(target, receipt["transaction"])
    restored = json.loads(watch.read_bytes())
    assert restored["installed_version"] == "v1.0.0"
    assert restored["pending_version"] == ""
    assert restored["status"] == "current"
    monkeypatch.setattr(tx, "_remove", original)
    assert tx.rollback(target, receipt["transaction"])["status"] == "rolled-back"
    assert json.loads(watch.read_bytes()) == restored
    restored.update(latest_version="v4.0.0", pending_version="v4.0.0", status="pending-install",
                    last_checked_at="poll after rollback", last_notified_at="notification after rollback")
    watch.write_bytes(tx.encoded(restored))
    assert tx.rollback(target, receipt["transaction"])["status"] == "rolled-back"
    assert json.loads(watch.read_bytes()) == restored


def test_real_updater_write_state_observation_is_rollback_compatible(tmp_path, monkeypatch):
    import importlib.util
    tx, target, watch, receipt = release_fixture(tmp_path)
    source = Path(__file__).resolve().parents[1] / "scripts/update-core-prompts.py"
    spec = importlib.util.spec_from_file_location("transaction_updater_probe", source)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    paths = module.Paths(support_root=target / ".core-prompts-updater", home=target)
    observed = module.write_state(paths, installed_version="v2.0.0", latest_version="v3.0.0",
                                  pending_version="v3.0.0", status="pending-install", note="real updater polling",
                                  last_notified_at="notification", verified_bundle_sha256="digest")
    tx.rollback(target, receipt["transaction"])
    assert json.loads(watch.read_bytes()) == {**observed, "installed_version": "v1.0.0"}


def test_corrupt_derived_release_restore_image_blocks_resume(tmp_path, monkeypatch):
    tx, target, watch, receipt = release_fixture(tmp_path)
    value = json.loads(watch.read_bytes())
    watch.write_bytes(tx.encoded({**value, "last_checked_at": "later polling"}))
    original = tx._remove
    def interrupted(path):
        if path == target / tx.INSTALLATION:
            raise OSError("interrupted")
        return original(path)
    monkeypatch.setattr(tx, "_remove", interrupted)
    with pytest.raises(tx.InstallError):
        tx.rollback(target, receipt["transaction"])
    journal = target / tx.TRANSACTIONS / receipt["transaction"] / "journal.json"
    data = json.loads(journal.read_bytes())
    data["release_restore"]["content"] = base64.b64encode(b"tampered").decode()
    journal.write_bytes(tx.encoded(data))
    monkeypatch.setattr(tx, "_remove", original)
    before = watch.read_bytes()
    with pytest.raises(tx.InstallError, match="corrupt derived"):
        tx.rollback(target, receipt["transaction"])
    assert watch.read_bytes() == before
    assert (target / tx.INSTALLATION).exists()
