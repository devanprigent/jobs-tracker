import type { Application, ApplicationInput, AuthCredentials, JobListing, User } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (response.status === 204) {
    return null as T;
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error ?? "Request failed");
  }

  return data as T;
}

type AuthResponse = {
  user: User;
};

export function register(credentials: AuthCredentials) {
  return request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function login(credentials: AuthCredentials) {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function logout() {
  return request<null>("/api/auth/logout", {
    method: "POST",
  });
}

export function getCurrentUser() {
  return request<AuthResponse>("/api/auth/me");
}

export function getApplications({ favorite = false }: { favorite?: boolean } = {}) {
  const query = favorite ? "?favorite=true" : "";
  return request<Application[]>(`/api/applications${query}`);
}

export function getCompanies() {
  return request<string[]>("/api/companies");
}

export function createApplication(application: ApplicationInput) {
  return request<Application>("/api/applications", {
    method: "POST",
    body: JSON.stringify(application),
  });
}

export function updateApplication(application: ApplicationInput & { id: number }) {
  return request<Application>(`/api/applications/${application.id}`, {
    method: "PUT",
    body: JSON.stringify(application),
  });
}

export function deleteApplication(id: number) {
  return request<null>(`/api/applications/${id}`, {
    method: "DELETE",
  });
}

export function getJobs() {
  return request<JobListing[]>("/api/listings");
}

export async function scrapeJobs() {
  const result = await request<{ imported: number; output: string; listings: JobListing[] }>("/api/listings/scrape", {
    method: "POST",
  });
  return { ...result, jobs: result.listings };
}

export function trackJob(id: number) {
  return request<Application>(`/api/listings/${id}/track`, {
    method: "POST",
  });
}
