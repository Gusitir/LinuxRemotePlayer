# WEB_DESIGN_SPEC — LinuxRemotePlayer purchase website (machine-optimized)

```yaml
document_type: design_specification
audience: AI coding agent (Gemini) — implement PHASE C4 of PLAN_COMERCIALIZACION.md
deliverables: [website/index.html, website/gracias.html, website/vercel.json]
tech_constraints:
  - Single-file pages: all CSS inline in a <style> block. No frameworks, no JS libraries,
    no build step. Only vanilla JS for: copy-to-clipboard, FAQ accordion, mobile nav.
  - System font stack (no webfont requests). SVG icons inline (reuse the app's stroke
    style: stroke-width 2, round caps — same family as frontend/index.html icons).
  - Weight budget: < 300KB total. Images: only icon-192/512.png + inline SVG mockup.
  - Language: ALL copy in Spanish (provided verbatim below — use it, do not rewrite).
  - Placeholders to leave as-is for the owner: {{BUY_URL}}, {{REPO_URL}}, {{SUPPORT_EMAIL}}.
```

---

## 1. DESIGN SYSTEM

```yaml
concept: >
  "El control remoto que tu PC con Linux merece." Dark cinematic theme that matches the
  app itself (the product IS dark-UI), with one confident accent color. Feels like a
  living-room product, not a dev tool: big type, generous spacing, soft glows evoking a
  TV in a dark room.
palette:
  bg-base:        "#0b1220"   # page background (same as app drawer)
  bg-raised:      "#111827"   # cards / sections alt
  bg-elevated:    "#1f2937"   # code blocks, inputs
  border:         "#28364d"   # 1px card borders
  text-primary:   "#f3f4f6"
  text-secondary: "#9ca3af"
  accent:         "#3b82f6"   # primary CTA, links (app's blue)
  accent-hover:   "#2563eb"
  success:        "#22c55e"   # buy CTA + checkmarks (app's green glow)
  glow:           "rgba(59,130,246,0.25)"  # radial glows behind hero/mockup
typography:
  stack: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif
  h1: clamp(2.2rem, 6vw, 3.5rem); weight 800; line-height 1.1; letter-spacing -0.02em
  h2: clamp(1.5rem, 4vw, 2.1rem); weight 700
  body: 1.06rem / 1.7; color text-secondary
  mono (keys/terminal): ui-monospace, SFMono-Regular, Menlo, Consolas, monospace
layout:
  max-width: 1080px centered; section vertical padding clamp(64px, 10vw, 120px)
  radius: 16px cards, 12px buttons, 10px code blocks
  buttons: primary = success bg, white text, subtle shadow 0 8px 24px rgba(34,197,94,.25);
           secondary = transparent, 1px accent border, accent text
  breakpoints: single column <= 760px; grid rows collapse; nav becomes stacked/simple
effects:
  - hero background: two blurred radial-gradients (accent glow top-left, green glow
    bottom-right), position: absolute, pointer-events none — pure CSS, no images.
  - cards: hover -> translateY(-2px) + border-color accent; transition 0.2s.
  - scroll-behavior: smooth; sections have id anchors for nav.
accessibility:
  - contrast >= 4.5:1 for body text (values above comply); focus-visible outlines on all
    interactive elements; alt text everywhere; single h1; aria-expanded on FAQ buttons.
```

---

## 2. PAGE STRUCTURE — index.html (sections in order)

### 2.1 NAV (sticky, backdrop-blur, bg rgba(11,18,32,0.8))
```yaml
left:  icon-192.png (28px, rounded) + wordmark "LinuxRemotePlayer" (weight 700)
right_links: ["Cómo funciona" -> #como-funciona, "Características" -> #caracteristicas,
              "Instalación" -> #instalacion, "Precio" -> #precio, "FAQ" -> #faq]
cta: button primary small "Comprar licencia" -> {{BUY_URL}}
mobile: links hidden <=760px (keep logo + CTA only; no hamburger needed — page is short)
```

### 2.2 HERO
```yaml
layout: 2 columns (55/45); collapses to single column, text first.
badge_over_h1: pill, border 1px accent, text accent, small:
  "🐧 Para HTPCs y PCs con Linux"
h1: "Convierte tu PC con Linux en una Smart TV"
subtitle: >
  Control remoto completo desde tu teléfono: touchpad, teclado, apps de streaming y
  control por voz. Sin hardware extra, sin cuentas, funcionando en tu propia red.
cta_row:
  - primary (success): "Comprar licencia — pago único" -> {{BUY_URL}}
  - secondary: "Instalar gratis" -> #instalacion
trust_line (small, text-secondary, below CTAs):
  "✓ Control básico gratis y open source  ·  ✓ La licencia desbloquea la voz con IA  ·  ✓ Tus datos nunca salen de tu casa"
right_column_mockup: >
  Inline SVG phone mockup (~300x620 viewBox): rounded-rect phone frame (bg-elevated,
  border), inside it a simplified recreation of the real app UI stacked vertically:
  status dot + "Connected" (green), a 5-circle app row (use brand-ish colors
  #E50914 #FF0000 #1DB954 #113CCF #9146FF), a large dotted-texture touchpad rectangle,
  a center round blue play button flanked by two gray round buttons, and a green mic
  circle with glow (filter: drop-shadow). Behind the phone: the CSS radial glows.
  This mockup must be BUILT AS SVG by hand — do not reference screenshots.
```

### 2.3 CÓMO FUNCIONA (#como-funciona) — 3 steps, grid-cols-3
```yaml
section_title: "Listo en tres pasos"
cards:
  - icon: terminal SVG
    title: "1. Instala en tu PC"
    text: "Un solo comando en la terminal de tu PC con Linux. El instalador configura todo: servicio, HTTPS y permisos."
  - icon: qr/link SVG
    title: "2. Empareja tu teléfono"
    text: "Abre el enlace que te da el instalador, acepta el certificado una vez e instala la app en tu pantalla de inicio. Sin tiendas de apps."
  - icon: sofa/play SVG
    title: "3. Controla desde el sofá"
    text: "Netflix, YouTube, Spotify y tus apps de Linux. Touchpad, teclado y multimedia. Con licencia, también por voz."
```

### 2.4 CARACTERÍSTICAS (#caracteristicas) — grid 2x3 cards
```yaml
section_title: "Todo lo que trae"
cards:
  - {icon: pointer, title: "Touchpad y ratón", text: "Mueve el puntero, haz clic y scroll como en un portátil. Pulsación larga = clic derecho."}
  - {icon: keyboard, title: "Teclado del teléfono", text: "Escribe búsquedas con el teclado de tu móvil y aparece en la TV al instante."}
  - {icon: grid-apps, title: "Tus apps de streaming", text: "Netflix, YouTube, Max, Disney+, Twitch y más en modo kiosk a pantalla completa. Añade las tuyas."}
  - {icon: mic (accent green), title: "Control por voz con IA", text: "«Pon vídeos de gatos en YouTube». Transcripción y comprensión de intención con IA.", badge: "Con licencia"}
  - {icon: shield, title: "Privado por diseño", text: "Todo corre en tu red local con HTTPS y emparejamiento seguro. Sin cuentas, sin rastreo, sin nube obligatoria."}
  - {icon: refresh, title: "Actualizaciones integradas", text: "Un botón en Ajustes comprueba y aplica la última versión. Instalar y desinstalar también es un solo comando."}
```

### 2.5 INSTALACIÓN (#instalacion)
```yaml
section_title: "Instalación en un comando"
intro_line: "En tu PC con Linux (Debian/Ubuntu y derivados), pega esto en la terminal:"
terminal_block:
  style: bg-elevated, border, radius 10px, mono font, padding 18px, overflow-x auto;
         fake window dots (red/yellow/green 10px circles) in a slim header bar.
  content: "curl -fsSL {{REPO_URL_RAW}}/main/scripts/bootstrap.sh | sudo bash"
  copy_button: right side, secondary style, JS navigator.clipboard.writeText + swap label
               "Copiar" -> "¡Copiado!" for 2s.
below_terminal_steps (ordered list, compact):
  1. "El instalador te preguntará el modo (TV dedicada o escritorio) y hará el resto."
  2. "Al terminar verás un enlace de emparejamiento: ábrelo en el navegador del teléfono."
  3. "Añade la app a tu pantalla de inicio y listo."
footnote: "Requiere Linux con systemd y un navegador Chromium. Código fuente en GitHub → {{REPO_URL}}"
```

### 2.6 PRECIO (#precio) — single centered card, max-width 420px
```yaml
section_title: "Precio simple"
card:
  border: 1px solid success; subtle green glow shadow.
  plan_name: "Licencia Personal"
  price_line: "9,99 €" (h1-sized) + " / pago único" (text-secondary)   # PLACEHOLDER PRICE:
              # leave a HTML comment for the owner to sync with the Stripe price.
  includes (checkmark list, success-colored ✓):
    - "Control por voz con IA (60 comandos/día)"
    - "Todas las funciones del control incluidas"
    - "Actualizaciones incluidas"
    - "1 TV/PC por licencia"
    - "La clave llega a tu correo al instante"
  cta: primary full-width "Comprar ahora" -> {{BUY_URL}}
  under_cta_small: "Pago seguro procesado por Stripe. No almacenamos datos de tarjeta."
free_reminder_line (below card, centered, text-secondary):
  "¿Solo quieres el control sin voz? Es gratis y open source — ve a Instalación."
```

### 2.7 FAQ (#faq) — native <details>/<summary> accordion, styled
```yaml
section_title: "Preguntas frecuentes"
items:
  - q: "¿Cómo recibo mi licencia?"
    a: "Al completar el pago, tu clave (formato LRP-XXXX-XXXX-XXXX) llega a tu correo en 1–2 minutos. En la app: Ajustes → Clave de licencia → pégala → Activar."
  - q: "¿Funciona sin licencia?"
    a: "Sí. El control remoto completo (touchpad, teclado, apps, multimedia) es gratuito. La licencia desbloquea el control por voz con IA y las funciones premium futuras."
  - q: "¿Qué necesito?"
    a: "Un PC con Linux (Debian, Ubuntu, Mint o derivados) conectado a la TV, y un teléfono Android o iPhone en la misma red WiFi."
  - q: "¿Mis datos salen de mi casa?"
    a: "El control funciona 100% en tu red local. Solo los comandos de voz se envían a la nube para transcribirse, y únicamente si activas esa función."
  - q: "¿Puedo actualizar la app?"
    a: "Sí, desde Ajustes → Buscar actualizaciones, o ejecutando scripts/update.sh en el PC. Las actualizaciones están incluidas con tu licencia."
  - q: "¿Y si quiero desinstalarla?"
    a: "sudo ./scripts/uninstall.sh la elimina por completo: servicio, permisos, certificados y firewall."
  - q: "¿Reembolsos?"
    a: "Escríbenos a {{SUPPORT_EMAIL}} dentro de los 14 días posteriores a la compra y te devolvemos el dinero."
```

### 2.8 CTA FINAL — full-width band, bg-raised, centered
```yaml
h2: "Tu sofá te está esperando"
text: "Instala gratis en 5 minutos. Añade la voz cuando quieras."
buttons: [primary "Comprar licencia" -> {{BUY_URL}}, secondary "Ver instalación" -> #instalacion]
```

### 2.9 FOOTER
```yaml
columns_or_rows:
  - wordmark + "Hecho para el salón. Con cariño por el software libre."
  - links: GitHub ({{REPO_URL}}), Soporte (mailto:{{SUPPORT_EMAIL}}), FAQ (#faq)
  - legal_line: "© 2026 LinuxRemotePlayer · Los nombres Netflix, YouTube y demás marcas
    pertenecen a sus respectivos dueños; este producto no está afiliado a ellos."
```

---

## 3. PAGE STRUCTURE — gracias.html (post-purchase, Stripe redirect target)

```yaml
layout: single centered column, max-width 560px, vertically centered, same design system.
content_order:
  1. Big success checkmark: inline SVG circle+check, success color, soft glow.
  2. h1: "¡Gracias por tu compra!"
  3. p: "Tu clave de licencia está en camino. Revisa tu correo — suele llegar en 1 o 2
     minutos. Mira también la carpeta de spam."
  4. Card "Cómo activarla" (bg-raised, left-aligned, 3 steps):
     1) "Abre la app Remote Kiosk en tu teléfono."
     2) "Entra en Ajustes → Clave de licencia."
     3) "Pega la clave LRP-XXXX-XXXX-XXXX y toca Activar."
  5. Divider + small: "¿No llegó en 10 minutos? Escríbenos a {{SUPPORT_EMAIL}} con el
     correo que usaste al pagar y te la reenviamos."
  6. secondary button: "Volver al inicio" -> /
constraints: NO JavaScript needed on this page. NEVER render the license key here — it
  travels only by email (the page cannot know it and must not try to fetch it).
```

---

## 4. IMPLEMENTATION CHECKLIST (agent self-verification)

```yaml
- [ ] Zero external requests except icon PNGs (no CDNs, no fonts, no analytics).
- [ ] {{BUY_URL}}, {{REPO_URL}}, {{REPO_URL_RAW}}, {{SUPPORT_EMAIL}} appear as literal
      placeholders — grep-able, documented in a top-of-file HTML comment for the owner.
- [ ] All copy matches this spec verbatim (Spanish).
- [ ] Responsive at 360px, 768px, 1440px without horizontal scroll.
- [ ] <details> FAQ works without JS; copy button degrades silently if clipboard API missing.
- [ ] OG/meta: title "LinuxRemotePlayer — Convierte tu PC Linux en una Smart TV";
      description = hero subtitle; og:image = icon-512.png; lang="es".
- [ ] Lighthouse mobile: Performance >= 90, Accessibility >= 90, SEO >= 90.
- [ ] vercel.json: {"cleanUrls": true}. gracias.html reachable at /gracias.
```
