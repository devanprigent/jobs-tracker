export const APPLICATION_STATES = [
  "Applied",
  "Interview",
  "Technical test",
  "Offer",
  "Rejected",
] as const;

export type ApplicationState = (typeof APPLICATION_STATES)[number];

export type Application = {
  id: number;
  position: string;
  company: string;
  country: string;
  city: string;
  state: ApplicationState;
  candidature_date: string;
  favorite: boolean;
  created_at?: string;
  updated_at?: string;
};

export type ApplicationInput = Omit<Application, "id" | "created_at" | "updated_at"> & {
  id?: number;
};

export type JobListing = {
  id: number;
  position: string;
  company: string;
  location: string | null;
  source_url: string | null;
  date_found: string | null;
  raw_payload?: unknown;
  created_at?: string;
};

export type Status = {
  loading: boolean;
  error: string;
};

export type User = {
  id: number;
  email: string;
};

export type AuthCredentials = {
  email: string;
  password: string;
};
