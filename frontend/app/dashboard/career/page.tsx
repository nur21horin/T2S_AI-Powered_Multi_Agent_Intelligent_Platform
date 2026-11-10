
"use client";

import { useState } from "react";

const careers = [
  {
    id: 1,
    title: "Frontend Developer",
    category: "Software Development",
    description: "Build websites and user interfaces using modern frontend technologies.",
    skills: ["HTML", "CSS", "JavaScript", "React"],
    match: 85,
    level: "Beginner friendly",
  },
  {
    id: 2,
    title: "Backend Developer",
    category: "Software Development",
    description: "Develop server-side applications, APIs and database systems.",
    skills: ["Java", "Spring Boot", "SQL", "REST API"],
    match: 72,
    level: "Intermediate",
  },
  {
    id: 3,
    title: "Data Scientist",
    category: "Data and AI",
    description: "Analyze data and build models to discover useful patterns.",
    skills: ["Python", "Statistics", "SQL", "Machine Learning"],
    match: 68,
    level: "Intermediate",
  },
  {
    id: 4,
    title: "AI / ML Engineer",
    category: "Data and AI",
    description: "Develop intelligent applications using machine learning techniques.",
    skills: ["Python", "Machine Learning", "Deep Learning", "TensorFlow"],
    match: 60,
    level: "Advanced",
  },
];

const opportunities = [
  {
    id: 1,
    title: "Frontend Development Intern",
    company: "Example Technology Company",
    type: "Internship",
    location: "Dhaka, Bangladesh",
    category: "Software Development",
  },
  {
    id: 2,
    title: "Junior Java Developer",
    company: "Example Software Company",
    type: "Entry-level",
    location: "Remote",
    category: "Software Development",
  },
  {
    id: 3,
    title: "Data Analyst Intern",
    company: "Example Data Solutions",
    type: "Internship",
    location: "Dhaka, Bangladesh",
    category: "Data and AI",
  },
];

export default function CareerPage() {
  const [activeTab, setActiveTab] = useState("Career Paths");
  const [savedCareers, setSavedCareers] = useState<number[]>([]);
  const [savedOpportunities, setSavedOpportunities] = useState<number[]>([]);

  function toggleCareer(id: number) {
    setSavedCareers((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id]
    );
  }

  function toggleOpportunity(id: number) {
    setSavedOpportunities((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id]
    );
  }

  return (
    <div className="space-y-8">
      {/* Heading */}
      <section>
        <p className="text-sm font-medium text-cyan-300">
          CAREER DEVELOPMENT
        </p>

        <h1 className="mt-2 text-3xl font-bold">Career Hub</h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-400">
          Explore career paths, understand required skills and discover
          opportunities that can support your professional development.
        </p>
      </section>

      {/* Statistics */}
      <section className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Career Paths", value: "04" },
          { label: "Opportunities", value: "03" },
          {
            label: "Saved Items",
            value: String(savedCareers.length + savedOpportunities.length).padStart(2, "0"),
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
          >
            <p className="text-sm text-gray-400">{stat.label}</p>
            <h2 className="mt-3 text-3xl font-bold">{stat.value}</h2>
          </div>
        ))}
      </section>

      {/* Tabs */}
      <section className="flex flex-wrap gap-2 border-b border-white/10 pb-4">
        {["Career Paths", "Opportunities", "My Saved Items"].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`rounded-xl px-4 py-2 text-sm transition ${
              activeTab === tab
                ? "bg-violet-500 text-white"
                : "border border-white/10 text-gray-400 hover:text-white"
            }`}
          >
            {tab}
          </button>
        ))}
      </section>

      {/* Career paths */}
      {activeTab === "Career Paths" && (
        <section className="space-y-5">
          <div>
            <h2 className="text-xl font-semibold">Explore Career Paths</h2>
            <p className="mt-1 text-sm text-gray-400">
              Discover different professional directions and their required skills.
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            {careers.map((career) => {
              const isSaved = savedCareers.includes(career.id);

              return (
                <article
                  key={career.id}
                  className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 hover:border-violet-400/40"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="rounded-full bg-violet-400/10 px-3 py-1 text-xs text-violet-300">
                      {career.category}
                    </span>
                    <span className="text-xs text-gray-400">
                      {career.level}
                    </span>
                  </div>

                  <h3 className="mt-5 text-xl font-semibold">
                    {career.title}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-gray-400">
                    {career.description}
                  </p>

                  <div className="mt-5">
                    <p className="text-xs font-semibold text-gray-400">
                      REQUIRED SKILLS
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {career.skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-lg border border-white/10 bg-[#0c1120] px-3 py-2 text-xs text-gray-300"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">
                        Example skill match
                      </span>
                      <span className="text-cyan-300">{career.match}%</span>
                    </div>

                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-cyan-400"
                        style={{ width: `${career.match}%` }}
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleCareer(career.id)}
                    className={`mt-5 w-full rounded-xl border px-4 py-3 text-sm transition ${
                      isSaved
                        ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                        : "border-white/10 bg-white/[0.04] text-gray-300 hover:border-violet-400/40"
                    }`}
                  >
                    {isSaved ? "Saved ✓" : "Save Career Path"}
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {/* Opportunities */}
      {activeTab === "Opportunities" && (
        <section className="space-y-5">
          <div>
            <h2 className="text-xl font-semibold">Career Opportunities</h2>
            <p className="mt-1 text-sm text-gray-400">
              Example internship and entry-level opportunity listings.
            </p>
          </div>

          {opportunities.map((opportunity) => {
            const isSaved = savedOpportunities.includes(opportunity.id);

            return (
              <article
                key={opportunity.id}
                className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
                    {opportunity.type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {opportunity.category}
                  </span>
                </div>

                <h3 className="mt-4 text-lg font-semibold">
                  {opportunity.title}
                </h3>

                <p className="mt-2 text-sm text-gray-400">
                  {opportunity.company}
                </p>

                <p className="mt-2 text-sm text-gray-500">
                  {opportunity.location}
                </p>

                <button
                  type="button"
                  onClick={() => toggleOpportunity(opportunity.id)}
                  className="mt-5 rounded-xl border border-white/10 px-4 py-3 text-sm text-gray-300 hover:border-cyan-400/40"
                >
                  {isSaved ? "Saved ✓" : "Save Opportunity"}
                </button>
              </article>
            );
          })}
        </section>
      )}

      {/* Saved items */}
      {activeTab === "My Saved Items" && (
        <section className="space-y-5">
          <h2 className="text-xl font-semibold">My Saved Items</h2>

          {savedCareers.length === 0 && savedOpportunities.length === 0 ? (
            <div className="rounded-2xl border border-white/10 p-8 text-center">
              <p className="font-medium">No saved items yet</p>
              <p className="mt-2 text-sm text-gray-400">
                Save a career path or opportunity to see it here.
              </p>
            </div>
          ) : (
            <>
              {careers
                .filter((career) => savedCareers.includes(career.id))
                .map((career) => (
                  <div
                    key={career.id}
                    className="rounded-xl border border-white/10 bg-white/[0.035] p-4"
                  >
                    <p className="font-medium">{career.title}</p>
                    <p className="mt-1 text-xs text-gray-400">Career Path</p>
                  </div>
                ))}

              {opportunities
                .filter((item) => savedOpportunities.includes(item.id))
                .map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-white/10 bg-white/[0.035] p-4"
                  >
                    <p className="font-medium">{item.title}</p>
                    <p className="mt-1 text-xs text-gray-400">Opportunity</p>
                  </div>
                ))}
            </>
          )}
        </section>
      )}
    </div>
  );
}
