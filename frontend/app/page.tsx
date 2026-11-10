
"use client";

import { useState } from "react";

const skills = [
  { icon: "✳", title: "Artificial Intelligence", tag: "AI & ML", color: "violet", level: "High demand" },
  { icon: "⌘", title: "Full-Stack Development", tag: "ENGINEERING", color: "cyan", level: "Popular" },
  { icon: "◈", title: "Data Science", tag: "ANALYTICS", color: "lime", level: "Growing" },
  { icon: "✧", title: "Product & UI Design", tag: "CREATIVE", color: "pink", level: "In demand" },
];

const colorStyles: Record<string, string> = {
  violet: "bg-violet-400/10 text-violet-300 border-violet-400/20",
  cyan: "bg-cyan-400/10 text-cyan-300 border-cyan-400/20",
  lime: "bg-lime-400/10 text-lime-300 border-lime-400/20",
  pink: "bg-pink-400/10 text-pink-300 border-pink-400/20",
};

export default function Home() {
  const [search, setSearch] = useState("");

  const filteredSkills = skills.filter((skill) =>
    `${skill.title} ${skill.tag}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="min-h-screen overflow-hidden bg-[#080B14] text-white selection:bg-violet-500/40">
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-[#080B14]/85 backdrop-blur-2xl">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <a href="#home" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-400 to-indigo-600 text-lg font-black shadow-lg shadow-violet-500/20">
              T
            </span>
            <span className="text-xl font-bold tracking-tight">
              T2S<span className="text-violet-400">.</span>
            </span>
          </a>

          <div className="hidden items-center gap-8 text-sm text-slate-400 md:flex">
            <a className="text-white transition hover:text-violet-300" href="#home">Home</a>
            <a className="transition hover:text-white" href="#explore">Explore</a>
            <a className="transition hover:text-white" href="#process">How it works</a>
            <a className="transition hover:text-white" href="#about">About</a>
          </div>

          <a href="#explore" className="rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-violet-200">
            Get started <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      {/* Hero */}
      <section id="home" className="relative isolate">
        <div className="pointer-events-none absolute -top-24 left-1/2 -z-10 h-[440px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/[0.13] blur-[120px]" />
        <div className="pointer-events-none absolute right-0 top-72 -z-10 h-80 w-80 rounded-full bg-cyan-500/[0.08] blur-[100px]" />

        <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 pb-20 pt-20 sm:px-8 sm:pt-28 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pb-28 lg:pt-32">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/[0.07] px-4 py-2 text-xs font-medium tracking-wide text-violet-200">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
              INTELLIGENCE MEETS POTENTIAL
            </div>

            <h1 className="mt-8 max-w-3xl text-5xl font-semibold leading-[1.08] tracking-[-0.045em] sm:text-6xl lg:text-[76px]">
              Your talent.
              <br />
              <span className="bg-gradient-to-r from-violet-300 via-indigo-300 to-cyan-200 bg-clip-text text-transparent">
                Your next level.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-base leading-8 text-slate-400 sm:text-lg">
              Discover what you can become. Build meaningful skills, find
              your people, and turn your potential into real-world progress
              with an AI-powered talent ecosystem.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <a href="#explore" className="group inline-flex items-center gap-3 rounded-full bg-violet-500 px-6 py-3.5 font-semibold shadow-xl shadow-violet-600/20 transition hover:-translate-y-0.5 hover:bg-violet-400">
                Discover your path
                <span className="transition group-hover:translate-x-1" aria-hidden="true">→</span>
              </a>
              <a href="#process" className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3.5 font-medium text-slate-300 transition hover:border-white/35 hover:bg-white/[0.04]">
                <span aria-hidden="true">▷</span> See how it works
              </a>
            </div>

            <div className="mt-12 flex flex-wrap gap-x-8 gap-y-4 border-t border-white/10 pt-7">
              <div>
                <p className="text-lg font-semibold">AI-guided</p>
                <p className="mt-1 text-sm text-slate-500">Personalized discovery</p>
              </div>
              <div className="hidden h-10 w-px bg-white/10 sm:block" />
              <div>
                <p className="text-lg font-semibold">Skill-first</p>
                <p className="mt-1 text-sm text-slate-500">Learn by doing</p>
              </div>
              <div className="hidden h-10 w-px bg-white/10 sm:block" />
              <div>
                <p className="text-lg font-semibold">Future-ready</p>
                <p className="mt-1 text-sm text-slate-500">Grow with purpose</p>
              </div>
            </div>
          </div>

          {/* Interactive-style dashboard preview */}
          <div className="relative mx-auto w-full max-w-xl">
            <div className="absolute -inset-5 rounded-[36px] bg-gradient-to-br from-violet-500/20 via-transparent to-cyan-400/10 blur-2xl" />

            <div className="relative rounded-[28px] border border-white/[0.12] bg-[#101522]/90 p-5 shadow-2xl shadow-black/40 sm:p-7">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-400/20 to-indigo-500/10 text-xl text-violet-300">
                    ✳
                  </div>
                  <div>
                    <p className="font-semibold">Your potential</p>
                    <p className="mt-1 text-xs text-slate-500">A space to discover and grow</p>
                  </div>
                </div>
                <span className="rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-3 py-1.5 text-xs text-cyan-200">
                  AI powered
                </span>
              </div>

              <div className="mt-6 overflow-hidden rounded-2xl border border-violet-300/15 bg-gradient-to-br from-violet-500/[0.18] via-[#17172A] to-cyan-500/[0.08] p-6 sm:p-7">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold tracking-[0.18em] text-violet-200">YOUR NEXT CHAPTER</p>
                  <span className="text-xl text-violet-200">✦</span>
                </div>
                <h2 className="mt-5 text-2xl font-semibold tracking-tight sm:text-3xl">
                  Build skills that
                  <br /> open new doors.
                </h2>
                <p className="mt-3 max-w-xs text-sm leading-6 text-slate-400">
                  Connect your interests to learning paths, projects, and opportunities.
                </p>
                <a href="#explore" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-white hover:text-violet-200">
                  Explore possibilities <span aria-hidden="true">↗</span>
                </a>
                <div className="mt-7 flex h-20 items-end gap-2 overflow-hidden">
                  {[28, 42, 35, 58, 46, 72, 60, 88, 69, 100, 78, 92, 72, 110, 84, 98].map((height, index) => (
                    <div key={index} className="flex-1 rounded-t-md bg-gradient-to-t from-violet-500/20 to-cyan-300/80" style={{ height: `${height * 0.65}px`, opacity: 0.35 + index * 0.04 }} />
                  ))}
                </div>
                <p className="mt-2 text-right text-[10px] tracking-widest text-slate-500">PROGRESS IS A JOURNEY</p>
              </div>

              <div className="mt-7 flex items-center justify-between">
                <div>
                  <p className="text-xs tracking-widest text-slate-500">EXPLORE</p>
                  <h3 className="mt-1 font-semibold">In-demand skill areas</h3>
                </div>
                <a href="#explore" className="text-sm text-violet-300 hover:text-white">View all ↗</a>
              </div>

              <div className="mt-4 space-y-3">
                {skills.slice(0, 3).map((skill) => (
                  <div key={skill.title} className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 transition hover:border-violet-300/25 hover:bg-white/[0.05]">
                    <span className={`flex h-11 w-11 items-center justify-center rounded-xl border text-xl ${colorStyles[skill.color]}`}>
                      {skill.icon}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{skill.title}</p>
                      <p className="mt-1 text-xs text-slate-500">{skill.tag}</p>
                    </div>
                    <span className="text-slate-500" aria-hidden="true">↗</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="absolute -right-2 top-24 hidden rounded-2xl border border-white/10 bg-[#171C2A] px-4 py-3 shadow-xl sm:block lg:-right-8">
              <p className="text-xs text-slate-500">THE T2S APPROACH</p>
              <p className="mt-1 text-sm font-semibold text-cyan-200">Discover · Develop · Grow</p>
            </div>
          </div>
        </div>
      </section>

      {/* Skill explorer */}
      <section id="explore" className="border-t border-white/[0.07] bg-[#0B0F1A] py-20 sm:py-24">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="flex flex-col gap-7 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold tracking-[0.22em] text-violet-300">FIND YOUR DIRECTION</p>
              <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">
                Explore what&apos;s <span className="text-slate-500">possible.</span>
              </h2>
              <p className="mt-4 max-w-xl leading-7 text-slate-400">
                Start with an interest. Discover a skill. Build something meaningful.
              </p>
            </div>

            <div className="w-full md:max-w-sm">
              <label htmlFor="skill-search" className="mb-2 block text-xs font-medium text-slate-400">
                SEARCH SKILL AREAS
              </label>
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.035] px-4 transition focus-within:border-violet-400/60 focus-within:ring-2 focus-within:ring-violet-400/10">
                <span className="text-slate-500" aria-hidden="true">⌕</span>
                <input
                  id="skill-search"
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="AI, engineering, design..."
                  className="w-full bg-transparent py-3.5 text-sm text-white outline-none placeholder:text-slate-600"
                />
                <span className="text-xs text-slate-600">⌘K</span>
              </div>
            </div>
          </div>

          <div className="mt-11 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {filteredSkills.map((skill, index) => (
              <article key={skill.title} className="group relative overflow-hidden rounded-2xl border border-white/[0.09] bg-[#101522] p-6 transition duration-300 hover:-translate-y-1 hover:border-violet-300/30 hover:bg-[#141A2A]">
                <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-violet-500/[0.07] blur-3xl transition group-hover:bg-violet-400/15" />
                <div className="relative flex items-start justify-between">
                  <span className={`flex h-12 w-12 items-center justify-center rounded-xl border text-xl ${colorStyles[skill.color]}`}>
                    {skill.icon}
                  </span>
                  <span className="text-sm text-slate-600">0{index + 1}</span>
                </div>
                <p className="relative mt-7 text-[10px] font-semibold tracking-[0.18em] text-slate-500">{skill.tag}</p>
                <h3 className="relative mt-2 min-h-12 text-lg font-semibold">{skill.title}</h3>
                <p className="relative mt-3 text-sm leading-6 text-slate-400">
                  Develop practical skills and explore new opportunities in this field.
                </p>
                <div className="relative mt-6 flex items-center justify-between border-t border-white/[0.08] pt-4">
                  <span className="text-xs text-slate-500">{skill.level}</span>
                  <a href="#process" aria-label={`Learn about ${skill.title}`} className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 text-slate-300 transition group-hover:border-violet-300/40 group-hover:bg-violet-400/10 group-hover:text-white">↗</a>
                </div>
              </article>
            ))}
            {filteredSkills.length === 0 && (
              <p className="col-span-full rounded-2xl border border-white/10 p-10 text-center text-slate-400">
                No matching skills yet. Try another keyword.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Process */}
      <section id="process" className="relative border-t border-white/[0.07] py-20 sm:py-24">
        <div className="pointer-events-none absolute left-1/2 top-0 h-80 w-96 -translate-x-1/2 rounded-full bg-violet-600/[0.07] blur-[110px]" />
        <div className="relative mx-auto max-w-7xl px-5 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold tracking-[0.22em] text-cyan-300">A CLEARER PATH FORWARD</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">
              Small steps. <span className="text-slate-500">Big possibilities.</span>
            </h2>
            <p className="mt-5 leading-7 text-slate-400">
              A simple framework for turning your interests into meaningful progress.
            </p>
          </div>

          <div className="mt-14 grid gap-5 md:grid-cols-3">
            {[
              { number: "01", icon: "◎", title: "Discover", accent: "text-violet-300", text: "Understand your interests and explore skills that connect with your ambitions." },
              { number: "02", icon: "↗", title: "Develop", accent: "text-cyan-300", text: "Build practical experience through learning, projects, and collaboration." },
              { number: "03", icon: "✦", title: "Grow", accent: "text-lime-300", text: "Turn your developing capabilities into new directions and opportunities." },
            ].map((step) => (
              <article key={step.number} className="rounded-2xl border border-white/[0.09] bg-gradient-to-b from-white/[0.045] to-transparent p-7 sm:p-8">
                <div className="flex items-center justify-between">
                  <span className={`text-3xl ${step.accent}`}>{step.icon}</span>
                  <span className="font-mono text-sm text-slate-600">{step.number} / 03</span>
                </div>
                <h3 className="mt-8 text-xl font-semibold">{step.title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="about" className="px-5 pb-20 pt-6 sm:px-8 sm:pb-24">
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-3xl border border-violet-300/20 bg-[#111426] px-6 py-14 text-center sm:px-12 sm:py-20">
          <div className="pointer-events-none absolute left-1/2 top-0 h-64 w-96 -translate-x-1/2 rounded-full bg-violet-500/20 blur-[90px]" />
          <div className="relative">
            <span className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs text-violet-200">
              THE FUTURE STARTS WITH YOU
            </span>
            <h2 className="mx-auto mt-6 max-w-3xl text-3xl font-semibold tracking-tight sm:text-5xl">
              Potential is just the beginning.
              <span className="mt-2 block text-slate-500">Let&apos;s build what&apos;s next.</span>
            </h2>
            <p className="mx-auto mt-5 max-w-xl leading-7 text-slate-400">
              Discover skills, explore possibilities, and start creating your own path with T2S.
            </p>
            <a href="#explore" className="mt-8 inline-flex items-center gap-3 rounded-full bg-white px-7 py-3.5 font-semibold text-slate-950 transition hover:bg-violet-200">
              Explore T2S <span aria-hidden="true">→</span>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.08]">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <a href="#home" className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500 font-bold">T</span>
            <span className="font-semibold">T2S<span className="text-slate-500">. </span><span className="font-normal text-slate-500">Talent to Skill</span></span>
          </a>
          <p className="text-sm text-slate-500">Discover your potential. Build your future.</p>
          <a href="#home" className="text-sm text-slate-400 transition hover:text-white">Back to top ↑</a>
        </div>
      </footer>
    </main>
  );
}