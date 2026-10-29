from pathlib import Path


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


def test_active_docs_declare_only_the_certified_platform():
    corpus = "\n".join(text(path) for path in ACTIVE)
    required = (
        "x86_64",
        "UEFI",
        "4 GB",
        "HD 2500",
        "GPL",
    )
    for phrase in required:
        assert phrase in corpus
    assert "KDE Neon" not in corpus
    assert "Plasma Bigscreen" not in corpus
    assert "Wayland" not in corpus
    assert "Appliance mode" not in corpus
    assert "Desktop mode" not in corpus


def test_es_and_en_active_pages_have_matching_support_facts():
    landing_facts = ("x86_64", "UEFI", "4 GB", "HD 2500", "GPL", "APK", "PWA")
    docs_facts = landing_facts
    terms_facts = ("x86_64", "UEFI", "4 GB", "HD 2500", "GPL")
    pairs = (
        (ROOT / "website" / "index.html", ROOT / "website" / "en" / "index.html", landing_facts),
        (ROOT / "website" / "docs.html", ROOT / "website" / "en" / "docs.html", docs_facts),
        (ROOT / "website" / "terminos.html", ROOT / "website" / "en" / "terms.html", terms_facts),
    )
    for es, en, facts in pairs:
        es_source, en_source = text(es), text(en)
        for fact in facts:
            assert fact in es_source, f"{fact!r} missing from {es.name}"
            assert fact in en_source, f"{fact!r} missing from {en.name}"
        assert "garant" in es_source.lower()
        assert "guarante" in en_source.lower()


def test_changelog_and_history_are_excluded_from_support_facts():
    excluded = (
        "website/changelog.html",
        "website/en/changelog.html",
        "archive/",
    )
    for path in excluded:
        assert path not in {file.as_posix() for file in ACTIVE}
