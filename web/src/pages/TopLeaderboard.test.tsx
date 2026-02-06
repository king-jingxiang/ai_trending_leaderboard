import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { TopLeaderboard } from './TopLeaderboard';
import { fetchTopProjects } from '../lib/api';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API module
vi.mock('../lib/api', () => ({
  fetchTopProjects: vi.fn(),
}));

const mockData = {
  date: '2026-02-06',
  categories: [
    {
      name: 'Application Frameworks',
      subcategories: [
        {
          name: 'Agent Framework',
          projects: [
            {
              name: 'n8n-io/n8n',
              owner: 'n8n-io',
              repo: 'n8n',
              url: 'https://github.com/n8n-io/n8n',
              description: 'Workflow automation',
              stargazers_count: 1000,
              forks_count: 500,
              growth_90d: 100,
              score: 2000,
              rank: 1,
              primary_tags: ['Application Frameworks'],
              secondary_tags: ['Agent Framework'],
              language: 'TypeScript',
              topics: ['automation']
            }
          ]
        }
      ]
    },
    {
      name: 'Tools',
      subcategories: []
    }
  ]
};

describe('TopLeaderboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (fetchTopProjects as any).mockReturnValue(new Promise(() => {}));
    render(<TopLeaderboard />);
    // Check for spinner or loading indicator logic
    // The component renders a spinner div with animate-spin
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders data after loading', async () => {
    (fetchTopProjects as any).mockResolvedValue(mockData);
    
    render(
      <BrowserRouter>
        <TopLeaderboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AI Trending Leaderboard')).toBeInTheDocument();
    });

    // Check for Category Tabs
    expect(screen.getByText('Application Frameworks')).toBeInTheDocument();
    expect(screen.getByText('Tools')).toBeInTheDocument();

    // Check for Subcategory
    expect(screen.getByText('Agent Framework')).toBeInTheDocument();

    // Check for Project
    expect(screen.getByText('n8n-io/n8n')).toBeInTheDocument();
    expect(screen.getByText('Workflow automation')).toBeInTheDocument();
    
    // Check Rank 1
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('switches categories', async () => {
    (fetchTopProjects as any).mockResolvedValue(mockData);
    
    render(
      <BrowserRouter>
        <TopLeaderboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Application Frameworks')).toBeInTheDocument();
    });

    // Initial state: Agent Framework is visible
    expect(screen.getByText('Agent Framework')).toBeInTheDocument();

    // Click Tools tab
    fireEvent.click(screen.getByText('Tools'));

    // Agent Framework should disappear (as Tools has no subcategories in mock)
    await waitFor(() => {
      expect(screen.queryByText('Agent Framework')).not.toBeInTheDocument();
    });
  });
});
