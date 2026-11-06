
"use client";

import { useState } from "react";

export default function ProfilePage() {
  const [name, setName] = useState("Student Name");
  const [email, setEmail] = useState("student@example.com");
  const [university, setUniversity] = useState(
    "Daffodil International University"
  );
  const [department, setDepartment] = useState("Software Engineering");
  const [semester, setSemester] = useState("4th Semester");
  const [bio, setBio] = useState(
    "I am a Software Engineering student interested in programming, technology and research."
  );

  const [skills, setSkills] = useState([
    "Java",
    "HTML",
    "CSS",
    "JavaScript",
  ]);

  const [interests, setInterests] = useState([
    "Artificial Intelligence",
    "Web Development",
  ]);

  const [newSkill, setNewSkill] = useState("");
  const [newInterest, setNewInterest] = useState("");
  const [message, setMessage] = useState("");

  function addSkill() {
    const value = newSkill.trim();

    if (value && !skills.includes(value)) {
      setSkills((previous) => [...previous, value]);
      setNewSkill("");
    }
  }

  function removeSkill(skill: string) {
    setSkills((previous) =>
      previous.filter((item) => item !== skill)
    );
  }

  function addInterest() {
    const value = newInterest.trim();

    if (value && !interests.includes(value)) {
      setInterests((previous) => [...previous, value]);
      setNewInterest("");
    }
  }

  function removeInterest(interest: string) {
    setInterests((previous) =>
      previous.filter((item) => item !== interest)
    );
  }

  const completedFields = [
    name,
    email,
    university,
    department,
    semester,
    bio,
  ].filter((value) => value.trim() !== "").length;

  const profileProgress = Math.round(
    ((completedFields +
      (skills.length > 0 ? 1 : 0) +
      (interests.length > 0 ? 1 : 0)) /
      8) *
      100
  );

  function saveProfile() {
    setMessage("Profile changes saved in this session!");
  }

  return (
    <div className="space-y-8">

      {/* Page Heading */}
      <section>
        <p className="text-sm font-medium text-cyan-300">
          STUDENT ACCOUNT
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          My Profile
        </h1>

        <p className="mt-2 text-gray-400">
          Manage your personal information, technical skills and
          academic interests.
        </p>
      </section>

      {/* Profile Overview */}
      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center">

          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-violet-500/20 text-3xl font-bold text-violet-300">
            {name.trim().charAt(0).toUpperCase() || "S"}
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-semibold">
              {name || "Student Name"}
            </h2>

            <p className="mt-2 text-sm text-gray-400">
              {department} · {university}
            </p>

            <p className="mt-1 text-sm text-cyan-300">
              {semester}
            </p>
          </div>

          <div className="rounded-xl border border-violet-400/20 bg-violet-400/5 p-4">
            <p className="text-xs text-gray-400">
              PROFILE COMPLETION
            </p>

            <p className="mt-2 text-2xl font-bold text-violet-300">
              {profileProgress}%
            </p>
          </div>
        </div>

        <div className="mt-6 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-violet-400 transition-all"
            style={{ width: `${profileProgress}%` }}
          />
        </div>
      </section>

      {/* Personal Information */}
      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold">
            Personal Information
          </h2>

          <p className="mt-1 text-sm text-gray-400">
            Update your basic student information.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Full Name
            </label>

            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
              placeholder="Enter your name"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Email Address
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              University
            </label>

            <input
              value={university}
              onChange={(event) => setUniversity(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Department
            </label>

            <input
              value={department}
              onChange={(event) => setDepartment(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Current Semester
            </label>

            <input
              value={semester}
              onChange={(event) => setSemester(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
            />
          </div>

        </div>

        <div className="mt-5">
          <label className="mb-2 block text-sm text-gray-300">
            About Me
          </label>

          <textarea
            value={bio}
            onChange={(event) => setBio(event.target.value)}
            rows={4}
            className="w-full resize-y rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
            placeholder="Write something about yourself..."
          />
        </div>
      </section>

      {/* Technical Skills */}
      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">
          Technical Skills
        </h2>

        <p className="mt-1 text-sm text-gray-400">
          Add the technologies and programming languages you know.
        </p>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <input
            value={newSkill}
            onChange={(event) => setNewSkill(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addSkill();
              }
            }}
            placeholder="Example: Python"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
          />

          <button
            type="button"
            onClick={addSkill}
            className="rounded-xl bg-violet-500 px-5 py-3 text-sm font-medium text-white hover:bg-violet-600"
          >
            + Add Skill
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          {skills.map((skill) => (
            <span
              key={skill}
              className="flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-300"
            >
              {skill}

              <button
                type="button"
                onClick={() => removeSkill(skill)}
                aria-label={`Remove ${skill}`}
                className="text-gray-400 hover:text-red-400"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </section>

      {/* Research Interests */}
      <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-xl font-semibold">
          Research & Career Interests
        </h2>

        <p className="mt-1 text-sm text-gray-400">
          Add topics that interest you academically or professionally.
        </p>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <input
            value={newInterest}
            onChange={(event) => setNewInterest(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                addInterest();
              }
            }}
            placeholder="Example: Data Science"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400"
          />

          <button
            type="button"
            onClick={addInterest}
            className="rounded-xl bg-violet-500 px-5 py-3 text-sm font-medium text-white hover:bg-violet-600"
          >
            + Add Interest
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          {interests.map((interest) => (
            <span
              key={interest}
              className="flex items-center gap-2 rounded-xl border border-violet-400/20 bg-violet-400/10 px-4 py-2 text-sm text-violet-300"
            >
              {interest}

              <button
                type="button"
                onClick={() => removeInterest(interest)}
                aria-label={`Remove ${interest}`}
                className="text-gray-400 hover:text-red-400"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </section>

      {/* Save Button */}
      <section className="flex flex-col items-start gap-3">
        <button
          type="button"
          onClick={saveProfile}
          className="rounded-xl bg-cyan-500 px-8 py-3 font-semibold text-white transition hover:bg-cyan-600"
        >
          Save Changes
        </button>

        {message && (
          <p className="text-sm text-cyan-300" role="status">
            {message}
          </p>
        )}
      </section>

    </div>
  );
}
