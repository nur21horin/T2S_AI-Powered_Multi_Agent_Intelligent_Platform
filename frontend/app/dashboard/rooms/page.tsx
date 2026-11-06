
"use client";

import { useState } from "react";

const rooms = [
  {
    id: 1,
    name: "Artificial Intelligence",
    category: "AI & ML",
    description:
      "Explore artificial intelligence concepts, intelligent systems and practical AI applications.",
    teacher: "AI Faculty",
    members: 45,
    level: "Intermediate",
    color: "violet",
  },
  {
    id: 2,
    name: "Machine Learning",
    category: "AI & ML",
    description:
      "Learn machine learning algorithms, model development and real-world data applications.",
    teacher: "ML Faculty",
    members: 38,
    level: "Intermediate",
    color: "cyan",
  },
  {
    id: 3,
    name: "Web Development",
    category: "Development",
    description:
      "Build modern websites using HTML, CSS, JavaScript and modern frontend frameworks.",
    teacher: "Web Faculty",
    members: 62,
    level: "Beginner",
    color: "blue",
  },
  {
    id: 4,
    name: "Competitive Programming",
    category: "Programming",
    description:
      "Practice problem solving, data structures and algorithms through coding challenges.",
    teacher: "CP Faculty",
    members: 51,
    level: "Advanced",
    color: "orange",
  },
  {
    id: 5,
    name: "Data Science",
    category: "Data",
    description:
      "Explore data analysis, visualization, statistics and predictive modeling.",
    teacher: "Data Faculty",
    members: 29,
    level: "Beginner",
    color: "green",
  },
  {
    id: 6,
    name: "Cybersecurity",
    category: "Security",
    description:
      "Understand cybersecurity principles, network security and secure software practices.",
    teacher: "Security Faculty",
    members: 34,
    level: "Intermediate",
    color: "red",
  },
];

export default function RoomsPage() {
  const [search, setSearch] = useState("");
  const [requests, setRequests] = useState<number[]>([]);

  const filteredRooms = rooms.filter((room) =>
    `${room.name} ${room.category} ${room.description}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  function toggleRequest(id: number) {
    setRequests((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id]
    );
  }

  return (
    <div className="space-y-8">

      {/* Page heading */}
      <section>
        <p className="text-sm font-medium text-violet-300">
          LEARNING COMMUNITIES
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          Technical Rooms
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-400">
          Discover teacher-led technical communities, develop
          practical skills and collaborate with other students.
        </p>
      </section>

      {/* Statistics */}
      <section className="grid gap-4 sm:grid-cols-3">

        <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
          <p className="text-sm text-gray-400">Available Rooms</p>
          <h2 className="mt-3 text-3xl font-bold">
            {rooms.length.toString().padStart(2, "0")}
          </h2>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
          <p className="text-sm text-gray-400">Total Members</p>
          <h2 className="mt-3 text-3xl font-bold">
            {rooms.reduce((total, room) => total + room.members, 0)}
          </h2>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
          <p className="text-sm text-gray-400">My Requests</p>
          <h2 className="mt-3 text-3xl font-bold text-violet-300">
            {requests.length.toString().padStart(2, "0")}
          </h2>
        </div>

      </section>

      {/* Search */}
      <section>
        <label
          htmlFor="room-search"
          className="mb-3 block text-sm font-medium"
        >
          Find a technical room
        </label>

        <input
          id="room-search"
          type="text"
          placeholder="Search AI, Web Development, Data Science..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="w-full rounded-xl border border-white/10 bg-[#0c1120] px-4 py-3 text-sm text-white outline-none transition placeholder:text-gray-500 focus:border-violet-400"
        />
      </section>

      {/* Room cards */}
      <section>
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">
              Explore Communities
            </h2>

            <p className="mt-1 text-sm text-gray-400">
              Find a community that matches your interests.
            </p>
          </div>

          <span className="text-xs text-gray-400">
            {filteredRooms.length} rooms found
          </span>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

          {filteredRooms.map((room) => {

            const requested = requests.includes(room.id);

            return (
              <div
                key={room.id}
                className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.035] p-5 transition hover:border-violet-400/40"
              >

                <div className="flex items-center justify-between">

                  <span className="rounded-full bg-violet-400/10 px-3 py-1 text-xs text-violet-300">
                    {room.category}
                  </span>

                  <span className="text-xs text-gray-400">
                    {room.level}
                  </span>

                </div>

                <h3 className="mt-5 text-lg font-semibold">
                  {room.name}
                </h3>

                <p className="mt-3 min-h-16 text-sm leading-6 text-gray-400">
                  {room.description}
                </p>

                <div className="mt-5 space-y-2 border-t border-white/10 pt-4">

                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Instructor</span>
                    <span className="text-gray-300">
                      {room.teacher}
                    </span>
                  </div>

                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Members</span>
                    <span className="text-gray-300">
                      {room.members} students
                    </span>
                  </div>

                </div>

                <button
                  type="button"
                  onClick={() => toggleRequest(room.id)}
                  className={`mt-5 w-full rounded-xl px-4 py-3 text-sm font-medium transition ${
                    requested
                      ? "border border-green-400/30 bg-green-400/10 text-green-300"
                      : "bg-violet-500 text-white hover:bg-violet-600"
                  }`}
                >
                  {requested ? "Request Sent ✓" : "Request to Join →"}
                </button>

              </div>
            );
          })}

        </div>

        {filteredRooms.length === 0 && (
          <div className="rounded-2xl border border-white/10 p-10 text-center">
            <h3 className="font-semibold">No rooms found</h3>
            <p className="mt-2 text-sm text-gray-400">
              Try searching with another keyword.
            </p>
          </div>
        )}

      </section>

    </div>
  );
}
