"use client";

// Small, dependency-free landing FX primitives.
//  - Reveal:   reveals children once they scroll into view (IntersectionObserver,
//              disconnects after firing). CSS does the transition via `.reveal`/`.in`.
//  - CountUp:  rAF count-up that starts when scrolled into view; snaps under
//              prefers-reduced-motion.
//  - spotlightMove: pointer handler that writes --mx/--my on the hovered element
//              (no React state -> no re-render) for the cursor-follow glow.

import { useEffect, useRef, useState } from "react";

const prefersReduced = () =>
  typeof window !== "undefined" &&
  window.matchMedia &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function Reveal({ as: Tag = "div", className = "", delay, children, ...rest }) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (prefersReduced() || !("IntersectionObserver" in window)) { setShown(true); return; }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) { setShown(true); io.disconnect(); }
      },
      { threshold: 0.16, rootMargin: "0px 0px -8% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const style = delay != null ? { transitionDelay: `${delay}ms` } : undefined;
  return (
    <Tag ref={ref} className={`reveal ${shown ? "in" : ""} ${className}`.trim()} style={style} {...rest}>
      {children}
    </Tag>
  );
}

export function CountUp({ to, decimals = 0, prefix = "", suffix = "" }) {
  const ref = useRef(null);
  const [val, setVal] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (prefersReduced() || !("IntersectionObserver" in window)) { setVal(to); return; }
    let raf = 0;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        io.disconnect();
        const dur = 1100;
        const t0 = performance.now();
        const step = (t) => {
          const p = Math.min(1, (t - t0) / dur);
          const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
          setVal(to * eased);
          if (p < 1) raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
      },
      { threshold: 0.5 }
    );
    io.observe(el);
    return () => { io.disconnect(); if (raf) cancelAnimationFrame(raf); };
  }, [to]);

  return (
    <span ref={ref}>
      {prefix}
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
}

// Cursor-follow spotlight: write the local cursor position as CSS vars on the
// element itself (no React state). Attach as onPointerMove on a card/grid.
export function spotlightMove(e) {
  const el = e.currentTarget;
  const r = el.getBoundingClientRect();
  el.style.setProperty("--mx", `${e.clientX - r.left}px`);
  el.style.setProperty("--my", `${e.clientY - r.top}px`);
}
