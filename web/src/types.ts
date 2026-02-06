export interface StarHistoryPoint {
  date: string;
  count: number;
}

export interface Repo {
  owner: string;
  repo: string;
  description: string;
  language: string;
  stars: number;
  forks: number;
  growth: number;
  growth_rate_90d?: number;
  tags: string[] | { primary_tags: string[]; secondary_tags: string[] };
  topics?: string[];
  star_history?: StarHistoryPoint[];
  last_seen?: string;
  // For Leaderboard compatibility
  name?: string; // full_name or owner/repo
  stargazers_count?: number;
  forks_count?: number;
  growth_90d?: number;
  score?: number;
  rank?: number;
  url?: string;
  primary_tags?: string[];
  secondary_tags?: string[];
}

export interface RankedProject extends Repo {
  name: string;
  url: string;
  stargazers_count: number;
  forks_count: number;
  growth_90d: number;
  score: number;
  rank: number;
  primary_tags: string[];
  secondary_tags: string[];
}

export interface SecondaryCategory {
  name: string;
  projects: RankedProject[];
}

export interface PrimaryCategory {
  name: string;
  subcategories: SecondaryCategory[];
}

export interface TopProjectsResponse {
  date: string;
  categories: PrimaryCategory[];
}

export type TimeRange = 'daily' | 'weekly' | 'monthly';
