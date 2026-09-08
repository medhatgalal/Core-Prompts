from __future__ import annotations

import json
from pathlib import Path

from intent_pipeline.uac_baselines import resolve_historical_baseline
from intent_pipeline.capability_resources import effective_capability_text


ROOT = Path(__file__).resolve().parents[1]
SSOT_PATH = ROOT / "ssot" / "engos-meta-supercharge.md"


def _text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return effective_capability_text(ROOT, "engos-meta-supercharge", text) if path == SSOT_PATH else text


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    next_start = text.find("\n## ", start + len(heading))
    if next_start == -1:
        return text[start:]
    return text[start:next_start]


def test_supercharge_preserves_existing_module_contract_markers() -> None:
    text = _text(SSOT_PATH)
    expectations = {
        "## MODULE: /ult": [
            "### Critical Execution Rule (ULT)",
            "`Generated Prompt`",
            "`Execution Output`",
            "`Why This Is Better`",
        ],
        "## MODULE: /catchup": [
            "Reconstruction only. Do not propose new solutions.",
            "Validation Status: PASS | FAIL",
            "Exactly one table, no leading prose",
        ],
        "## MODULE: /basis": [
            "`Basis Map`",
            "`Actual-to-Minimum Ratio`",
            "`Proof Needed`",
        ],
        "## MODULE: /simple": [
            "`Complexity Diagnosis`",
            "`Decomplect Plan`",
            "`Why This Is Simpler`",
        ],
        "## MODULE: /invert": [
            "`Inversion Analysis`",
            "`Dogs Not Barking`",
            "`Guarded Forward Solution`",
        ],
        "## MODULE: /contract": [
            "`Contract Spec`",
            "`QA Evaluation JSON`",
            '"overall_score": 0',
        ],
        "## MODULE: /grade": [
            "Default to up to 10 actual candidate trials;",
            "`Iteration Ladder`",
            "`Final Artifact`",
        ],
        "## MODULE: /full": [
            "Run sequential passes and show outputs per pass.",
            "`PASS 3 — ADVERSARIAL`",
            "`PASS 5 — GRADE (up to 10 trials)`",
        ],
        "## MODULE: /gaslight": [
            "Never run unless explicitly invoked by `/gaslight`.",
            "### GASLIGHT 13 — Canonical Technique IDs",
            "Promise Reciprocity",
        ],
        "## MODULE: /stop-ult": [
            "Exit `/ult` mode",
            "does not disable SuperCharge itself",
        ],
    }

    for heading, markers in expectations.items():
        section = _section(text, heading)
        for marker in markers:
            assert marker in section, f"{heading} lost marker {marker!r}"


def test_supercharge_help_exposes_debate_deep_and_examples() -> None:
    text = _text(SSOT_PATH)
    help_text = _text(ROOT / "sources/capability-resources/engos-meta-supercharge/references/help.md")

    assert 'version: "v5.0"' in text
    assert "# End of SuperCharge v5.0" in text
    assert "# End of SuperCharge v4.1" not in text
    assert "SuperCharge v5.0" in help_text
    assert "Ask `engos-meta-supercharge /help examples`" in help_text
    assert "`engos-meta-supercharge /adversarial /debate <task>`" in help_text
    assert "`engos-meta-supercharge /adversarial /debate /deep <task>`" in help_text
    assert help_text.index("/adversarial /debate <task>") < help_text.index("/adversarial /debate /deep <task>")
    assert "### Stack Examples" in help_text
    assert "Stacking is sequential" in help_text

    examples = _text(ROOT / "sources/capability-resources/engos-meta-supercharge/references/help-examples.md")
    assert "/adversarial /debate`" in examples
    assert "/adversarial /debate /deep`" in examples
    assert examples.index("/adversarial /debate`") < examples.index("/adversarial /debate /deep`")
    assert "Do not execute any examples." in examples


def test_supercharge_adversarial_debate_contract_is_operational() -> None:
    text = _text(SSOT_PATH)
    section = _section(text, "## MODULE: /adversarial")

    for marker in (
        "`Attack Surface`",
        "`Contradictions / Gaps`",
        "`Mitigations / Fixes`",
        "`Residual Risk`",
        "### Nested Module: /adversarial /debate",
        "`Bull Case`",
        "`Bear Case`",
        "`Decider Verdict`",
        "`Confidence: 0-100`",
        "`Flip Conditions`",
        "### Nested Module: /adversarial /debate /deep",
        "`Bull Opening`",
        "`Bear Rebuttal`",
        "`Bull Counter`",
        "`Bear Final Challenge`",
        "`Decision-Risk Table`",
        "`Recommended Next Validation`",
        "`code_review`",
        "`architecture_decision`",
        "`investing_analysis`",
    ):
        assert marker in section


def test_supercharge_historical_baseline_remains_unchanged():
    baseline = resolve_historical_baseline(ROOT, "engos-meta-supercharge")
    import hashlib
    assert hashlib.sha256(baseline.baseline_text.encode()).hexdigest() == "488bc14a2fa4e3ce625adad07c98b2aa7a6af38d6ddbee64e182b2db82d9897a"
    assert "version: v4.0" in baseline.baseline_text


def test_supercharge_generated_surfaces_include_debate_contract() -> None:
    generated_paths = [
        ROOT / ".codex" / "skills" / "engos-meta-supercharge" / "SKILL.md",
        ROOT / ".gemini" / "skills" / "engos-meta-supercharge" / "SKILL.md",
        ROOT / ".claude" / "skills" / "engos-meta-supercharge" / "SKILL.md",
        ROOT / ".kiro" / "skills" / "engos-meta-supercharge" / "SKILL.md",
    ]

    for path in generated_paths:
        text = effective_capability_text(ROOT, "engos-meta-supercharge", _text(path))
        assert "SuperCharge v5.0" in text
        assert "/adversarial /debate <task>" in text
        assert "/adversarial /debate /deep <task>" in text
        assert text.index("/adversarial /debate <task>") < text.index("/adversarial /debate /deep <task>")
        assert "## HELP EXAMPLES OUTPUT" in text
        assert "`Bull Case`" in text
        assert "`Bull Opening`" in text


def test_supercharge_descriptor_and_resources_preserve_uac_boundaries() -> None:
    descriptor = json.loads((ROOT / ".meta" / "capabilities" / "engos-meta-supercharge.json").read_text(encoding="utf-8"))
    descriptor_text = json.dumps(descriptor, sort_keys=True)

    assert descriptor["layers"]["minimal"]["capability_type"] == "both"
    assert descriptor["layers"]["minimal"]["version"] == "v5.0"
    assert descriptor["declared_capability"] == "both"
    assert descriptor["layers"]["minimal"]["tool_policy"]["scope"] == "uac_intake_only"
    assert "orchestration" in descriptor["layers"]["minimal"]["tool_policy"]["forbidden"]
    assert "delegation decisions" in descriptor["layers"]["minimal"]["tool_policy"]["forbidden"]
    assert "runtime execution control" in descriptor["layers"]["minimal"]["tool_policy"]["forbidden"]
    assert "adversarial debate" in descriptor_text.lower()
    assert any("run adversarial debate" in hint for hint in descriptor["invocation_hints"])

    codex_agent = (ROOT / ".codex" / "agents" / "engos-meta-supercharge.toml").read_text(encoding="utf-8")
    assert "\ntools =" not in codex_agent

    resource_paths = [
        ROOT / ".codex" / "skills" / "engos-meta-supercharge" / "resources" / "capability.json",
        ROOT / ".gemini" / "skills" / "engos-meta-supercharge" / "resources" / "capability.json",
        ROOT / ".claude" / "skills" / "engos-meta-supercharge" / "resources" / "capability.json",
        ROOT / ".kiro" / "skills" / "engos-meta-supercharge" / "resources" / "capability.json",
    ]
    for path in resource_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["layers"]["minimal"]["capability_type"] == "both"
        assert payload["layers"]["minimal"]["version"] == "v5.0"


def test_supercharge_namespace_keeps_conversational_prefix_and_dispatch_contract():
    text = _text(SSOT_PATH)
    activation = text.split('### Activation Triggers', 1)[1].split('### Help Triggers', 1)[0]
    for prefix in ('`engos-meta-supercharge`', '`/engos-meta-supercharge`',
                   '`supercharge`', '`/supercharge`'):
        assert prefix in activation
    assert 'case-insensitive' in activation
    assert 'Normalize only the leading capability name' in activation
    assert 'preserve every following module, modifier, argument, and their order' in activation
    assert 'same help, examples, details, stacking, and terminal-control precedence' in activation
    assert '`Supercharge /full`' in activation
    assert '`supercharge /simple /invert /contract <task>`' in activation
    assert 'do not register native CLI menu aliases' in activation
    precedence = text.split('### Terminal-Control Precedence', 1)[1].split('### Command Grammar', 1)[0]
    assert '`/stop`' not in precedence
    assert precedence.index('`/stop-ult`') < precedence.index('Help, examples, and details')
