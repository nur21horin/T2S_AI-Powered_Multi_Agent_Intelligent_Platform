
import Link from "next/link";

export default function AlumniDashboard() {
  const stats = [
    { label: "Mentoring sessions", value: "06" },
    { label: "Students supported", value: "18" },
    { label: "Career opportunities", value: "09" },
  ];

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-medium text-cyan-300">
          ALUMNI WORKSPACE
        </p>
        <h1 className="mt-2 text-3xl font-bold">Welcome to your alumni hub</h1>
        <p className="mt-2 text-gray-400">
          Share your experience, mentor students, and connect them with career
          opportunities.
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
        <h2 className="text-xl font-semibold">Ways to get involved</h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-white/5 bg-[#0c1120] p-5">
            <h3 className="font-semibold">Mentor students</h3>
            <p className="mt-2 text-sm text-gray-400">
              Share practical advice and help students develop their skills.
            </p>
          </div>

          <div className="rounded-xl border border-white/5 bg-[#0c1120] p-5">
            <h3 className="font-semibold">Share opportunities</h3>
            <p className="mt-2 text-sm text-gray-400">
              Help students discover internships, projects, and career paths.
            </p>
          </div>
        </div>
      </section>

      <Link
        href="/dashboard/career"
        className="block rounded-2xl border border-white/10 p-5 transition hover:border-cyan-400/50"
      >
        <h2 className="font-semibold">Career Hub →</h2>
        <p className="mt-2 text-sm text-gray-400">
          Explore career resources and opportunities.
        </p>
      </Link>
    </div>
  );
}