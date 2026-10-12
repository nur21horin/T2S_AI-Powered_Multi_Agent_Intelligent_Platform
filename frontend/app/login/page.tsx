
"use client";

import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("Demo only: backend authentication is not connected yet.");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#080b14] px-5 py-12 text-white">
      <div className="w-full max-w-md">
        <Link href="/" className="text-xl font-bold">
          <span className="text-violet-400">T2S</span> Platform
        </Link>

        <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-8 shadow-2xl">
          <p className="text-sm font-medium text-violet-300">WELCOME BACK</p>
          <h1 className="mt-2 text-3xl font-bold">Log in to T2S</h1>
          <p className="mt-3 text-sm text-gray-400">
            Continue your journey from talent to skill.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="mb-2 block text-sm text-gray-300">
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 outline-none focus:border-violet-400"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-sm text-gray-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 outline-none focus:border-violet-400"
              />
            </div>

            <button
              type="submit"
              className="w-full rounded-xl bg-violet-500 px-4 py-3 font-semibold transition hover:bg-violet-400"
            >
              Log in
            </button>

            {message && (
              <p role="status" className="text-sm text-cyan-300">
                {message}
              </p>
            )}
          </form>

          <p className="mt-6 text-center text-sm text-gray-400">
            New to T2S?{" "}
            <Link
              href="/register"
              className="font-semibold text-violet-300 hover:text-violet-200"
            >
              Create an account
            </Link>
          </p>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          AI-powered learning, built around you.
        </p>
      </div>
    </main>
  );
}