import { useEffect, useState } from "react";
export function ThemeToggle() {
  const [theme, setTheme] = useState(
    () =>
      localStorage.getItem("defect-lens-theme") ??
      (window.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"),
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  return (
    <button
      type="button"
      className="secondary"
      aria-label="Toggle theme"
      onClick={() => {
        const next = theme === "dark" ? "light" : "dark";
        localStorage.setItem("defect-lens-theme", next);
        setTheme(next);
      }}
    >
      {theme === "dark" ? "Light theme" : "Dark theme"}
    </button>
  );
}
