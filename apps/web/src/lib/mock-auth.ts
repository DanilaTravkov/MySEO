export const mockUserStorageKey = "myseo-mock-user";
export const mockAuthEvent = "myseo:mock-auth";

export type MockUser = {
  name: string;
  email: string;
  company: string;
  role: string;
  createdAt: string;
  experienceLevel?: "guided" | "advanced";
};

export const defaultMockUser: MockUser = {
  name: "John Doe",
  email: "test@exmaple.com",
  company: "",
  role: "",
  createdAt: new Date().toISOString(),
  experienceLevel: "guided",
};

export function readMockUser(): MockUser | null {
  try {
    const value = localStorage.getItem(mockUserStorageKey);
    if (!value) return defaultMockUser;
    const user = JSON.parse(value) as Partial<MockUser>;
    if (typeof user.name !== "string" || typeof user.email !== "string") return defaultMockUser;
    return {
      name: user.name,
      email: user.email,
      company: typeof user.company === "string" ? user.company : "",
      role: typeof user.role === "string" ? user.role : "",
      createdAt: typeof user.createdAt === "string" ? user.createdAt : new Date().toISOString(),
      experienceLevel: user.experienceLevel === "advanced" ? "advanced" : "guided",
    };
  } catch {
    return defaultMockUser;
  }
}

export function saveMockUser(user: MockUser) {
  const normalizedUser: MockUser = {
    ...user,
    name: user.name.trim() || "John Doe",
    email: user.email.trim().toLowerCase() || "test@exmaple.com",
    company: user.company ?? "",
    role: user.role ?? "",
    createdAt: user.createdAt || new Date().toISOString(),
    experienceLevel: user.experienceLevel === "advanced" ? "advanced" : "guided",
  };

  localStorage.setItem(mockUserStorageKey, JSON.stringify(normalizedUser));
  window.dispatchEvent(new Event(mockAuthEvent));
}

export function clearMockUser() {
  localStorage.removeItem(mockUserStorageKey);
  window.dispatchEvent(new Event(mockAuthEvent));
}

export function userInitials(name: string) {
  const initials = name.trim().split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
  return initials || "MY";
}

export function nameFromEmail(email: string) {
  const normalizedEmail = email.trim().toLowerCase();
  if (normalizedEmail === "test@exmaple.com") return "John Doe";

  const localPart = normalizedEmail.split("@")[0] ?? "MySEO user";
  return localPart.split(/[._-]+/).filter(Boolean).map((part) => `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`).join(" ") || "MySEO user";
}
