
"use client";

import { useState } from "react";

const researchProjects = [
  {
    id: 1,
    title: "AI-Based Student Performance Prediction",
    field: "Artificial Intelligence",
    status: "Looking for members",
    description:
      "Explore how machine learning can help identify student learning patterns and predict academic performance.",
    members: 2,
    level: "Intermediate",
  },
  {
    id: 2,
    title: "Smart Healthcare Monitoring System",
    field: "Machine Learning",
    status: "In progress",
    description:
      "Study the use of intelligent systems for monitoring health-related information.",
    members: 3,
    level: "Advanced",
  },
  {
    id: 3,
    title: "Cybersecurity Awareness Among Students",
    field: "Cybersecurity",
    status: "Looking for members",
    description:
      "Investigate student awareness of online security, privacy and common digital threats.",
    members: 1,
    level: "Beginner",
  },
  {
    id: 4,
    title: "Natural Language Processing for Bangla",
    field: "Natural Language Processing",
    status: "In progress",
    description:
      "Explore language-processing techniques and their applications for Bangla text.",
    members: 4,
    level: "Advanced",
  },
];

const papers = [
  {
    title: "Machine Learning in Education",
    field: "Artificial Intelligence",
    year: "2025",
    type: "Research Paper",
  },
  {
    title: "A Survey of Natural Language Processing",
    field: "Natural Language Processing",
    year: "2024",
    type: "Survey Paper",
  },
  {
    title: "An Overview of Modern Cybersecurity",
    field: "Cybersecurity",
    year: "2025",
    type: "Review Paper",
  },
];

const interests = [
  "Artificial Intelligence",
  "Machine Learning",
  "Web Development",
  "Cybersecurity",
  "Data Science",
  "Natural Language Processing",
];

export default function ResearchPage() {
  const [selectedInterests, setSelectedInterests] = useState<string[]>([
    "Artificial Intelligence",
  ]);

  const [joinedProjects, setJoinedProjects] = useState<number[]>([]);
  const [activeTab, setActiveTab] = useState("Projects");

  function toggleInterest(interest: string) {
    setSelectedInterests((previous) =>
      previous.includes(interest)
        ? previous.filter((item) => item !== interest)
        : [...previous, interest]
    );
  }

  function toggleProject(id: number) {
    setJoinedProjects((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id]
    );
  }

  return (
    <div className="space-y-8">
      {/* Page heading */}
      <section>
        <p className="text-sm font-medium text-cyan-300">
          RESEARCH AND INNOVATION
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          Research Hub
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-400">
          Discover research opportunities, explore academic topics,
          and connect with students who share your research interests.
        </p>
      </section>

      {/* Statistics */}
      <section className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Research Projects", value: "04" },
          { label: "Research Papers", value: "03" },
          {
            label: "My Research Interests",
            value: String(selectedInterests.length).padStart(2, "0"),
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
        {["Projects", "Research Papers", "My Interests"].map((tab) => (
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

      {/* Research projects */}
      {activeTab === "Projects" && (
        <section className="space-y-5">
          <div>
            <h2 className="text-xl font-semibold">
              Available Research Projects
            </h2>
            <p className="mt-1 text-sm text-gray-400">
              Explore projects and express your interest in joining.
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            {researchProjects.map((project) => {
              const isJoined = joinedProjects.includes(project.id);

              return (
                <article
                  key={project.id}
                  className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 transition hover:border-violet-400/40"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="rounded-full bg-violet-400/10 px-3 py-1 text-xs text-violet-300">
                      {project.field}
                    </span>

                    <span className="text-xs text-gray-400">
                      {project.status}
                    </span>
                  </div>

                  <h3 className="mt-5 text-lg font-semibold">
                    {project.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-gray-400">
                    {project.description}
                  </p>

                  <div className="mt-5 flex flex-wrap gap-4 border-t border-white/10 pt-4 text-xs text-gray-400">
                    <span>{project.members} members</span>
                    <span>{project.level} level</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleProject(project.id)}
                    className={`mt-5 w-full rounded-xl px-4 py-3 text-sm font-medium transition ${
                      isJoined
                        ? "border border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                        : "bg-violet-500 text-white hover:bg-violet-600"
                    }`}
                  >
                    {isJoined ? "Interest Submitted ✓" : "Express Interest"}
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {/* Research papers */}
      {activeTab === "Research Papers" && (
        <section className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold">Research Paper Library</h2>
            <p className="mt-1 text-sm text-gray-400">
              Browse example academic research materials.
            </p>
          </div>

          {papers.map((paper) => (
            <article
              key={paper.title}
              className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
                  {paper.type}
                </span>
                <span className="text-xs text-gray-500">{paper.year}</span>
              </div>

              <h3 className="mt-4 font-semibold">{paper.title}</h3>
              <p className="mt-2 text-sm text-gray-400">{paper.field}</p>
            </article>
          ))}
        </section>
      )}

      {/* Research interests */}
      {activeTab === "My Interests" && (
        <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-6">
          <h2 className="text-xl font-semibold">Select Research Interests</h2>

          <p className="mt-2 text-sm text-gray-400">
            Select the research fields you are interested in exploring.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            {interests.map((interest) => {
              const selected = selectedInterests.includes(interest);

              return (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`rounded-xl border px-4 py-3 text-sm transition ${
                    selected
                      ? "border-violet-400/50 bg-violet-400/10 text-violet-300"
                      : "border-white/10 bg-[#0c1120] text-gray-400 hover:text-white"
                  }`}
                >
                  {selected ? "✓ " : "+ "}
                  {interest}
                </button>
              );
            })}
          </div>

          <p className="mt-6 text-sm text-gray-400">
            Selected interests: {selectedInterests.length}
          </p>
        </section>
      )}
    </div>
  );
}
