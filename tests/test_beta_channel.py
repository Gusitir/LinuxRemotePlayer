import logging
import ast
import os
import socket

import pytest


@pytest.fixture
def main_module(monkeypatch):
    monkeypatch.delenv("LRP_CHANNEL", raising=False)

    # Load only the channel/config contract because the optional application runtime
    # dependencies (for example segno) are not installed in the test environment.
    source = open("backend/main.py", encoding="utf-8").read()
    tree = ast.parse(source)
    wanted = {
        "STABLE_CHANNEL", "BETA_CHANNEL",
        "get_channel", "get_config",
    }
    nodes = []
    for node in tree.body:
        is_wanted_assignment = isinstance(node, (ast.Assign, ast.AnnAssign)) and any(
            isinstance(target, ast.Name) and target.id in wanted
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
        if is_wanted_assignment:
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted:
            node.decorator_list = []
            nodes.append(node)
    namespace = {
        "os": os,
        "logger": logging.getLogger("main"),
        "socket": socket,
        "VERSION": "1.0.0",
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "backend/main.py", "exec"), namespace)

    return type("MainContract", (), namespace)


@pytest.mark.parametrize("value", [None, "", "   ", "production", "stable-beta", "1"])
def test_missing_empty_invalid_channel_defaults_to_stable(main_module, monkeypatch, value):
    if value is None:
        monkeypatch.delenv("LRP_CHANNEL", raising=False)
    else:
        monkeypatch.setenv("LRP_CHANNEL", value)
    assert main_module.get_channel() == "stable"


def test_invalid_channel_logs_warning(main_module, monkeypatch, caplog):
    monkeypatch.setenv("LRP_CHANNEL", "canary")
    with caplog.at_level(logging.WARNING, logger="main"):
        assert main_module.get_channel() == "stable"
    assert "Invalid LRP_CHANNEL" in caplog.text


@pytest.mark.parametrize("value, expected", [("stable", "stable"), (" beta ", "beta")])
def test_explicit_channels_are_normalized(main_module, monkeypatch, value, expected):
    monkeypatch.setenv("LRP_CHANNEL", value)
    assert main_module.get_channel() == expected


def test_api_config_exposes_normalized_channel(main_module, monkeypatch):
    monkeypatch.setenv("LRP_CHANNEL", "not-beta")
    assert main_module.get_config()["channel"] == "stable"
    monkeypatch.setenv("LRP_CHANNEL", "beta")
    assert main_module.get_config()["channel"] == "beta"
