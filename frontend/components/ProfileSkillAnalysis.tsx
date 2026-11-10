"use client";

import { useState } from "react";

export default function ProfileSkillAnalysis() {
  const [profile, setProfile] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeProfile = async () => {
    if (!profile.trim()) return;

    setLoading(true);
    setError("");
    setResult("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/agents/profile-skill",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            profile: profile,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult(data.result);

    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">

      <div>
        <h1 className="text-2xl font-bold">
          AI Profile & Skill Analysis
        </h1>

        <p className="text-gray-500">
          Let T2S analyze your academic and technical profile.
        </p>
      </div>

      <textarea
        value={profile}
        onChange={(e) => setProfile(e.target.value)}
        placeholder="Enter your academic profile, skills and career goals..."
        className="min-h-52 w-full rounded-xl border p-4"
      />

      <button
        onClick={analyzeProfile}
        disabled={loading || !profile.trim()}
        className="rounded-xl bg-blue-600 px-6 py-3 text-white disabled:opacity-50"
      >
        {loading ? "Analyzing Profile..." : "Analyze My Profile"}
      </button>

      {error && (
        <div className="rounded-xl bg-red-100 p-4 text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <p className="animate-pulse text-blue-600">
          Profile Agent is analyzing your skills...
        </p>
      )}

      {result && (
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-bold">
            Profile Analysis Result
          </h2>

          <pre className="whitespace-pre-wrap font-sans leading-7 text-gray-800">
            {result}
          </pre>
        </div>
      )}

    </div>
  );
}