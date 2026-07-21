# -*- coding: utf-8 -*-
"""Remove PlatformLanding scoped layout rules — golden-ratio.css owns spacing/grid."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'PlatformLanding.vue'
text = p.read_text(encoding='utf-8')

old_style = """<style scoped>
.landing-page {
  min-height: 100vh;
  position: relative;
  font-family: var(--font-ui);
  background: transparent;
  color: var(--text);
}

.landing-shell {
  position: relative;
  z-index: 1;
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 0 clamp(20px, 3vw, 40px) 32px;
  min-height: calc(100vh - var(--nav-height, 72px));
  display: flex;
  flex-direction: column;
}

.splash-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: var(--landing-splash-bg, var(--page-bg));
  display: flex;
  align-items: center;
  justify-content: center;
  animation: splash-fade 0.5s ease 1.1s forwards;
}

.splash-card {
  padding: 28px 36px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gradient-card-border, var(--border));
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow);
}

@keyframes splash-fade {
  to { opacity: 0; pointer-events: none; }
}

.landing-hero {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  align-items: center;
  padding: clamp(32px, 6vh, 64px) 0;
}

@media (min-width: 900px) {
  .landing-hero {
    grid-template-columns: minmax(0, 1.15fr) minmax(240px, 300px) minmax(0, 0.65fr);
    gap: clamp(32px, 4vw, 56px);
    align-items: center;
  }

  .hero-copy {
    grid-column: 1;
  }
}

@media (min-width: 900px) {
  .hero-panel {
    grid-column: 2;
    max-width: 300px;
    justify-self: center;
  }
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: clamp(240px, 36vh, 420px);
  min-width: 0;
}

.hero-title {
  margin: 0;
  font-size: clamp(2.75rem, 8vw, 5.25rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.hero-title-main { color: var(--text); }
.hero-title-accent { color: var(--primary); }

.hero-desc {
  margin: 24px 0 0;
  max-width: 36em;
  font-size: var(--text-lg);
  line-height: var(--text-lg--line-height);
  color: var(--muted);
}

.hero-panel {
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--radius-xl);
  background: var(--gradient-card-bg, var(--landing-panel-bg, var(--card-bg)));
  box-shadow: var(--gradient-card-shadow);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
  width: 100%;
  max-width: none;
}

@media (min-width: 900px) {
  .hero-panel {
    max-width: 300px;
    justify-self: center;
  }
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
  margin: -16px -16px 2px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.quick-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 12px 10px;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--card-radius);
  cursor: pointer;
  font-family: inherit;
  color: var(--text);
  transition: border-color 0.2s, background 0.2s;
}

.quick-card:hover {
  border-color: var(--gradient-card-border-hover, var(--border));
  background: var(--hover);
}

.quick-card.primary {
  border-color: rgba(var(--primary-rgb), 0.35);
  background: rgba(var(--primary-rgb), 0.08);
}

.quick-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.quick-label {
  font-size: var(--text-sm);
  font-weight: 600;
}

.quick-card.primary .quick-label { color: var(--primary); }

.quick-hint {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--muted);
}

.shortcut-nav {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 2px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.shortcut-link {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--hover);
  cursor: pointer;
  font-family: inherit;
  color: var(--text);
  text-align: left;
  transition: border-color 0.2s, background 0.2s;
}

.shortcut-link:hover {
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.08);
}

.shortcut-label {
  font-size: var(--text-sm);
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 12px;
}

@media (min-width: 768px) {
  .feature-grid { grid-template-columns: repeat(4, 1fr); gap: 24px; }
}

.feature-card {
  padding: 28px 24px;
  background: var(--gradient-card-bg, var(--card-bg));
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--card-radius);
  box-shadow: var(--gradient-card-shadow);
  cursor: pointer;
  min-height: 180px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  border-color: var(--gradient-card-border-hover, var(--primary));
  box-shadow: var(--gradient-card-shadow-hover, var(--gradient-card-shadow));
}

.feature-title {
  margin: 12px 0 8px;
  font-size: var(--text-xl);
  font-weight: 600;
}

.feature-desc {
  margin: 0;
  font-size: var(--text-base);
  color: var(--muted);
  line-height: var(--text-base--line-height);
}

.landing-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  font-size: var(--text-xs);
  color: var(--muted);
  padding-top: 20px;
  margin-top: 24px;
  border-top: 1px solid var(--border);
}

.landing-footer .linux-uname {
  width: 100%;
  margin: 0 0 4px;
  border: none;
  border-radius: var(--card-radius);
}

.landing-footer a {
  color: var(--primary);
  text-decoration: none;
}

.landing-footer a:hover { text-decoration: underline; }
</style>"""

new_style = """<style scoped>
.landing-page {
  min-height: 100vh;
  position: relative;
  font-family: var(--font-ui);
  background: transparent;
  color: var(--text);
}

.landing-shell {
  position: relative;
  z-index: 1;
  max-width: none;
  width: 100%;
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 72px));
  display: flex;
  flex-direction: column;
}

.splash-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: var(--landing-splash-bg, var(--page-bg));
  display: flex;
  align-items: center;
  justify-content: center;
  animation: splash-fade 0.5s ease 1.1s forwards;
}

.splash-card {
  padding: var(--fib-34) var(--fib-55);
  border-radius: var(--radius-xl);
  border: 1px solid var(--gradient-card-border, var(--border));
  background: var(--gradient-card-bg, var(--card-bg));
  box-shadow: var(--gradient-card-shadow);
}

@keyframes splash-fade {
  to { opacity: 0; pointer-events: none; }
}

.landing-hero {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  align-items: center;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.hero-title {
  margin: 0;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.hero-title-main { color: var(--text); }
.hero-title-accent { color: var(--primary); }

.hero-desc {
  margin: 0;
  font-size: var(--text-lg);
  line-height: var(--text-lg--line-height);
  color: var(--muted);
}

.hero-panel {
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--radius-xl);
  background: var(--gradient-card-bg, var(--landing-panel-bg, var(--card-bg)));
  box-shadow: var(--gradient-card-shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: var(--fib-8);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}

.quick-card {
  display: flex;
  align-items: flex-start;
  gap: var(--fib-13);
  width: 100%;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--card-radius);
  cursor: pointer;
  font-family: inherit;
  color: var(--text);
  transition: border-color 0.2s, background 0.2s;
}

.quick-card:hover {
  border-color: var(--gradient-card-border-hover, var(--border));
  background: var(--hover);
}

.quick-card.primary {
  border-color: rgba(var(--primary-rgb), 0.35);
  background: rgba(var(--primary-rgb), 0.08);
}

.quick-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.quick-label {
  font-weight: 600;
}

.quick-card.primary .quick-label { color: var(--primary); }

.quick-hint {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--muted);
}

.shortcut-nav {
  display: grid;
  grid-template-columns: 1fr;
  border-top: 1px solid var(--border);
}

.shortcut-link {
  display: flex;
  align-items: center;
  gap: var(--fib-8);
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  background: var(--hover);
  cursor: pointer;
  font-family: inherit;
  color: var(--text);
  text-align: left;
  transition: border-color 0.2s, background 0.2s;
}

.shortcut-link:hover {
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.08);
}

.shortcut-label {
  font-size: var(--text-sm);
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.feature-card {
  background: var(--gradient-card-bg, var(--card-bg));
  border: 1px solid var(--gradient-card-border, var(--border));
  border-radius: var(--card-radius);
  box-shadow: var(--gradient-card-shadow);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  border-color: var(--gradient-card-border-hover, var(--primary));
  box-shadow: var(--gradient-card-shadow-hover, var(--gradient-card-shadow));
}

.feature-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 600;
}

.feature-desc {
  margin: 0;
  font-size: var(--text-base);
  color: var(--muted);
  line-height: var(--text-base--line-height);
}

.landing-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--muted);
  border-top: 1px solid var(--border);
}

.landing-footer .linux-uname {
  width: 100%;
  margin: 0 0 var(--fib-8);
  border: none;
  border-radius: var(--card-radius);
}

.landing-footer a {
  color: var(--primary);
  text-decoration: none;
}

.landing-footer a:hover { text-decoration: underline; }
</style>"""

if old_style not in text:
    raise SystemExit('PlatformLanding style block mismatch — manual merge needed')

text = text.replace(old_style, new_style, 1)
p.write_text(text, encoding='utf-8', newline='\n')
print('PlatformLanding.vue scoped layout stripped OK')
