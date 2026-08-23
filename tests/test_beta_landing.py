from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
PAGES = {
    "es": ROOT / "website" / "index.html",
    "en": ROOT / "website" / "en" / "index.html",
}
STYLESHEET = ROOT / "website" / "style.css"
COMMAND = "curl -fsSL https://www.linuxremoteplayer.com/beta/install.sh | sudo bash"
PROHIBITED = (
    "paddle",
    "premium",
    "license",
    "licencia",
    "purchase",
    "compr",
    "ai",
    "cloud",
    "docs",
    "document",
    "changelog",
    "novedad",
    "terms",
    "download",
    "descarg",
)


class VisiblePage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.body_depth = 0
        self.hidden_depth = 0
        self.text = []
        self.links = []
        self.images = []
        self.commands = []
        self.in_code = False
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        self.attributes.append(attrs)
        if tag == "body":
            self.body_depth = 1
        elif self.body_depth:
            if tag in {"script", "style"}:
                self.hidden_depth += 1
            if tag == "a":
                self.links.append(attrs.get("href", ""))
            if tag == "img":
                self.images.append(attrs.get("src", ""))
            if tag == "code":
                self.in_code = True

    def handle_endtag(self, tag):
        if tag == "body":
            self.body_depth = 0
        elif self.body_depth:
            if tag in {"script", "style"}:
                self.hidden_depth -= 1
            if tag == "code":
                self.in_code = False

    def handle_data(self, data):
        if self.body_depth and not self.hidden_depth:
            self.text.append(data)
            if self.in_code:
                self.commands.append(data.strip())


def parse_page(path):
    parser = VisiblePage()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def test_beta_landing_has_exact_copy_and_single_command():
    expected = {
        "es": (
            "BETA OPT-IN · 1.99.x",
            "LinuxRemotePlayer beta",
            "Canal voluntario para probar la distribución antes de 2.0.0.",
            "Tu instalación estable 1.9.1 no cambia ni descubre esta beta.",
            "Requiere Debian/Ubuntu Linux con systemd.",
            "Riesgo aceptado: esta beta aún no tiene firma independiente, protección de downgrade ni rollback.",
        ),
        "en": (
            "OPT-IN BETA · 1.99.x",
            "LinuxRemotePlayer beta",
            "A voluntary channel for testing distribution before 2.0.0.",
            "Your stable 1.9.1 installation is unchanged and cannot discover this beta.",
            "Requires Debian/Ubuntu Linux with systemd.",
            "Accepted risk: this beta does not yet have independent signing, downgrade protection, or rollback.",
        ),
    }
    for language, path in PAGES.items():
        page = parse_page(path)
        visible = " ".join(" ".join(page.text).split())
        for phrase in expected[language]:
            assert phrase in visible
        assert page.commands == [COMMAND]
        assert visible.count(COMMAND) == 1


def test_beta_landing_uses_only_the_approved_class_based_structure():
    for language, path in PAGES.items():
        page = parse_page(path)
        source = path.read_text(encoding="utf-8")
        assert "<style" not in source.lower()
        assert all("style" not in attrs for attrs in page.attributes)
        assert re.search(r"<main>\s*<section class=\"center\">", source)
        assert page.tags.count("section") == 1
        assert page.tags.count("h1") == 1
        assert page.tags.count("code") == 1
        assert 'class="section-title"' in source
        assert 'class="section-sub"' in source
        assert 'class="terminal"' in source
        assert 'class="terminal-header"' in source
        assert 'class="terminal-body"' in source
        assert 'class="terminal-cmd"' in source
        assert 'class="brand"' in source
        assert 'class="btn btn-outline"' in source
        assert f'href="{"/en/" if language == "es" else "../"}"' in source
        assert "<nav" not in source


def test_beta_landing_has_namespaced_responsive_css_only():
    css = STYLESHEET.read_text(encoding="utf-8")
    for path in PAGES.values():
        source = path.read_text(encoding="utf-8")
        assert '<body class="beta-landing">' in source
        assert "style=" not in source
        assert "<style" not in source.lower()
    assert ".beta-landing .nav-inner" in css
    assert ".beta-landing .btn.btn-outline" in css
    assert ".beta-landing main" in css
    assert ".beta-landing section" in css
    assert ".beta-landing .terminal" in css
    assert ".beta-landing .terminal-body" in css
    assert "box-sizing: border-box" in css
    assert "overflow-wrap: anywhere" in css
    assert ".beta-landing .terminal-body {\n    min-width: 0;\n    overflow-x: auto;" in css
    beta_css = css[css.index("/* ---------- beta landing responsive bounds ---------- */") :]
    assert "overflow: hidden" not in beta_css
    assert "overflow-x: hidden" not in beta_css
    assert re.search(r"(?m)^\s*(?:html|body|main|section)\s*\{[^}]*overflow", beta_css) is None


def test_beta_landing_has_only_the_language_link_and_no_screenshot():
    assert parse_page(PAGES["es"]).links == ["/en/"]
    assert parse_page(PAGES["en"]).links == ["../"]
    for path in PAGES.values():
        page = parse_page(path)
        assert page.images
        assert all("screenshot" not in image.lower() for image in page.images)


def test_beta_landing_has_no_prohibited_visible_or_navigable_references():
    for path in PAGES.values():
        source = path.read_text(encoding="utf-8")
        page = parse_page(path)
        visible = " ".join(" ".join(page.text).split()).lower()
        links = " ".join(page.links).lower()
        assert not re.search(r"https?://[^\s]*latest\.json", links)
        for prohibited in PROHIBITED:
            assert prohibited not in visible
            assert prohibited not in links
        assert "install.sh" in COMMAND
