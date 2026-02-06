import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchRepoDetails } from '../lib/api';
import type { Repo } from '../types';
import { StarHistoryChart } from '../components/StarHistoryChart';
import { ArrowLeft, Star, GitFork, ExternalLink, Calendar, TrendingUp, TrendingDown } from 'lucide-react';

const formatNumber = (num: number | undefined): string => {
  if (num === undefined || num === null) return 'N/A';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
};

const calculateGrowth = (project: Repo) => {
  if (!project.star_history || project.star_history.length === 0) {
    // Fallback to existing growth field if no history
    if (project.growth_90d !== undefined) {
       return {
         value: formatNumber(project.growth_90d),
         percentage: '',
         isPositive: project.growth_90d >= 0
       };
    }
    if (project.growth !== undefined) {
       return {
         value: formatNumber(project.growth),
         percentage: '',
         isPositive: project.growth >= 0
       };
    }
    return null;
  }

  const history = [...project.star_history].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const currentStars = project.stargazers_count || project.stars || history[history.length - 1].count;
  
  const now = new Date();
  const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
  
  // Find point closest to 90 days ago
  let closestPoint = history[0];
  let minDiff = Math.abs(new Date(closestPoint.date).getTime() - ninetyDaysAgo.getTime());
  
  for (const point of history) {
    const diff = Math.abs(new Date(point.date).getTime() - ninetyDaysAgo.getTime());
    if (diff < minDiff) {
      minDiff = diff;
      closestPoint = point;
    }
  }

  const growth = currentStars - closestPoint.count;
  const percentage = closestPoint.count > 0 
    ? ((growth / closestPoint.count) * 100).toFixed(1) + '%' 
    : '';

  return {
    value: formatNumber(Math.abs(growth)),
    percentage,
    isPositive: growth >= 0
  };
};

export const ProjectDetails: React.FC = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const [project, setProject] = useState<Repo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (owner && repo) {
      setLoading(true);
      fetchRepoDetails(owner, repo)
        .then(data => {
          setProject(data);
          setError(null);
        })
        .catch(err => {
          console.error(err);
          setError("Failed to load project details");
        })
        .finally(() => setLoading(false));
    }
  }, [owner, repo]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Project not found</h2>
        <Link to="/leaderboard" className="text-indigo-600 hover:text-indigo-800">
          Back to Leaderboard
        </Link>
      </div>
    );
  }

  const primaryTag = project.tags && !Array.isArray(project.tags) && project.tags.primary_tags ? project.tags.primary_tags[0] : null;
  const tagsList = project.tags 
    ? (Array.isArray(project.tags) ? project.tags : [...(project.tags.primary_tags || []), ...(project.tags.secondary_tags || [])])
    : [];

  const growthData = calculateGrowth(project);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/leaderboard" className="inline-flex items-center text-gray-500 hover:text-gray-900 transition-colors">
        <ArrowLeft size={20} className="mr-2" />
        Back to Leaderboard
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                 {primaryTag && (
                    <span className="text-sm font-medium text-indigo-600">
                      {primaryTag}
                    </span>
                 )}
              </div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                {project.owner} / {project.repo}
              </h1>
              <p className="text-gray-600 mt-2 text-lg">{project.description}</p>
              
              <div className="flex flex-wrap gap-2 mt-4">
                {tagsList.map(tag => (
                  <span key={tag} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium">
                    {tag}
                  </span>
                ))}
                {project.language && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                    {project.language}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
               <a 
                href={`https://github.com/${project.owner}/${project.repo}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                <ExternalLink size={16} />
                View on GitHub
              </a>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 border-t border-gray-100 pt-8">
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <div className="flex justify-center items-center text-gray-500 mb-1">
                <Star size={18} className="mr-1" />
                <span className="text-sm">Stars</span>
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(project.stargazers_count || project.stars)}
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-center">
               <div className="flex justify-center items-center text-gray-500 mb-1">
                <GitFork size={18} className="mr-1" />
                <span className="text-sm">Forks</span>
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(project.forks_count || project.forks)}
              </div>
            </div>
             <div className="p-4 bg-gray-50 rounded-lg text-center">
               <div className="flex justify-center items-center text-gray-500 mb-1">
                <Calendar size={18} className="mr-1" />
                <span className="text-sm">90d Growth</span>
              </div>
              {growthData ? (
                <div className={`text-2xl font-bold flex items-center justify-center gap-1 ${growthData.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {growthData.isPositive ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                  <span>{growthData.isPositive ? '+' : '-'}{growthData.value}</span>
                </div>
              ) : (
                 <div className="text-gray-400 mt-1">N/A</div>
              )}
              {growthData?.percentage && (
                  <div className={`text-xs font-medium ${growthData.isPositive ? 'text-green-600' : 'text-red-600'} opacity-80`}>
                    {growthData.percentage}
                  </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Star History</h2>
        {project.star_history && project.star_history.length > 0 ? (
          <StarHistoryChart data={project.star_history} />
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400">
            No history data available
          </div>
        )}
      </div>
    </div>
  );
};
