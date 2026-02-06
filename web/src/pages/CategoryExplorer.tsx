import React, { useState, useEffect, useRef, useMemo } from 'react';
import { RepoCard } from '../components/RepoCard';
import { fetchAllRepos } from '../lib/api';
import type { Repo } from '../types';
import clsx from 'clsx';

type SortMode = 'composite' | 'trend' | 'stars';
type FilterMode = 'tag' | 'topic';
type TagLevel = 'all' | 'primary' | 'secondary';

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'composite', label: '综合排序' },
  { value: 'trend', label: '增长趋势' },
  { value: 'stars', label: 'Star 数' }
];

export const CategoryExplorer: React.FC = () => {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedPrimary, setSelectedPrimary] = useState("All");
  const [selectedSecondary, setSelectedSecondary] = useState("All");
  const [selectedTopic, setSelectedTopic] = useState("All");
  const [selectedTagLevel, setSelectedTagLevel] = useState<TagLevel>('all');
  const [sortMode, setSortMode] = useState<SortMode>('composite');
  const [filterMode, setFilterMode] = useState<FilterMode>('tag');
  const [expandedPrimaries, setExpandedPrimaries] = useState<string[]>([]);
  const mainContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAllRepos().then(setRepos);
  }, []);

  useEffect(() => {
    mainContentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [selectedPrimary, selectedSecondary, selectedTopic, filterMode]);

  const handleFilterModeChange = (mode: FilterMode) => {
    setFilterMode(mode);
    setSelectedPrimary("All");
    setSelectedSecondary("All");
    setSelectedTopic("All");
    setSelectedTagLevel('all');
  };

  const normalizeTags = (tags: Repo['tags']) => {
    if (Array.isArray(tags)) {
      return { primary: [], secondary: tags };
    }
    return {
      primary: tags?.primary_tags || [],
      secondary: tags?.secondary_tags || [],
    };
  };

  const tagHierarchy = useMemo(() => {
    const hierarchy = new Map<string, { count: number; secondary: Map<string, number> }>();
    repos.forEach((repo) => {
      const { primary, secondary } = normalizeTags(repo.tags);
      const primarySet = new Set(primary.map((tag) => tag.trim()).filter(Boolean));
      const secondarySet = new Set(secondary.map((tag) => tag.trim()).filter(Boolean));
      primarySet.forEach((primaryTag) => {
        const current = hierarchy.get(primaryTag) || { count: 0, secondary: new Map() };
        current.count += 1;
        secondarySet.forEach((secondaryTag) => {
          current.secondary.set(secondaryTag, (current.secondary.get(secondaryTag) || 0) + 1);
        });
        hierarchy.set(primaryTag, current);
      });
    });
    return Array.from(hierarchy.entries())
      .map(([name, data]) => ({
        name,
        count: data.count,
        secondary: Array.from(data.secondary.entries())
          .map(([secondaryName, count]) => ({ name: secondaryName, count }))
          .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name)),
      }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  }, [repos]);

  const togglePrimaryExpand = (primaryName: string) => {
    setExpandedPrimaries((prev) =>
      prev.includes(primaryName)
        ? prev.filter((item) => item !== primaryName)
        : [...prev, primaryName]
    );
  };

  const topicCategories = useMemo(() => {
    const counts = new Map<string, number>();
    repos.forEach((repo) => {
      (repo.topics || []).forEach((topic) => {
        const normalized = topic.trim();
        if (!normalized) return;
        counts.set(normalized, (counts.get(normalized) || 0) + 1);
      });
    });
    const ordered = Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([name]) => name);
    return ["All", ...ordered];
  }, [repos]);

  const normalizedTopic = selectedTopic.trim().toLowerCase();
  const normalizedPrimary = selectedPrimary.trim().toLowerCase();
  const normalizedSecondary = selectedSecondary.trim().toLowerCase();
  const filteredRepos = filterMode === 'topic'
    ? (selectedTopic === "All"
        ? repos
        : repos.filter(repo => {
            const list = repo.topics || [];
            return list.some(item => item.trim().toLowerCase() === normalizedTopic);
          }))
    : (selectedTagLevel === 'all'
        ? repos
        : repos.filter(repo => {
            const { primary, secondary } = normalizeTags(repo.tags);
            const primaryMatch = primary.some(item => item.trim().toLowerCase() === normalizedPrimary);
            if (selectedTagLevel === 'primary') return primaryMatch;
            const secondaryMatch = secondary.some(item => item.trim().toLowerCase() === normalizedSecondary);
            return primaryMatch && secondaryMatch;
          }));

  const parseUpdatedAt = (repo: Repo) => {
    if (!repo.last_seen) return 0;
    const time = new Date(repo.last_seen).getTime();
    return Number.isFinite(time) ? time : 0;
  };

  const maxValues = filteredRepos.reduce(
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

  const sortedRepos = [...filteredRepos].sort((a, b) => {
    if (sortMode === 'trend') return b.growth - a.growth;
    if (sortMode === 'stars') return b.stars - a.stars;
    return getCompositeScore(b) - getCompositeScore(a);
  });

  return (
    <div className="flex flex-col md:flex-row gap-8">
      {/* Sidebar */}
      <div className="w-full md:w-64 flex-shrink-0">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 sticky top-24 max-h-[calc(100vh-6rem)] overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => handleFilterModeChange('tag')}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-md transition-colors border",
                filterMode === 'tag'
                  ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                  : "text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              Tag
            </button>
            <button
              onClick={() => handleFilterModeChange('topic')}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-md transition-colors border",
                filterMode === 'topic'
                  ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                  : "text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              Topic
            </button>
          </div>
          <h3 className="font-semibold text-gray-900 mb-4 px-2">
            {filterMode === 'tag' ? 'Tags' : 'Topics'}
          </h3>
          {filterMode === 'tag' ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2 border-b border-gray-100 pb-3">
                <button
                  onClick={() => {
                    setSelectedPrimary("All");
                    setSelectedSecondary("All");
                    setSelectedTagLevel('all');
                  }}
                  className={clsx(
                    "px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                    selectedTagLevel === 'all'
                      ? "bg-indigo-50 text-indigo-700 border-indigo-200 shadow-sm"
                      : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  All
                </button>
              </div>
              {tagHierarchy.length === 0 ? (
                <div className="text-xs text-gray-400 px-2 py-1">暂无标签</div>
              ) : (
                tagHierarchy.map((primary) => {
                  const isExpanded = expandedPrimaries.includes(primary.name);
                  return (
                    <div
                      key={primary.name}
                      className="rounded-lg border border-gray-200 bg-white shadow-sm"
                    >
                      <div className="flex items-center justify-between gap-2 px-3 py-2">
                        <button
                          onClick={() => {
                            setSelectedPrimary(primary.name);
                            setSelectedSecondary("All");
                            setSelectedTagLevel('primary');
                            togglePrimaryExpand(primary.name);
                          }}
                          className={clsx(
                            "flex items-center gap-2 text-left text-xs font-semibold rounded-md px-2.5 py-1 transition-colors",
                            selectedPrimary === primary.name && selectedTagLevel === 'primary'
                              ? "bg-indigo-50 text-indigo-700"
                              : "text-gray-700 hover:bg-gray-50"
                          )}
                        >
                          <span>{primary.name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600">
                            {primary.count}
                          </span>
                        </button>
                        <button
                          onClick={() => togglePrimaryExpand(primary.name)}
                          className={clsx(
                            "text-xs font-semibold px-2 py-1 rounded-md border transition-colors",
                            isExpanded
                              ? "bg-gray-50 text-gray-700 border-gray-200"
                              : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
                          )}
                        >
                          {isExpanded ? '收起' : '展开'}
                        </button>
                      </div>
                      {isExpanded && (
                        <div className="px-3 pb-3 pt-1 space-y-2">
                          {primary.secondary.map((secondary) => (
                            <button
                              key={`${primary.name}-${secondary.name}`}
                              onClick={() => {
                                setSelectedPrimary(primary.name);
                                setSelectedSecondary(secondary.name);
                                setSelectedTagLevel('secondary');
                              }}
                              className={clsx(
                                "w-full flex items-center justify-between rounded-md border px-3 py-2 text-xs font-medium transition-colors",
                                selectedPrimary === primary.name &&
                                  selectedSecondary === secondary.name &&
                                  selectedTagLevel === 'secondary'
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200 shadow-sm"
                                  : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"
                              )}
                            >
                              <span className="truncate">{secondary.name}</span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600">
                                {secondary.count}
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {topicCategories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedTopic(category)}
                  title={category !== "All" ? `Topic: ${category}` : "显示全部 Topic"}
                  className={clsx(
                    "px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                    selectedTopic === category
                      ? "bg-indigo-50 text-indigo-700 border-indigo-200 shadow-sm"
                      : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  {category}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1" ref={mainContentRef}>
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <h1
              className="text-2xl font-bold text-gray-900"
            >
              {filterMode === 'tag'
                ? (selectedTagLevel === 'all'
                    ? 'All'
                    : selectedTagLevel === 'primary'
                      ? selectedPrimary
                      : `${selectedPrimary} / ${selectedSecondary}`)
                : selectedTopic}
            </h1>
            <p className="text-gray-500 mt-1">
              Found {filteredRepos.length} repositories · {filterMode === 'tag'
                ? `Tag 视图 · ${selectedTagLevel === 'primary' ? '一级标签' : selectedTagLevel === 'secondary' ? '二级标签' : '全部标签'}`
                : 'Topic 视图'}
            </p>
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sortedRepos.map((repo, idx) => (
            <RepoCard key={`${repo.owner}/${repo.repo}`} repo={repo} rank={idx + 1} growthLabel="90d" />
          ))}
        </div>
      </div>
    </div>
  );
};
