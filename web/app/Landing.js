"use client";

import { useEffect, useState } from "react";
import CallWidget from "./CallWidget";
import Logo from "./Logo";
import { dict } from "./i18n";
import { Reveal, CountUp, spotlightMove } from "./fx";

const CTA_URL = "https://vexiumai.com"; // "book a setup call" link (change freely)

export default function Landing() {
  const [lang, setLang] = useState("en"); // default English
  const t = dict[lang];

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return (
    <div className="wrap">
      <nav className="nav">
        <a className="brand" href="#top" aria-label="Vexium AI">
          <Logo size={34} />
          <span className="word metal">VEXIUM&nbsp;AI</span>
        </a>
        <div className="nav-right">
          <div className="nav-links">
            <a href="#demo">{t.nav.demo}</a>
            <a href="#how">{t.nav.how}</a>
            <a href="#features">{t.nav.features}</a>
          </div>
          <div className="lang" role="group" aria-label="Language">
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
            <button className={lang === "es" ? "on" : ""} onClick={() => setLang("es")}>ES</button>
          </div>
          <a className="nav-cta" href="#demo">{t.cta.primary}</a>
        </div>
      </nav>

      <header className="hero" id="demo">
        <div className="hero-spot" aria-hidden="true" />
        <div className="hero-beams" aria-hidden="true"><i /><i /><i /></div>

        <div className="hero-copy">
          <Logo size={108} className="hero-logo" />
          <span className="badge"><span className="live" /> {t.hero.badge}</span>
          <h1>
            <span className="metal">{t.hero.titleA}</span>
            <span className="glow-blue">{t.hero.titleHi}</span>
            <span className="metal">{t.hero.titleB}</span>
          </h1>
          <p className="sub">{t.hero.sub}</p>
          <div className="hero-meta">
            {t.hero.meta.map(([k, v]) => (
              <div key={k}>
                <span className="k">{k}</span>
                <span className="v">{v}</span>
              </div>
            ))}
          </div>
        </div>

        <CallWidget t={t.call} demos={t.demos} />
      </header>

      <Reveal as="section" className="stats" aria-label="Key metrics">
        {t.stats.items.map((s, i) => (
          <div className="stat" key={i}>
            <div className="stat-v glow-blue">
              <CountUp to={s.to} decimals={s.decimals} prefix={s.prefix} suffix={s.suffix} />
            </div>
            <div className="stat-k">{s.label}</div>
          </div>
        ))}
      </Reveal>

      <div className="tech" aria-label={t.tech.label}>
        <span className="tech-label">{t.tech.label}</span>
        <ul className="sr-only">{t.tech.items.map((x, i) => (<li key={i}>{x}</li>))}</ul>
        <div className="marquee" aria-hidden="true">
          <div className="marquee-track">
            {[...t.tech.items, ...t.tech.items, ...t.tech.items].map((x, i) => (
              <span className="marquee-item" key={i}>{x}</span>
            ))}
          </div>
        </div>
      </div>

      <section className="section" id="how">
        <Reveal className="section-head">
          <span className="eyebrow">{t.nav.how}</span>
          <h2>{t.how.title}</h2>
          <p className="lead">{t.how.lead}</p>
        </Reveal>
        <Reveal className="steps stagger">
          <span className="steps-line" aria-hidden="true" />
          {t.how.steps.map((s, i) => (
            <div className="step" key={i}>
              <h4>{s.h}</h4>
              <p>{s.p}</p>
            </div>
          ))}
        </Reveal>
      </section>

      <section className="section" id="features">
        <Reveal className="section-head">
          <span className="eyebrow">{t.nav.features}</span>
          <h2>{t.features.title}</h2>
          <p className="lead">{t.features.lead}</p>
        </Reveal>
        <Reveal className="bento stagger">
          {t.features.cards.map((c, i) => (
            <div className="bento-card" key={i} onPointerMove={spotlightMove}>
              <div className="bento-glow" aria-hidden="true" />
              <div className="ic">{c.ic}</div>
              <h4>{c.h}</h4>
              <p>{c.p}</p>
            </div>
          ))}
        </Reveal>
      </section>

      <Reveal as="section" className="cta-band">
        <div className="cta-beam" aria-hidden="true" />
        <h2>{t.cta.title}</h2>
        <p>{t.cta.sub}</p>
        <div className="cta-actions">
          <a className="btn primary" href="#demo">{t.cta.primary}</a>
          <a className="btn" href={CTA_URL} target="_blank" rel="noopener noreferrer">{t.cta.secondary}</a>
        </div>
      </Reveal>

      <footer>
        <span>© {new Date().getFullYear()} Vexium AI — vexiumai.com</span>
        <span>{t.footer.tag}</span>
      </footer>
    </div>
  );
}
