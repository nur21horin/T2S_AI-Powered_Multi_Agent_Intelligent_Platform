
"use client";

import { useState } from "react";

const resources = [
  {
    id: 1,
    title: "Introduction to Artificial Intelligence",
    category: "Artificial Intelligence",
    type: "Course",
    level: "Beginner",
    description: "Understand AI fundamentals, intelligent agents and real-world applications.",
    author: "AI Learning Team",
  },
  {
    id: 2,
    title: "Complete Web Development Guide",
    category: "Web Development",
    type: "Tutorial",
    level: "Beginner",
    description: "Learn HTML, CSS, JavaScript and modern frontend development.",
    author: "Web Development Team",
  },
  {
    id: 3,
    title: "Machine Learning Fundamentals",
    category: "Machine Learning",
    type: "Book",
    level: "Intermediate",
    description: "Explore supervised learning, unsupervised learning and model evaluation.",
    author: "ML Learning Team",
  },
  {
    id: 4,
    title: "Data Structures and Algorithms",
    category: "Programming",
    type: "Course",
    level: "Intermediate",
    description: "Develop problem-solving skills through algorithms and data structures.",
    author: "Programming Team",
  },
  {
    id: 5,
    title: "Research Methodology",
    category: "Research",
    type: "Guide",
    level: "Intermediate",
    description: "Learn research questions, literature reviews and academic writing.",
    author: "Research Team",
  },
  {
    id: 6,
    title: "Cybersecurity Essentials",
    category: "Cybersecurity",
    type: "Tutorial",
    level: "Beginner",
    description: "Understand fundamental cybersecurity concepts and digital safety.",
    author: "Security Learning Team",
  },
];

const categories = [
  "All",
  "Artificial Intelligence",
  "Web Development",
  "Machine Learning",
  "Programming",
  "Research",
  "Cybersecurity",
];

export default function KnowledgePage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [saved, setSaved] = useState<number[]>([]);

  const filteredResources = resources.filter((resource) => {
    const matchesSearch =
      `${resource.title} ${resource.description} ${resource.category}`
        .toLowerCase()
        .includes(search.toLowerCase());

    const matchesCategory =
      category === "All" || resource.category === category;

    return matchesSearch && matchesCategory;
  });

  function toggleSave(id: number) {
    setSaved((previous) =>
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
          LEARNING RESOURCES
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          Knowledge Hub
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-400">
          Discover courses, tutorials, books and educational
          resources to strengthen your knowledge and technical skills.
        </p>
      </section>

      {/* Statistics */}
      <section className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Available Resources", value: resources.length },
          { label: "Categories", value: categories.length - 1 },
          { label: "Saved Resources", value: saved.length },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
          >
            <p className="text-sm text-gray-400">{stat.label}</p>
            <h2 className="mt-3 text-3xl font-bold">
              {String(stat.value).padStart(2, "0")}
            </h2>
          </div>
        ))}
      </section>

      {/* Search */}
      <section>
        <label
          htmlFor="resource-search"
          className="mb-3 block text-sm font-medium"
        >
          Search learning resources
        </label>

        <input
          id="resource-search"
          type="text"
          placeholder="Search courses, books, tutorials..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none placeholder:text-gray-500 focus:border-cyan-400"
        />
      </section>

      {/* Categories */}
      <section>
        <h2 className="mb-4 text-lg font-semibold">
          Browse Categories
        </h2>

        <div className="flex flex-wrap gap-2">
          {categories.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setCategory(item)}
              className={`rounded-full px-4 py-2 text-xs transition ${
                category === item
                  ? "bg-cyan-500 text-white"
                  : "border border-white/10 bg-white/[0.035] text-gray-400 hover:border-cyan-400/40 hover:text-white"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      {/* Resources */}
      <section>
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">
              Explore Resources
            </h2>
            <p className="mt-1 text-sm text-gray-400">
              Find useful materials for your learning journey.
            </p>
          </div>

          <span className="text-xs text-gray-400">
            {filteredResources.length} results
          </span>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filteredResources.map((resource) => {
            const isSaved = saved.includes(resource.id);

            return (
              <article
                key={resource.id}
                className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.035] p-5 transition hover:border-cyan-400/40"
              >
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
                    {resource.type}
                  </span>

                  <span className="text-xs text-gray-500">
                    {resource.level}
                  </span>
                </div>

                <h3 className="mt-5 text-lg font-semibold">
                  {resource.title}
                </h3>

                <p className="mt-3 min-h-16 text-sm leading-6 text-gray-400">
                  {resource.description}
                </p>

                <div className="mt-5 border-t border-white/10 pt-4">
                  <p className="text-xs text-gray-500">
                    CATEGORY
                  </p>

                  <p className="mt-1 text-sm text-cyan-300">
                    {resource.category}
                  </p>

                  <p className="mt-3 text-xs text-gray-500">
                    By {resource.author}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => toggleSave(resource.id)}
                  className={`mt-5 w-full rounded-xl border px-4 py-3 text-sm font-medium transition ${
                    isSaved
                      ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                      : "border-white/10 bg-white/[0.04] text-gray-300 hover:border-cyan-400/40"
                  }`}
                >
                  {isSaved ? "Saved ✓" : "Save Resource +"}
                </button>
              </article>
            );
          })}
        </div>

        {filteredResources.length === 0 && (
          <div className="rounded-2xl border border-white/10 p-10 text-center">
            <h3 className="font-semibold">No resources found</h3>
            <p className="mt-2 text-sm text-gray-400">
              Try another search or category.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
