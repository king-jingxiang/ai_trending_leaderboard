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
  tags: string[] | { primary_tags: string[]; secondary_tags: string[] };
  topics?: string[];
  star_history?: StarHistoryPoint[];
  last_seen?: string;
}

export type TimeRange = 'daily' | 'weekly' | 'monthly';
