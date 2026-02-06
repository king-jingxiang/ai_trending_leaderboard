import React, { useEffect, useState } from 'react';
import { RepoCard } from '../components/RepoCard';
import { fetchTrending } from '../lib/api';
import type { Repo, TimeRange } from '../types';
import clsx from 'clsx';

type SortMode = 'composite' | 'trend' | 'stars';

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'composite', label: '综合排序' },
  { value: 'trend', label: '增长趋势' },
  { value: 'stars', label: 'Star 数' }
];

export const Dashboard: React.FC = () => {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<TimeRange>('daily');
  const [sortMode, setSortMode] = useState<SortMode>('composite');

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const data = await fetchTrending(timeRange);
      setRepos(data);
      setLoading(false);
    };
    loadData();
  }, [timeRange]);

  const parseUpdatedAt = (repo: Repo) => {
    if (!repo.last_seen) return 0;
    const time = new Date(repo.last_seen).getTime();
    return Number.isFinite(time) ? time : 0;
  };

  const maxValues = repos.reduce(
    (acc, repo) => ({
      stars: Math.max(acc.stars, repo.stars),
      growth: Math.max(acc.growth, repo.growth),
      forks: Math.max(acc.forks, repo.forks),
      updated: Math.max(acc.updated, parseUpdatedAt(repo))
    }),
    { stars: 1, growth: 1, forks: 1, updated: 1 }
  );

  const getCompositeScore = (repo: Repo) => {
    const updatedScore = parseUpdatedAt(repo) / maxValues.updated;
    const starsScore = repo.stars / maxValues.stars;
    const growthScore = repo.growth / maxValues.growth;
    const forksScore = repo.forks / maxValues.forks;
    return 0.1 * updatedScore + 0.3 * starsScore + 0.4 * growthScore + 0.2 * forksScore;
  };

  const sortedRepos = [...repos].sort((a, b) => {
    if (sortMode === 'trend') return b.growth - a.growth;
    if (sortMode === 'stars') return b.stars - a.stars;
    return getCompositeScore(b) - getCompositeScore(a);
  });

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-end sm:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trending Repositories</h1>
          <p className="text-gray-500 mt-1">See what the AI community is most excited about today.</p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="bg-white p-1 rounded-lg border border-gray-200 inline-flex">
            {(['daily', 'weekly', 'monthly'] as TimeRange[]).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={clsx(
                  "px-4 py-1.5 text-sm font-medium rounded-md capitalize transition-colors",
                  timeRange === range
                    ? "bg-indigo-50 text-indigo-700 shadow-sm"
                    : "text-gray-500 hover:text-gray-900"
                )}
              >
                {range}
              </button>
            ))}
          </div>
          <div className="bg-white p-1 rounded-lg border border-gray-200 inline-flex">
            {SORT_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setSortMode(option.value)}
                className={clsx(
                  "px-4 py-1.5 text-sm font-medium rounded-md transition-colors",
                  sortMode === option.value
                    ? "bg-indigo-50 text-indigo-700 shadow-sm"
                    : "text-gray-500 hover:text-gray-900"
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-200 rounded-xl"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {sortedRepos.map((repo, idx) => (
            <RepoCard key={`${repo.owner}/${repo.repo}`} repo={repo} rank={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
};
