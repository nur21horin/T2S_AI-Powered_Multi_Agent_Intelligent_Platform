
import Link from "next/link";

export default function StudentDashboard() {
  const stats = [
    { label: "Enrolled courses", value: "04" },
    { label: "Tasks in progress", value: "06" },
    { label: "Completed tasks", value: "12" },
  ];

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-medium text-cyan-300">
          STUDENT WORKSPACE
        </p>
        <h1 className="mt-2 text-3xl font-bold">My learning dashboard</h1>
        <p className="mt-2 text-gray-400">
          Track your learning, build skills, and explore new opportunities.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-white/10 bg-white/[0.04] p-5"
          >
            <p className="text-sm text-gray-400">{stat.label}</p>
            <p className="mt-3 text-3xl font-bold">{stat.value}</p>
          </div>
        ))}
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">Continue learning</h2>
        <div className="mt-5 space-y-3">
          {[
            { title: "Web Development", progress: "65%" },
            { title: "Data Science", progress: "40%" },
            { title: "Research Skills", progress: "80%" },
          ].map((course) => (
            <div
              key={course.title}
              className="rounded-xl border border-white/5 bg-[#0c1120] p-4"
            >
              <div className="flex justify-between gap-3">
                <span className="font-medium">{course.title}</span>
                <span className="text-sm text-cyan-300">
                  {course.progress}
                </span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-cyan-400"
                  style={{ width: course.progress }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/dashboard/tasks"
          className="rounded-2xl border border-white/10 p-5 transition hover:border-cyan-400/50"
        >
          <h2 className="font-semibold">My tasks →</h2>
          <p className="mt-2 text-sm text-gray-400">
            View assignments and track your work.
          </p>
        </Link>

        <Link
          href="/dashboard/knowledge"
          className="rounded-2xl border border-white/10 p-5 transition hover:border-cyan-400/50"
        >
          <h2 className="font-semibold">Knowledge Hub →</h2>
          <p className="mt-2 text-sm text-gray-400">
            Explore learning resources.
          </p>
        </Link>
      </div>
    </div>
  );
}