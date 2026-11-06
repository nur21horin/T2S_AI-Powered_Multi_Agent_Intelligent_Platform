
import Link from "next/link";

export default function TeacherDashboard() {
  const stats = [
    { label: "Active tasks", value: "08" },
    { label: "Students", value: "54" },
    { label: "Submissions to review", value: "11" },
  ];

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-medium text-cyan-300">
          TEACHER WORKSPACE
        </p>
        <h1 className="mt-2 text-3xl font-bold">Teaching overview</h1>
        <p className="mt-2 text-gray-400">
          Organize learning activities and support student development.
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
        <h2 className="text-xl font-semibold">Task overview</h2>
        <p className="mt-2 text-sm text-gray-400">
          Example teaching activities
        </p>

        <div className="mt-5 space-y-3">
          {[
            { title: "React fundamentals", count: 24 },
            { title: "Data analysis project", count: 18 },
            { title: "Research proposal", count: 12 },
          ].map((task) => (
            <div
              key={task.title}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/5 bg-[#0c1120] p-4"
            >
              <p className="font-medium">{task.title}</p>
              <span className="text-sm text-gray-400">
                {task.count} students
              </span>
            </div>
          ))}
        </div>
      </section>

      <Link
        href="/dashboard/rooms"
        className="block rounded-2xl border border-white/10 p-5 transition hover:border-cyan-400/50"
      >
        <h2 className="font-semibold">Technical rooms →</h2>
        <p className="mt-2 text-sm text-gray-400">
          Explore collaborative learning spaces.
        </p>
      </Link>
    </div>
  );
}