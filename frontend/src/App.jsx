import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import BackendStatusBanner from './components/BackendStatusBanner.jsx'
import Landing from './pages/Landing.jsx'
import Analyze from './pages/Analyze.jsx'
import Dashboard from './pages/Dashboard.jsx'
import MyDatasetsPage from './pages/MyDatasets.jsx'

export default function App() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <BackendStatusBanner />
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/my-datasets" element={<MyDatasetsPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
