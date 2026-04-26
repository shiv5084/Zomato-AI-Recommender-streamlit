import sys
import os
import pytest
from unittest.mock import patch
from phase0.cli import _handle_doctor, _check_env_var, _check_file, _check_command

def test_missing_env_var():
    # Detects: Missing API key (0.1 Configuration and Environment)
    with patch.dict(os.environ, clear=True):
        ok, msg = _check_env_var("OPENAI_API_KEY")
        assert not ok
        assert "OPENAI_API_KEY is not set" in msg

def test_present_env_var():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy"}):
        ok, msg = _check_env_var("OPENAI_API_KEY")
        assert ok
        assert "OPENAI_API_KEY is set" in msg

def test_python_runtime_check(capsys):
    # Detects: Different Python runtime than documented (0.2 Dependency and Runtime Mismatch)
    with patch("sys.version_info", (3, 9)):
        _handle_doctor()
        captured = capsys.readouterr()
        assert "[FAIL] python>=3.10" in captured.out

def test_doctor_command_fails_fast_on_missing_config(capsys):
    # Tests that `doctor` command correctly identifies failure and returns exit code 1
    with patch.dict(os.environ, clear=True):
        exit_code = _handle_doctor()
        captured = capsys.readouterr()
        assert "[FAIL] OPENAI_API_KEY: OPENAI_API_KEY is not set" in captured.out
        assert exit_code == 1

def test_doctor_command_success(capsys):
    with patch("sys.version_info", (3, 11)):
        with patch("phase0.cli._check_command", return_value=(True, "git found")), \
             patch("phase0.cli._check_file", return_value=(True, ".env.example exists")), \
             patch("phase0.cli._check_env_var", return_value=(True, "var is set")):
            exit_code = _handle_doctor()
            captured = capsys.readouterr()
            assert exit_code == 0
            assert "All doctor checks passed." in captured.out
