"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ThemeToggle } from "../components/ThemeProvider";
import NightLandscape from "../components/NightLandscape";

const slides = [
  { eyebrow: "YOUR NEXT CHAPTER", title: "Discover your path.", copy: "Find the skills that fit your curiosity. Build a future that feels like your own.", action: "Explore pathways" },
  { eyebrow: "LEARN TOGETHER", title: "Grow with your people.", copy: "Join technical rooms, share ideas, and make progress alongside a community.", action: "Meet your community" },
  { eyebrow: "MAKE IT REAL", title: "Turn ideas into impact.", copy: "Shape your skills through projects, research, and opportunities that matter.", action: "Find opportunities" },
];

const features = [
  { icon: "⌘", tag: "LEARN", title: "Technical Rooms", detail: "Find a friendly community, learn from mentors, and build practical skills together.", href: "/dashboard/rooms" },
  { icon: "↗", tag: "GROW", title: "Your Progress", detail: "Turn steady effort into visible progress with learning goals and milestones.", href: "/dashboard/progress" },
  { icon: "✦", tag: "CONNECT", title: "Research & Career", detail: "Explore projects, career paths, and opportunities that match your interests.", href: "/dashboard/research" },
];

export default function Home() {
  const [slide, setSlide] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [search, setSearch] = useState("");
  const activeSlide = slides[slide];

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setSlide((current) => (current + 1) % slides.length), 6500);
    return () => window.clearInterval(timer);
  }, [playing]);

  function changeSlide(direction: number) {
    setSlide((current) => (current + direction + slides.length) % slides.length);
  }

  const matchedFeatures = features.filter((feature) =>
    `${feature.title} ${feature.tag} ${feature.detail}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="night-home page-enter">
      <section className="night-hero" id="home">
        <NightLandscape />
        <header className="night-nav">
          <Link href="/" className="night-brand"><span className="brand-orb"/>T2S<span className="brand-company">YOUR TALENT, YOUR FUTURE</span></Link>
          <nav aria-label="Main navigation" className="night-nav-links">
            <a href="#home">Home</a><a href="#features">Services <span className="nav-caret">▾</span></a><a href="#about">About</a><a href="#contact">Contact</a>
          </nav>
          <div className="night-nav-actions"><ThemeToggle/><Link href="/login" className="night-signin">Sign in</Link><Link href="/register" className="night-register">Create account</Link></div>
        </header>

        <div className="night-copy" aria-live="polite">
          <p className="night-eyebrow">{activeSlide.eyebrow}</p>
          <h1 key={activeSlide.title}>{activeSlide.title}</h1>
          <p className="night-description">{activeSlide.copy}</p>
          <a href="#features" className="night-learn">{activeSlide.action}<span aria-hidden="true">→</span></a>
        </div>

        <button type="button" className="night-next" onClick={() => changeSlide(1)} aria-label="Next feature">›</button>
        <div className="night-carousel-controls">
          <button type="button" onClick={() => changeSlide(-1)} aria-label="Previous feature">‹</button>
          <button type="button" className="night-play" onClick={() => setPlaying((value) => !value)} aria-label={playing ? "Pause slideshow" : "Play slideshow"}>{playing ? "Ⅱ" : "▶"}</button>
          <div className="night-dots" aria-label={`Slide ${slide + 1} of ${slides.length}`}>{slides.map((item, index) => <button key={item.title} type="button" onClick={() => setSlide(index)} aria-label={`Show slide ${index + 1}`} aria-current={slide === index} />)}</div>
        </div>
        <a className="night-contact" href="mailto:hello@t2s.example" aria-label="Contact T2S"><span>☎</span><small>LET&apos;S TALK</small></a>
        <a href="#features" className="night-scroll" aria-label="Scroll to explore">↓</a>
      </section>

      <section id="features" className="night-content-section">
        <div className="night-section-heading"><div><p className="night-kicker">FIND YOUR NEXT TRAIL</p><h2>Make room for what&apos;s possible.</h2><p>Explore a space built for learning, collaboration, and meaningful progress.</p></div>
          <label className="night-search"><span aria-hidden="true">⌕</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search ways to grow" aria-label="Search features"/></label>
        </div>
        <div className="night-feature-grid">{matchedFeatures.map((feature) => <Link key={feature.title} href={feature.href} className="night-feature-card"><span className="night-feature-icon">{feature.icon}</span><span className="night-feature-tag">{feature.tag}</span><h3>{feature.title}</h3><p>{feature.detail}</p><span className="night-feature-link">Explore feature <span aria-hidden="true">↗</span></span></Link>)}
          {matchedFeatures.length === 0 && <p className="night-empty">No features match “{search}”. Try another search.</p>}
        </div>
      </section>

      <section id="about" className="night-about"><div><p className="night-kicker">THE T2S JOURNEY</p><h2>Discover. Develop. Grow.</h2><p>Start with a spark of curiosity. Find a community, keep learning, and build toward a future you can see.</p></div><Link href="/register" className="night-learn">Start your journey <span aria-hidden="true">→</span></Link></section>
      <footer id="contact" className="night-footer"><Link href="/" className="night-brand"><span className="brand-orb"/>T2S</Link><p>Talent to Skill · Built for the journey ahead.</p><a href="mailto:hello@t2s.example">Contact the T2S team</a></footer>
    </main>
  );
}
