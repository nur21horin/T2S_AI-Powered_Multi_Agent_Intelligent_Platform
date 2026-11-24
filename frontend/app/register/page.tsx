"use client";

import Link from "next/link";
import { useState } from "react";
import { ThemeToggle } from "../../components/ThemeProvider";
import FeatureScene from "../../components/FeatureScene";

export default function RegisterPage() {
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setMessage("Your passwords do not match. Please check them and try again.");
      return;
    }
    setMessage("Your profile is ready to get started. Account creation will be available when authentication is connected.");
  }

  return <main className="page-enter flex min-h-screen items-center justify-center bg-[#052f2c] px-5 py-12 text-white"><div className="w-full max-w-md">
    <div className="flex items-center justify-between"><Link href="/" className="text-xl font-bold"><span className="text-emerald-400">T2S</span> Platform</Link><ThemeToggle /></div>
    <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-8 shadow-2xl">
      <p className="text-sm font-medium text-emerald-300">START YOUR JOURNEY</p><h1 className="mt-2 text-3xl font-bold">Create an account</h1><p className="mt-3 text-sm text-gray-400">Build skills and discover your next opportunity.</p><FeatureScene scene="profile" className="auth-feature-scene mt-6" />
      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <label className="block text-sm text-gray-300">Full name<input required autoComplete="name" className="mt-2 w-full rounded-xl border border-white/10 bg-[#073b36] px-4 py-3 outline-none focus:border-emerald-400" placeholder="Your name" /></label>
        <label className="block text-sm text-gray-300">Email address<input required type="email" autoComplete="email" className="mt-2 w-full rounded-xl border border-white/10 bg-[#073b36] px-4 py-3 outline-none focus:border-emerald-400" placeholder="you@university.edu" /></label>
        <label className="block text-sm text-gray-300">I am a<select className="mt-2 w-full rounded-xl border border-white/10 bg-[#073b36] px-4 py-3 outline-none focus:border-emerald-400"><option>Student</option><option>Teacher</option><option>Alumni</option></select></label>
        <label className="block text-sm text-gray-300">Password<input required minLength={8} type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#073b36] px-4 py-3 outline-none focus:border-emerald-400" placeholder="At least 8 characters" /></label>
        <label className="block text-sm text-gray-300">Confirm password<input required minLength={8} type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#073b36] px-4 py-3 outline-none focus:border-emerald-400" placeholder="Enter your password again" /></label>
        <button className="w-full rounded-xl bg-emerald-500 px-4 py-3 font-semibold text-[#052f2c] transition hover:bg-emerald-400">Create account</button>
        {message && <p role="status" className="text-sm text-teal-300">{message}</p>}
      </form>
      <p className="mt-6 text-center text-sm text-gray-400">Already have an account? <Link href="/login" className="font-semibold text-emerald-300 hover:text-emerald-200">Log in</Link></p>
    </div>
  </div></main>;
}
