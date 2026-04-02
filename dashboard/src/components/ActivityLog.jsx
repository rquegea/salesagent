import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

function ActivityLog() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadActivities()
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadActivities, 10000)
    return () => clearInterval(interval)
  }, [filter])

  const loadActivities = async () => {
    try {
      setLoading(true)

      let query = supabase
        .from('prospects')
        .select('id, first_name, last_name, status, product_target, updated_at, last_contact_at')

      // Get recent updates
      const { data, error: err } = await query
        .order('updated_at', { ascending: false })
        .limit(50)

      if (err) throw err

      // Map to activities
      const logs = data.map(prospect => ({
        id: prospect.id,
        type: 'status_change',
        status: prospect.status,
        name: `${prospect.first_name} ${prospect.last_name}`,
        product: prospect.product_target,
        time: new Date(prospect.updated_at),
      }))

      setActivities(logs)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getActivityIcon = (status) => {
    const icons = {
      new: '✨',
      drafted: '✏️',
      sent: '📧',
      followed_up_1: '↩️',
      followed_up_2: '↩️↩️',
      replied: '💬',
      meeting: '📞',
      closed: '✅',
      exhausted: '❌',
    }
    return icons[status] || '•'
  }

  const getActivityLabel = (status) => {
    const labels = {
      new: 'Nuevo prospect',
      drafted: 'Borrador creado',
      sent: 'Email enviado',
      followed_up_1: 'Follow-up 1',
      followed_up_2: 'Follow-up 2',
      replied: 'Respuesta recibida',
      meeting: 'Reunión agendada',
      closed: 'Cerrado',
      exhausted: 'Exhaused',
    }
    return labels[status] || 'Evento'
  }

  const getActivityColor = (status) => {
    const colors = {
      new: 'bg-gray-100 text-gray-700',
      drafted: 'bg-yellow-100 text-yellow-700',
      sent: 'bg-purple-100 text-purple-700',
      followed_up_1: 'bg-blue-100 text-blue-700',
      followed_up_2: 'bg-indigo-100 text-indigo-700',
      replied: 'bg-green-100 text-green-700',
      meeting: 'bg-emerald-100 text-emerald-700',
      closed: 'bg-red-100 text-red-700',
      exhausted: 'bg-gray-100 text-gray-600',
    }
    return colors[status] || 'bg-gray-100 text-gray-700'
  }

  const formatTime = (date) => {
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Hace unos segundos'
    if (diffMins < 60) return `Hace ${diffMins}m`
    if (diffHours < 24) return `Hace ${diffHours}h`
    if (diffDays < 7) return `Hace ${diffDays}d`

    return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })
  }

  const filteredActivities = filter === 'all'
    ? activities
    : activities.filter(a => a.status === filter)

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

  return (
    <div className="space-y-6">
      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'all'
              ? 'bg-gray-900 text-white'
              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
          }`}
        >
          Todo
        </button>
        {['sent', 'replied', 'drafted', 'new'].map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === status
                ? 'bg-gray-900 text-white'
                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Timeline */}
      {filteredActivities.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
          Sin actividades
        </div>
      ) : (
        <div className="space-y-2">
          {filteredActivities.map((activity, i) => (
            <div
              key={activity.id + i}
              className="bg-white border border-gray-200 rounded-lg p-4 flex items-start gap-4 hover:shadow-sm transition-shadow"
            >
              <div className="text-2xl flex-shrink-0 mt-1">
                {getActivityIcon(activity.status)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-gray-900 text-sm">
                    {activity.name}
                  </h3>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getActivityColor(activity.status)}`}>
                    {getActivityLabel(activity.status)}
                  </span>
                  <span className="text-xs text-gray-500">
                    {activity.product === 'shieldai' ? 'ShieldAI' : '2laps'}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {formatTime(activity.time)}
                </div>
              </div>

              <div className="text-xs text-gray-400 flex-shrink-0">
                {activity.time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ActivityLog
