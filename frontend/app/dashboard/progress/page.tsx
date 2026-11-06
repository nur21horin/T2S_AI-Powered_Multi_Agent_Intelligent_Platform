
"use client";

import { useState } from "react";

export default function ProgressPage() {
  const [selectedCourse, setSelectedCourse] = useState("All Courses");

  const courses = [
    {
      name: "React Development",
      category: "Frontend",
      progress: 80,
      completed: "8 of 10 lessons",
    },
    {
      name: "Python Programming",
      category: "Programming",
      progress: 60,
      completed: "6 of 10 lessons",
    },
    {
      name: "UI/UX Design",
      category: "Design",
      progress: 45,
      completed: "9 of 20 lessons",
    },
    {
      name: "Machine Learning",
      category: "AI & Data",
      progress: 30,
      completed: "3 of 10 lessons",
    },
  ];

  const filteredCourses =
    selectedCourse === "All Courses"
      ? courses
      : courses.filter((course) => course.category === selectedCourse);

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold text-cyan-300">
          LEARNING ANALYTICS
        </p>
        <h1 className="mt-2 text-3xl font-bold">Progress Tracking</h1>
        <p className="mt-2 text-gray-400">
          Monitor your learning journey and celebrate your achievements.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Overall Progress", value: "62%", color: "text-cyan-300" },
          { label: "Courses Enrolled", value: "04", color: "text-white" },
          { label: "Lessons Completed", value: "26", color: "text-green-400" },
          { label: "Learning Hours", value: "48h", color: "text-purple-400" },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-2xl border border-white/10 bg-white/[0.04] p-5"
          >
            <p className="text-sm text-gray-400">{item.label}</p>
            <h2 className={`mt-3 text-3xl font-bold ${item.color}`}>
              {item.value}
            </h2>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">Overall Learning Progress</h2>
        <p className="mt-2 text-sm text-gray-400">
          You have completed 62% of your learning goals.
        </p>

        <div className="mt-5 h-4 overflow-hidden rounded-full bg-gray-700">
          <div
            className="h-full rounded-full bg-cyan-400"
            style={{ width: "62%" }}
          />
        </div>
        <p className="mt-2 text-right text-sm text-cyan-300">62% completed</p>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-semibold">Course Progress</h2>
            <p className="mt-1 text-sm text-gray-400">
              Track your progress in each course.
            </p>
          </div>

          <select
            value={selectedCourse}
            onChange={(event) => setSelectedCourse(event.target.value)}
            className="rounded-lg border border-white/10 bg-[#0c1120] px-4 py-2 text-white"
          >
            <option>All Courses</option>
            <option>Frontend</option>
            <option>Programming</option>
            <option>Design</option>
            <option>AI & Data</option>
          </select>
        </div>

        <div className="mt-6 space-y-6">
          {filteredCourses.map((course) => (
            <div key={course.name}>
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <h3 className="font-semibold">{course.name}</h3>
                  <p className="mt-1 text-sm text-gray-400">
                    {course.category} · {course.completed}
                  </p>
                </div>
                <span className="font-semibold text-cyan-300">
                  {course.progress}%
                </span>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-700">
                <div
                  className="h-full rounded-full bg-cyan-400"
                  style={{ width: `${course.progress}%` }}
                />
              </div>
            </div>
          ))}

          {filteredCourses.length === 0 && (
            <p className="text-gray-400">No courses found.</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">Recent Achievement</h2>
        <div className="mt-4 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-yellow-400/10 text-3xl">
            🏆
          </div>
          <div>
            <h3 className="font-semibold">Learning Starter</h3>
            <p className="mt-1 text-sm text-gray-400">
              You completed your first learning milestone!
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
