"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Theme = "night" | "light";
const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({
  theme: "night",
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("night");

  useEffect(() => {
    const saved = window.localStorage.getItem("t2s-theme");
    const initial: Theme = saved === "light" ? "light" : "night";
    setTheme(initial);
    document.documentElement.dataset.theme = initial;
  }, []);

  function toggleTheme() {
    setTheme((current) => {
      const next = current === "night" ? "light" : "night";
      document.documentElement.dataset.theme = next;
      window.localStorage.setItem("t2s-theme", next);
      return next;
    });
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useContext(ThemeContext);
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "night" ? "light" : "night"} mode`}
      title={`Switch to ${theme === "night" ? "light" : "night"} mode`}
      className={`theme-toggle ${className}`}
    >
      <span aria-hidden="true">{theme === "night" ? "N" : "L"}</span>
      <span>{theme === "night" ? "Light mode" : "Night mode"}</span>
    </button>
  );
}
