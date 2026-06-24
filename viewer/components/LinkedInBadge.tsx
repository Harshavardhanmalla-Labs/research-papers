"use client";
import { useEffect } from "react";
import { useTheme } from "./ThemeProvider";

/**
 * Official LinkedIn profile badge, theme-aware. LinkedIn's profile.js scans the
 * document for `.LI-profile-badge` divs and replaces each with an iframe whose
 * style is fixed at scan time by `data-theme`. To follow the app's light/dark
 * toggle we key the badge div by theme (so React remounts a fresh, unprocessed
 * div) and re-inject profile.js on every theme change so it re-scans.
 */
export default function LinkedInBadge() {
  const { theme } = useTheme();

  useEffect(() => {
    const s = document.createElement("script");
    s.src = "https://platform.linkedin.com/badges/js/profile.js";
    s.async = true;
    s.defer = true;
    s.type = "text/javascript";
    document.body.appendChild(s);
    return () => { s.remove(); };
  }, [theme]); // re-scan when the theme flips

  return (
    <div className="li-badge-card" key={theme}>
      <div
        className="badge-base LI-profile-badge"
        data-locale="en_US"
        data-size="large"
        data-theme={theme === "dark" ? "dark" : "light"}
        data-type="HORIZONTAL"
        data-vanity="harshavardhanmalla"
        data-version="v1"
      >
        <a
          className="badge-base__link LI-simple-link"
          href="https://www.linkedin.com/in/harshavardhanmalla?trk=profile-badge"
          target="_blank"
          rel="noreferrer"
        >
          Harshavardhan Malla
        </a>
      </div>
    </div>
  );
}
