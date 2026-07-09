// Vexium mark — a chrome "V" chevron cradling a glowing blue orb. Pure SVG so it
// always renders crisply at any size (great for mobile/retina). If you later drop a
// real PNG at /vexium-logo.png, swap <Logo/> for an <img>.
"use client";

import { useId } from "react";

export default function Logo({ size = 40, className = "" }) {
  const uid = useId().replace(/:/g, ""); // SSR-safe, unique gradient/filter ids
  return (
    <svg
      className={className}
      width={size}
      height={size * 0.92}
      viewBox="0 0 200 184"
      fill="none"
      role="img"
      aria-label="Vexium"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={`${uid}-chrome`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="0.34" stopColor="#d7deec" />
          <stop offset="0.52" stopColor="#8b96ad" />
          <stop offset="0.66" stopColor="#eef2f8" />
          <stop offset="1" stopColor="#9aa4ba" />
        </linearGradient>
        <linearGradient id={`${uid}-edge`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.9" />
          <stop offset="1" stopColor="#5d6986" stopOpacity="0.5" />
        </linearGradient>
        <radialGradient id={`${uid}-orb`} cx="0.4" cy="0.36" r="0.7">
          <stop offset="0" stopColor="#f3eaff" />
          <stop offset="0.4" stopColor="#c084fc" />
          <stop offset="0.75" stopColor="#a855f7" />
          <stop offset="1" stopColor="#7c3aed" />
        </radialGradient>
        <filter id={`${uid}-glow`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Chrome V band */}
      <path
        d="M16 18 L52 18 L100 110 L148 18 L184 18 L116 158 Q100 184 84 158 Z"
        fill={`url(#${uid}-chrome)`}
        stroke={`url(#${uid}-edge)`}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* Inner bevel highlight */}
      <path
        d="M40 30 L100 142 L160 30"
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.55"
        strokeWidth="2.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Glowing blue orb in the notch */}
      <g filter={`url(#${uid}-glow)`}>
        <circle cx="100" cy="78" r="17" fill={`url(#${uid}-orb)`} />
        <circle cx="94" cy="72" r="5" fill="#ffffff" fillOpacity="0.85" />
      </g>
    </svg>
  );
}
