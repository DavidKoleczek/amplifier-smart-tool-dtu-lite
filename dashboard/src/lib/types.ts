// Mirrors the result classes in src/dtu_lite/schemas.py; the API returns them unchanged.

export type UniverseState = "starting" | "running" | "degraded" | "stopped";
export type Health = "starting" | "healthy" | "unhealthy";

export type Service = {
  name: string;
  state: string;
  health: Health | null;
  image: string;
};

export type Url = {
  url: string;
  port: number;
  path: string;
  label: string | null;
};

export type Universe = {
  id: string;
  name: string;
  description: string | null;
  profile_path: string;
  twin_machine: string;
  state: UniverseState;
  services: Service[];
  urls: Url[];
  state_path: string;
  created_at: string;
};

export type ApiError = {
  code: string;
  message: string;
  remedy: string;
};
