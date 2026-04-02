import { useEffect, useState } from 'react'
import { fetchProspects } from '../lib/supabase'

function ProspectsTable({ onSelectProspect }) {
  const [prospects, setProspects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    status: '',
    product: '',
    search: '',
  })

  useEffect(() => {
    const loadProspects = async () => {
      try {
        setLoading(true)
        const data = await fetchProspects(filters)
        setProspects(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadProspects()
  }, [filters])

  const statusColors = {
    new: 'bg-gray-100 text-gray-800',
    drafted: 'bg-yellow-100 text-yellow-800',
    sent: 'bg-purple-100 text-purple-800',
    followed_up_1: 'bg-blue-100 text-blue-800',
    followed_up_2: 'bg-indigo-100 text-indigo-800',
    replied: 'bg-green-100 text-green-800',
    meeting: 'bg-emerald-100 text-emerald-800',
    closed: 'bg-red-100 text-red-800',
    exhausted: 'bg-gray-100 text-gray-600',
  }

  const statusLabels = {
    new: 'New',
    drafted: 'Drafted',
    sent: 'Sent',
    followed_up_1: 'Follow-up 1',
    followed_up_2: 'Follow-up 2',
    replied: 'Replied',
    meeting: 'Meeting',
    closed: 'Closed',
    exhausted: 'Exhausted',
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex gap-4 flex-wrap items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Búsqueda</label>
          <input
            type="text"
            placeholder="Nombre, empresa, email..."
            value={filters.search}
            onChange={e => setFilters({ ...filters, search: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={filters.status}
            onChange={e => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            {Object.entries(statusLabels).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Producto</label>
          <select
            value={filters.product}
            onChange={e => setFilters({ ...filters, product: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            <option value="shieldai">ShieldAI</option>
            <option value="twolaps">2laps</option>
          </select>
        </div>

        <button
          onClick={() => setFilters({ status: '', product: '', search: '' })}
          className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          Limpiar filtros
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-gray-400">Cargando...</div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
          Error: {error}
        </div>
      ) : prospects.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
          No hay prospects con esos filtros
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Nombre</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Empresa</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Cargo</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Email</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Producto</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Touchpoints</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {prospects.map(prospect => (
                  <tr
                    key={prospect.id}
                    onClick={() => onSelectProspect(prospect)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      {prospect.first_name} {prospect.last_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{prospect.company_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{prospect.job_title}</td>
                    <td className="px-6 py-4 text-sm text-blue-600 truncate">{prospect.email}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {prospect.product_target === 'shieldai' ? 'ShieldAI' : '2laps'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[prospect.status]}`}>
                        {statusLabels[prospect.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">
                      {prospect.touchpoints}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-gray-50 border-t border-gray-200 px-6 py-3 text-sm text-gray-600">
            {prospects.length} prospects
          </div>
        </div>
      )}
    </div>
  )
}

export default ProspectsTable
