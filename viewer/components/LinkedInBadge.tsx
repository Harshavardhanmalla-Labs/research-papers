"use client";
import { useEffect, useRef } from "react";

/**
 * Official LinkedIn profile badge. LinkedIn's profile.js scans the document for
 * `.LI-profile-badge` divs and replaces them with an iframe. In a client-routed
 * app we (re)inject the script on mount so the badge renders even after
 * navigation. The iframe is theme-locked (LinkedIn only offers light/dark), so
 * we wrap it in an on-brand card that matches the surrounding design.
 */
export default function LinkedInBadge() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const s = document.createElement("script");
    s.src = "https://platform.linkedin.com/badges/js/profile.js";
    s.async = true;
    s.defer = true;
    s.type = "text/javascript";
    document.body.appendChild(s);
    return () => { s.remove(); };
  }, []);

  return (
    <div ref={ref} className="li-badge-card">
      <div
        className="badge-base LI-profile-badge"
        data-locale="en_US"
        data-size="medium"
        data-theme="dark"
        data-type="VERTICAL"
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
