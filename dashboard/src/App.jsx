import { useState, useEffect } from 'react'
import Navigation from './components/Navigation'
import Overview from './components/Overview'
import ProspectsTable from './components/ProspectsTable'
import ProspectDetail from './components/ProspectDetail'
import SendQueue from './components/SendQueue'
import ActivityLog from './components/ActivityLog'

function App() {
  const [view, setView] = useState('overview')
  const [selectedProspect, setSelectedProspect] = useState(null)

  const handleSelectProspect = (prospect) => {
    setSelectedProspect(prospect)
    setView('detail')
  }

  const handleBack = () => {
    setSelectedProspect(null)
    setView('overview')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation currentView={view} onNavigate={setView} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {view === 'overview' && <Overview />}
        {view === 'prospects' && <ProspectsTable onSelectProspect={handleSelectProspect} />}
        {view === 'detail' && selectedProspect && (
          <ProspectDetail prospect={selectedProspect} onBack={handleBack} />
        )}
        {view === 'queue' && <SendQueue />}
        {view === 'activity' && <ActivityLog />}
      </main>
    </div>
  )
}

export default App
