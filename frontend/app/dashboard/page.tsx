
const stats = [
  { label: "Skills in progress", value: "06", note: "Demo data" },
  { label: "Tasks completed", value: "12", note: "Across your workspace" },
  { label: "Learning progress", value: "68%", note: "Example progress" },
  { label: "Research projects", value: "02", note: "Sample projects" },
];

const activities = [
  {
    title: "Complete your profile",
    category: "PROFILE",
    status: "Recommended",
  },
  {
    title: "Explore a technical room",
    category: "COLLABORATION",
    status: "Ready to explore",
  },
  {
    title: "Review learning resources",
    category: "KNOWLEDGE HUB",
    status: "Recommended",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-medium text-violet-300">
          YOUR T2S WORKSPACE
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">
          Welcome to your dashboard.
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-400 md:text-base">
          Your space to develop skills, collaborate on projects, explore
          research, and prepare for your career.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
          >
            <p className="text-sm text-gray-400">{stat.label}</p>
            <p className="mt-4 text-3xl font-bold">{stat.value}</p>
            <p className="mt-2 text-xs text-violet-300">{stat.note}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Your next steps</h2>
              <p className="mt-1 text-sm text-gray-400">
                Start exploring the T2S platform.
              </p>
            </div>
            <span className="rounded-full bg-violet-400/10 px-3 py-1 text-xs text-violet-300">
              Getting started
            </span>
          </div>

          <div className="mt-6 space-y-3">
            {activities.map((activity, index) => (
              <div
                key={activity.title}
                className="flex items-center gap-4 rounded-xl border border-white/5 bg-[#0c1120] p-4"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-400/10 text-sm font-semibold text-violet-300">
                  0{index + 1}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{activity.title}</p>
                  <p className="mt-1 text-xs tracking-wide text-gray-500">
                    {activity.category}
                  </p>
                </div>
                <span className="hidden text-xs text-gray-400 sm:block">
                  {activity.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-violet-400/20 bg-gradient-to-br from-violet-500/15 to-cyan-500/5 p-6">
          <p className="text-sm font-medium text-violet-300">
            TALENT TO SKILL
          </p>
          <h2 className="mt-3 text-2xl font-bold">
            Make your next move count.
          </h2>
          <p className="mt-3 text-sm leading-6 text-gray-400">
            Use learning resources, practical tasks, research collaboration,
            and career tools to develop your capabilities.
          </p>
          <div className="mt-6 rounded-xl border border-white/10 bg-black/10 p-4">
            <p className="text-sm font-medium">Platform preview</p>
            <p className="mt-2 text-xs leading-5 text-gray-400">
              The numbers and activities on this page are placeholders.
              We will connect them to real user data later.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}