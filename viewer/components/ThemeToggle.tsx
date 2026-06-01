"use client";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      className="theme-pill relative flex items-center w-[44px] h-[24px] rounded-full flex-shrink-0"
    >
      {/* Track icons */}
      <span className="absolute left-[5px] flex items-center justify-center w-[14px] h-[14px] pointer-events-none">
        <Sun size={10} className={isDark ? "text-fg-5" : "text-amber-500"} />
      </span>
      <span className="absolute right-[5px] flex items-center justify-center w-[14px] h-[14px] pointer-events-none">
        <Moon size={10} className={isDark ? "text-accent" : "text-fg-5"} />
      </span>

      {/* Sliding knob — background controlled by CSS (.theme-knob / .dark .theme-knob) */}
      <span
        className="theme-knob absolute top-[3px] left-[3px] w-[18px] h-[18px] rounded-full shadow-sm"
        style={{
          transform: isDark ? "translateX(20px)" : "translateX(0px)",
        }}
      />
    </button>
  );
}
