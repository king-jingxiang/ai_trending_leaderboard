import type { Repo, TimeRange, TopProjectsResponse } from '../types';

const BASE_URL = import.meta.env.VITE_DATA_URL || 'https://pub-f31a5865021b44d0a2c4003b3da37f04.r2.dev';

// Mock Data for development
const MOCK_REPOS: Repo[] = [
  {
    owner: "sig-networks",
    repo: "not-a-real-repo",
    description: "An awesome AI agent framework that does everything.",
    language: "Python",
    stars: 12500,
    forks: 1200,
    growth: 450,
    tags: {
      primary_tags: ["Frameworks & Orchestration"],
      secondary_tags: ["Agent Framework", "RAG"]
    },
    topics: ["agent-framework", "multi-agent", "llm"],
    star_history: [
      { date: "2023-10-01", count: 100 },
      { date: "2023-11-01", count: 500 },
      { date: "2023-12-01", count: 2000 },
      { date: "2024-01-01", count: 8000 },
      { date: "2024-01-30", count: 12500 },
    ]
  },
  {
    owner: "tensor-flow-x",
    repo: "super-fast-inference",
    description: "Inference engine optimized for everything.",
    language: "C++",
    stars: 8900,
    forks: 800,
    growth: 120,
    tags: {
      primary_tags: ["Infrastructure & Training"],
      secondary_tags: ["Inference & Serving", "Quantization"]
    },
    topics: ["inference", "serving", "quantization"],
    star_history: [
      { date: "2023-12-01", count: 1000 },
      { date: "2024-01-01", count: 5000 },
      { date: "2024-01-30", count: 8900 },
    ]
  }
];

export async function fetchTrending(range: TimeRange): Promise<Repo[]> {
  try {
    console.log(`Fetching trending for range: ${range}`);
    const today = new Date().toISOString().split('T')[0];
    const response = await fetch(`${BASE_URL}/data/${range}/${today}.json`);
    if (!response.ok) throw new Error("Failed to fetch");
    return await response.json();
  } catch (e) {
    console.warn("Using mock data", e);
    return MOCK_REPOS;
  }
}

export async function fetchTopProjects(date?: string): Promise<TopProjectsResponse | null> {
  try {
    const targetDate = date || new Date().toISOString().split('T')[0];
    console.log(`Fetching top projects for date: ${targetDate}`);
    const response = await fetch(`${BASE_URL}/data/top/top_projects_${targetDate}.json`);
    if (!response.ok) throw new Error("Failed to fetch top projects");
    return await response.json();
  } catch (e) {
    console.warn("Failed to fetch top projects", e);
    // Try yesterday if today fails? Or just return null
    return null;
  }
}

export async function fetchRepoDetails(owner: string, repo: string): Promise<Repo | null> {
  try {
    const response = await fetch(`${BASE_URL}/data/projects/${owner}/${repo}.json`);
    if (!response.ok) throw new Error("Failed to fetch");
    return await response.json();
  } catch (e) {
    console.warn("Using mock data for details", e);
    return MOCK_REPOS.find(r => r.owner === owner && r.repo === repo) || MOCK_REPOS[0];
  }
}

export async function fetchAllRepos(): Promise<Repo[]> {
  try {
    const response = await fetch(`${BASE_URL}/data/index.json`);
    if (!response.ok) throw new Error("Failed to fetch index");
    const data = await response.json();
    return data.map((item: any) => ({
      ...item,
      // Map growth_90d to growth if growth is missing, or default to 0
      growth: item.growth ?? item.growth_90d ?? 0,
      last_seen: item.last_seen ?? item.last_updated
    }));
  } catch {
    return MOCK_REPOS;
  }
}
