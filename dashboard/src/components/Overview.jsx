import { useEffect, useState } from 'react'
import { getProspectsStats } from '../lib/supabase'

function Overview() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true)
        const data = await getProspectsStats()
        setStats(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadStats()
    // Refetch every 30 seconds
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-400">Cargando...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        Error: {error}
      </div>
    )
  }

  if (!stats) return null

  const metrics = [
    { label: 'Total prospects', value: stats.total, color: 'bg-blue-50 border-blue-200' },
    { label: 'Nuevos (new)', value: stats.new, color: 'bg-gray-50 border-gray-200' },
    { label: 'Borradores (drafted)', value: stats.drafted, color: 'bg-yellow-50 border-yellow-200' },
    { label: 'Enviados (sent)', value: stats.sent, color: 'bg-purple-50 border-purple-200' },
    { label: 'Respuestas (replied)', value: stats.replied, color: 'bg-green-50 border-green-200' },
    { label: 'Tasa respuesta', value: `${stats.responseRate}%`, color: 'bg-emerald-50 border-emerald-200' },
    { label: 'ShieldAI', value: stats.shieldai, color: 'bg-indigo-50 border-indigo-200' },
    { label: '2laps', value: stats.twolaps, color: 'bg-pink-50 border-pink-200' },
  ]

  return (
    <div className="space-y-8">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <div
            key={i}
            className={`${metric.color} border rounded-lg p-6 transition-all hover:shadow-sm`}
          >
            <div className="text-sm text-gray-600 mb-2">{metric.label}</div>
            <div className="text-3xl font-semibold text-gray-900">{metric.value}</div>
          </div>
        ))}
      </div>

      {/* Activity Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Actividad últimos 7 días</h2>

        <div className="flex items-end gap-2 h-40">
          {Object.entries(stats.activityByDay)
            .reverse()
            .map(([date, count], i) => {
              const maxCount = Math.max(...Object.values(stats.activityByDay), 1)
              const height = (count / maxCount) * 100
              const dateObj = new Date(date)
              const day = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'][dateObj.getDay()]

              return (
                <div key={date} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-blue-500 rounded-t opacity-80 hover:opacity-100 transition-opacity"
                    style={{ height: `${Math.max(height, 5)}%` }}
                  />
                  <div className="text-xs text-gray-500 mt-2 text-center">{day}</div>
                  {count > 0 && <div className="text-xs font-semibold text-gray-700 mt-1">{count}</div>}
                </div>
              )
            })}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Distribución por producto</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">ShieldAI</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500"
                    style={{ width: `${(stats.shieldai / stats.total) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-10 text-right">
                  {((stats.shieldai / stats.total) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">2laps</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-pink-500"
                    style={{ width: `${(stats.twolaps / stats.total) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-10 text-right">
                  {((stats.twolaps / stats.total) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Distribución por estado</h3>
          <div className="space-y-3">
            {[
              { label: 'New', value: stats.new, color: 'bg-gray-400' },
              { label: 'Drafted', value: stats.drafted, color: 'bg-yellow-500' },
              { label: 'Sent', value: stats.sent, color: 'bg-purple-500' },
              { label: 'Replied', value: stats.replied, color: 'bg-green-500' },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{item.label}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={item.color}
                      style={{ width: `${(item.value / stats.total) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-10 text-right">
                    {item.value}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Overview
