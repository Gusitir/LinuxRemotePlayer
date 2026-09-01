from pathlib import Path
import subprocess


ROOT = Path(__file__).parents[1]
ACTIVE = (
    ROOT / "README.md",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "DEVELOPING.md",
    ROOT / "website" / "index.html",
    ROOT / "website" / "en" / "index.html",
    ROOT / "website" / "docs.html",
    ROOT / "website" / "en" / "docs.html",
    ROOT / "website" / "terminos.html",
    ROOT / "website" / "en" / "terms.html",
    ROOT / "backend" / ".env.example",
)


def text(path):
    return path.read_text(encoding="utf-8")


def test_active_docs_declare_only_the_certified_host_and_session():
    corpus = "\n".join(text(path) for path in ACTIVE)
    required = (
        "Debian 13 stable amd64 minimal",
        "NVIDIA RTX 3060 12 GB",
        "Xorg/Openbox",
        "Firefox ESR",
        "LRP_MODE=htpc",
    )
    for phrase in required:
        assert phrase in corpus
    assert "KDE Neon" not in corpus
    assert "Plasma Bigscreen" not in corpus
    assert "Wayland" not in corpus
    assert "Appliance mode" not in corpus
    assert "Desktop mode" not in corpus


def test_es_and_en_active_pages_have_matching_support_facts():
    pairs = (
        (ROOT / "website" / "index.html", ROOT / "website" / "en" / "index.html"),
        (ROOT / "website" / "docs.html", ROOT / "website" / "en" / "docs.html"),
        (ROOT / "website" / "terminos.html", ROOT / "website" / "en" / "terms.html"),
    )
    for es, en in pairs:
        es_source, en_source = text(es), text(en)
        for fact in ("Debian 13 stable amd64 minimal", "NVIDIA RTX 3060 12 GB", "Xorg/Openbox", "Firefox ESR"):
            assert fact in es_source
            assert fact in en_source
        assert "garant" in es_source.lower()
        assert "guarante" in en_source.lower()


def test_changelog_and_history_are_excluded_and_unchanged():
    excluded = (
        "website/changelog.html",
        "website/en/changelog.html",
        "archive/",
    )
    for path in excluded:
        assert path not in {file.as_posix() for file in ACTIVE}
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *excluded, "archive/"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
