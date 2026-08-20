export type ExperienceLevel = "guided" | "advanced";

export const experienceLevelStorageKey = "myseo-experience-level";
export const experienceLevelEvent = "myseo:experience-level";

export function readExperienceLevel(): ExperienceLevel {
  if (typeof window === "undefined") return "guided";
  return localStorage.getItem(experienceLevelStorageKey) === "advanced" ? "advanced" : "guided";
}

export function cacheExperienceLevel(level: ExperienceLevel) {
  localStorage.setItem(experienceLevelStorageKey, level);
  window.dispatchEvent(new CustomEvent<ExperienceLevel>(experienceLevelEvent, { detail: level }));
}
