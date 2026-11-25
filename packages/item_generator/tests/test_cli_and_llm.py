from types import SimpleNamespace

import pytest
from fromage_item_generator import LLMResult, cli
from fromage_item_generator import llm as llm_module

BRIEF = '{"candidate_brief": "Vous parlez de votre logement.", "suggested_angles": ["Où"]}'


class FakeLLM:
    def __init__(self, model):
        self.replies = iter([BRIEF, "not json"])

    def complete(self, system, user, metadata=None):
        return LLMResult(next(self.replies), 100, 50)

    def flush(self):
        pass


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setattr(llm_module, "AnthropicLLM", FakeLLM)


def args(tmp_path, *extra, part="monologue_suivi"):
    return [
        "--exam",
        "delf-a2-tp",
        "--part",
        part,
        "--theme",
        "logement",
        "--out",
        str(tmp_path),
        *extra,
    ]


def test_success_exit_code_and_cost_line(fake_llm, tmp_path, capsys):
    assert cli.main(args(tmp_path, "--n", "1")) == 0
    out = capsys.readouterr().out
    assert "1/1 Items" in out
    assert "cost $" in out


def test_partial_failure_exits_1(fake_llm, tmp_path, capsys):
    assert cli.main(args(tmp_path, "--n", "2")) == 1
    assert "skipped invalid Item" in capsys.readouterr().err


def test_unknown_part_exits_2(fake_llm, tmp_path):
    assert cli.main(args(tmp_path, part="nope")) == 2


def test_n_below_one_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(args(tmp_path, "--n", "0"))


def test_exam_id_cannot_be_a_path(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["--exam", "../x", "--part", "p", "--theme", "t", "--out", str(tmp_path)])


def test_unknown_exam_exits_2(tmp_path):
    assert cli.main(["--exam", "nope", "--part", "p", "--theme", "t", "--out", str(tmp_path)]) == 2


class FakeObservation:
    def __init__(self):
        self.updates = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, **kwargs):
        self.updates.append(kwargs)


def test_anthropic_adapter_extracts_text_usage_truncation_and_traces(monkeypatch):
    observation = FakeObservation()
    started = []
    langfuse = SimpleNamespace(
        start_as_current_observation=lambda **kw: started.append(kw) or observation
    )
    message = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="{}"), SimpleNamespace(type="other")],
        usage=SimpleNamespace(input_tokens=7, output_tokens=3),
        stop_reason="max_tokens",
    )
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: message))
    monkeypatch.setattr(llm_module.anthropic, "Anthropic", lambda: client)
    monkeypatch.setattr(llm_module, "get_client", lambda: langfuse)

    result = llm_module.AnthropicLLM("m").complete("s", "u", {"theme": "logement"})

    assert result == LLMResult("{}", 7, 3, truncated=True)
    assert observation.updates[0]["usage_details"] == {"input": 7, "output": 3}
    assert started[0]["metadata"] == {"theme": "logement"}
