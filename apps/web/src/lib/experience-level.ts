import { readMockUser, saveMockUser } from "@/lib/mock-auth";

export type ExperienceLevel = "guided" | "advanced";

export const experienceLevelStorageKey = "myseo-experience-level";
export const experienceLevelEvent = "myseo:experience-level";

export function readExperienceLevel(): ExperienceLevel {
  if (typeof window === "undefined") return "guided";
  const user = readMockUser();
  if (user) return user.experienceLevel === "advanced" ? "advanced" : "guided";
  return localStorage.getItem(experienceLevelStorageKey) === "advanced" ? "advanced" : "guided";
}

export function saveExperienceLevel(level: ExperienceLevel) {
  const user = readMockUser();
  if (user) saveMockUser({ ...user, experienceLevel: level });
  else localStorage.setItem(experienceLevelStorageKey, level);
  window.dispatchEvent(new CustomEvent<ExperienceLevel>(experienceLevelEvent, { detail: level }));
}
