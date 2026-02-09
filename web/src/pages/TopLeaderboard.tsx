import React, { useEffect, useState } from 'react';
import { fetchTopProjects } from '../lib/api';
import type { TopProjectsResponse } from '../types';
import { ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export const TopLeaderboard: React.FC = () => {
  const [data, setData] = useState<TopProjectsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>('');
  const [activeSubCategory, setActiveSubCategory] = useState<string>('');

  useEffect(() => {
    fetchTopProjects().then(response => {
      setData(response);
      if (response && response.categories.length > 0) {
        const firstCategory = response.categories[0];
        setActiveCategory(firstCategory.name);
        if (firstCategory.subcategories.length > 0) {
          setActiveSubCategory(firstCategory.subcategories[0].name);
        }
      }
      setLoading(false);
    });
  }, []);

  const handleCategoryChange = (categoryName: string) => {
    setActiveCategory(categoryName);
    const category = data?.categories.find(c => c.name === categoryName);
    if (category && category.subcategories.length > 0) {
      setActiveSubCategory(category.subcategories[0].name);
    } else {
      setActiveSubCategory('');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!data || !data.categories.length) {
    return (
      <div className="text-center py-12 text-gray-500">
        No leaderboard data available.
      </div>
    );
  }

  const selectedCategory = data.categories.find(c => c.name === activeCategory);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Trending Leaderboard</h1>
        <p className="text-gray-500 mt-2">
           Weighted Score = Stars + (Forks * 2) + (90d Growth * 10)
        </p>
        <p className="text-sm text-gray-400 mt-1">Generated on: {data.date}</p>
      </div>

      {/* Primary Category Tabs */}
      <div className="border-b border-gray-200 overflow-x-auto no-scrollbar">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {data.categories.map((category) => (
            <button
              key={category.name}
              onClick={() => handleCategoryChange(category.name)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeCategory === category.name
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
            >
              {category.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Secondary Categories Tabs */}
      {selectedCategory && selectedCategory.subcategories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedCategory.subcategories.map((sub) => (
            <button
              key={sub.name}
              onClick={() => setActiveSubCategory(sub.name)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-colors
                ${activeSubCategory === sub.name
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
              `}
            >
              {sub.name}
            </button>
          ))}
        </div>
      )}

      {/* Content Area */}
      <div className="space-y-12">
        {selectedCategory?.subcategories
          .filter(sub => sub.name === activeSubCategory)
          .map((sub) => (
          <div key={sub.name} className="space-y-4 animate-in fade-in duration-300">
            <h2 className="text-xl font-bold text-gray-900 border-l-4 border-indigo-500 pl-3">
              {sub.name}
            </h2>
            
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12 sm:px-6">
                        Rank
                      </th>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px] sm:px-6">
                        Project
                      </th>
                      <th scope="col" className="hidden sm:table-cell px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stars
                      </th>
                      <th scope="col" className="hidden md:table-cell px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Forks
                      </th>
                      <th scope="col" className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider sm:px-6">
                        90d Growth
                      </th>
                      <th scope="col" className="hidden lg:table-cell px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th scope="col" className="hidden xl:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[300px]">
                        Description
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {sub.projects.map((project) => (
                      <tr key={project.name} className="hover:bg-gray-50 transition-colors">
                        <td className="px-3 py-4 whitespace-nowrap text-center sm:px-6">
                          <div className={`
                            inline-flex items-center justify-center w-6 h-6 sm:w-8 sm:h-8 rounded-full font-bold text-xs sm:text-sm
                            ${project.rank === 1 ? 'bg-yellow-100 text-yellow-700' : 
                              project.rank === 2 ? 'bg-gray-100 text-gray-700' :
                              project.rank === 3 ? 'bg-orange-100 text-orange-700' : 'text-gray-500'}
                          `}>
                            {project.rank}
                          </div>
                        </td>
                        <td className="px-4 py-4 sm:px-6">
                          <div className="flex items-center">
                            <div>
                                <Link 
                                  to={`/project/${project.owner}/${project.repo}`}
                                  className="text-sm font-semibold text-indigo-600 hover:text-indigo-900 block"
                                >
                                  {project.repo}
                                </Link>
                                <a 
                                  href={project.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1 mt-0.5 break-all"
                                >
                                  {project.url} <ExternalLink size={10} />
                                </a>
                                {/* Mobile-only metrics */}
                                <div className="sm:hidden mt-1 text-xs text-gray-500 flex gap-2">
                                  <span>⭐ {(project.stargazers_count/1000).toFixed(1)}k</span>
                                  <span>Score: {(project.score/1000).toFixed(1)}k</span>
                                </div>
                            </div>
                          </div>
                        </td>
                        <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                          {(project.stargazers_count / 1000).toFixed(1)}k
                        </td>
                        <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                          {(project.forks_count / 1000).toFixed(1)}k
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap text-center text-sm text-green-600 font-medium sm:px-6">
                          +{(project.growth_90d / 1000).toFixed(1)}k
                        </td>
                        <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap text-center text-sm font-bold text-gray-900">
                          {(project.score / 1000).toFixed(1)}k
                        </td>
                        <td className="hidden xl:table-cell px-6 py-4 text-sm text-gray-500 line-clamp-2 max-w-xs">
                          {project.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
