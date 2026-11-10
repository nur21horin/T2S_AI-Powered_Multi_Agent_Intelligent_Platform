
import Link from "next/link";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: "▦" },
  { label: "My Profile", href: "/dashboard/profile", icon: "◎" },
  { label: "Technical Rooms", href: "/dashboard/rooms", icon: "⌘" },
  { label: "Tasks", href: "/dashboard/tasks", icon: "✓" },
  { label: "My Progress", href: "/dashboard/progress", icon: "↗" },
  { label: "Knowledge Hub", href: "/dashboard/knowledge", icon: "▤" },
  { label: "Research Hub", href: "/dashboard/research", icon: "⌕" },
  { label: "Career Hub", href: "/dashboard/career", icon: "◇" },
];

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen bg-[#080b14] text-white md:flex">
      <aside className="border-b border-white/10 bg-[#0c1120] p-5 md:fixed md:inset-y-0 md:left-0 md:w-64 md:overflow-y-auto md:border-b-0 md:border-r">
        <Link href="/" className="text-2xl font-bold">
          <span className="text-violet-400">T2S</span>
          <span className="ml-2 text-sm font-medium text-gray-400">
            Workspace
          </span>
        </Link>

        <p className="mb-3 mt-9 text-xs font-semibold uppercase tracking-widest text-gray-500">
          Workspace
        </p>

        <nav aria-label="Dashboard navigation" className="grid grid-cols-2 gap-2 md:grid-cols-1">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-gray-300 transition hover:bg-violet-500/10 hover:text-white"
            >
              <span className="text-lg text-violet-300">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="mt-8 rounded-xl border border-violet-400/20 bg-violet-400/5 p-4">
          <p className="text-sm font-semibold">Keep growing</p>
          <p className="mt-2 text-xs leading-5 text-gray-400">
            Build skills, collaborate, and track your progress.
          </p>
        </div>

        <Link
          href="/"
          className="mt-6 block text-sm text-gray-400 hover:text-white"
        >
          ← Back to homepage
        </Link>
      </aside>

      <div className="min-w-0 flex-1 md:ml-64">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-[#080b14]/90 px-5 py-4 backdrop-blur md:px-8">
          <div>
            <p className="text-xs text-gray-500">T2S PLATFORM</p>
            <p className="mt-1 text-sm font-medium">Your workspace</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-gray-400 sm:block">
              Demo account
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-500/20 font-semibold text-violet-200">
              T
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl p-5 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}