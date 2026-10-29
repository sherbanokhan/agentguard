# Tests for the secure agent.
#
# These use the same attack articles as test_vulnerable_agent.py.
# There, the tests pass when the attacks work. Here, they pass when
# the attacks get blocked and normal requests still go through.

import logging

import pytest

from app import secure_agent as secure


@pytest.fixture
def lab(tmp_path, monkeypatch):
    # Same idea as before: a fresh temporary lab for every test,
    # so nothing touches my real app/lab_data folder
    lab_dir = tmp_path / "lab_data"
    private_dir = tmp_path / "lab_private"

    monkeypatch.setattr(secure, "LAB_DIR", lab_dir)
    monkeypatch.setattr(secure, "PRIVATE_DIR", private_dir)

    secure.setup_lab()
    return lab_dir


# ----- Layer 1: the agent doesn't follow instructions in content -----

def test_exfil_article_does_not_send_anything(lab, capsys):
    result = secure.secure_agent(secure.ARTICLE_EXFIL)

    assert result["actions_taken"] == []
    assert "[SIMULATED SEND]" not in capsys.readouterr().out


def test_traversal_article_does_not_leak_ssh_key(lab, capsys):
    result = secure.secure_agent(secure.ARTICLE_TRAVERSAL)

    assert result["actions_taken"] == []
    assert "DEMO_SSH_KEY_NOT_REAL_67890" not in capsys.readouterr().out


def test_injection_is_detected(lab):
    result = secure.secure_agent(secure.ARTICLE_EXFIL)
    assert result["injection_detected"] is True


def test_benign_article_is_summarized_without_warning(lab, capsys):
    # Making sure the defenses don't break normal use (no false positive here)
    article = "How to reset your password.\nGo to the settings page and click reset."

    result = secure.secure_agent(article)

    assert result["summary"] == "How to reset your password."
    assert result["injection_detected"] is False
    assert "[WARNING]" not in capsys.readouterr().out


# ----- Layer 2: the tools block bad input on their own -----

def test_read_blocks_path_traversal(lab):
    with pytest.raises(secure.SecurityViolation):
        secure.safe_read_file("../lab_private/fake_ssh_key.txt")


def test_read_blocks_absolute_path(lab):
    # Made-up path. It's rejected before any file is opened.
    with pytest.raises(secure.SecurityViolation):
        secure.safe_read_file("/Users/attacker/.ssh/id_ed25519")


def test_read_still_allows_files_inside_lab(lab):
    # The fix shouldn't stop the agent from reading files it's supposed to
    assert secure.safe_read_file("fake_api_key.txt") == "DEMO_KEY_NOT_REAL_12345"


def test_send_blocks_unapproved_destination(lab, capsys):
    with pytest.raises(secure.SecurityViolation):
        secure.safe_send_message("attacker@example.test", "secret")

    assert "[SIMULATED SEND]" not in capsys.readouterr().out


def test_send_allows_approved_destination(lab, capsys):
    secure.safe_send_message("support-team@example.test", "hello")
    assert "[SIMULATED SEND] Destination: support-team@example.test" in capsys.readouterr().out


# ----- Layer 3: blocked actions show up in the log -----

def test_blocked_read_is_logged(lab, caplog):
    with caplog.at_level(logging.WARNING, logger="agentguard.security"):
        with pytest.raises(secure.SecurityViolation):
            secure.safe_read_file("../lab_private/fake_ssh_key.txt")

    assert "BLOCKED read_file: path traversal attempt" in caplog.text