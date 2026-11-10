
"use client";

import { useState } from "react";

export default function TasksPage() {
  const [status, setStatus] = useState("Pending");

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm text-cyan-300">LEARNING MANAGEMENT</p>
        <h1 className="mt-2 text-3xl font-bold">Tasks & Assignments</h1>
        <p className="mt-2 text-gray-400">
          Manage your assignments and track your learning progress.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <p className="text-sm text-gray-400">Total Tasks</p>
          <h2 className="mt-3 text-3xl font-bold">04</h2>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <p className="text-sm text-gray-400">In Progress</p>
          <h2 className="mt-3 text-3xl font-bold">02</h2>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <p className="text-sm text-gray-400">Completed</p>
          <h2 className="mt-3 text-3xl font-bold">02</h2>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">My Assignments</h2>

        <div className="mt-5 space-y-4">
          <div className="rounded-xl border border-white/10 p-4">
            <h3 className="font-semibold">Build a React Portfolio</h3>
            <p className="mt-2 text-sm text-gray-400">
              Create a responsive portfolio using React.
            </p>
            <p className="mt-2 text-xs text-gray-500">
              Deadline: November 12, 2026
            </p>

            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="mt-4 rounded-lg border border-white/10 bg-[#0c1120] px-4 py-2 text-white"
            >
              <option>Pending</option>
              <option>In Progress</option>
              <option>Completed</option>
            </select>

            <p className="mt-3 text-sm text-cyan-300">
              Current status: {status}
            </p>
          </div>

          <div className="rounded-xl border border-white/10 p-4">
            <h3 className="font-semibold">Python Data Analysis</h3>
            <p className="mt-2 text-sm text-gray-400">
              Analyze a dataset and present your findings.
            </p>
            <p className="mt-2 text-xs text-gray-500">
              Deadline: November 15, 2026
            </p>
            <span className="mt-3 inline-block text-sm text-yellow-400">
              Pending
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
