"use client";

import { useSyncExternalStore } from "react";

const noSubscription = () => () => {};
const noMicrophoneOnServer = () => false;
const microphoneAvailable = () =>
  window.isSecureContext && Boolean(navigator.mediaDevices?.getUserMedia);
const reducedMotionOnServer = () => true;
const reducedMotion = () =>
  !("IntersectionObserver" in window) ||
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function subscribeMotion(listener) {
  const query = window.matchMedia("(prefers-reduced-motion: reduce)");
  query.addEventListener("change", listener);
  return () => query.removeEventListener("change", listener);
}

export function useMicrophoneAvailable() {
  return useSyncExternalStore(noSubscription, microphoneAvailable, noMicrophoneOnServer);
}

export function useReducedMotion() {
  return useSyncExternalStore(subscribeMotion, reducedMotion, reducedMotionOnServer);
}
