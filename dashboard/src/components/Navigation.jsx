function Navigation({ currentView, onNavigate }) {
  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: '📊' },
    { id: 'prospects', label: 'Prospects', icon: '👥' },
    { id: 'queue', label: 'Cola de envío', icon: '📬' },
    { id: 'activity', label: 'Actividad', icon: '⚡' },
  ]

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <h1 className="text-xl font-semibold text-gray-900">T&T Outreach</h1>

          <div className="flex gap-1">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === item.id
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
