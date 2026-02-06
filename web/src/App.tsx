import { HashRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { TopLeaderboard } from './pages/TopLeaderboard';
import { ProjectDetails } from './pages/ProjectDetails';
import { CategoryExplorer } from './pages/CategoryExplorer';

function App() {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/leaderboard" element={<TopLeaderboard />} />
          <Route path="/project/:owner/:repo" element={<ProjectDetails />} />
          <Route path="/categories" element={<CategoryExplorer />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
}

export default App;
