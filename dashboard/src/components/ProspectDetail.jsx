import { useState } from 'react'
import { updateProspectStatus } from '../lib/supabase'

function ProspectDetail({ prospect, onBack }) {
  const [isUpdating, setIsUpdating] = useState(false)

  const handleStatusChange = async (newStatus) => {
    try {
      setIsUpdating(true)
      await updateProspectStatus(prospect.id, newStatus)
      prospect.status = newStatus
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setIsUpdating(false)
    }
  }

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

  const cadenceInfo = {
    0: 'Cold email',
    3: 'LinkedIn connect',
    7: 'Follow-up 1',
    14: 'Follow-up 2',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="text-gray-600 hover:text-gray-900 text-xl"
        >
          ← Volver
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {prospect.first_name} {prospect.last_name}
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Contact Info */}
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Información de contacto</h2>

            <div className="space-y-4 text-sm">
              <div>
                <div className="text-gray-600 mb-1">Empresa</div>
                <div className="font-medium text-gray-900">{prospect.company_name}</div>
              </div>

              <div>
                <div className="text-gray-600 mb-1">Cargo</div>
                <div className="font-medium text-gray-900">{prospect.job_title}</div>
              </div>

              <div>
                <div className="text-gray-600 mb-1">Email</div>
                <a
                  href={`mailto:${prospect.email}`}
                  className="font-medium text-blue-600 hover:underline"
                >
                  {prospect.email}
                </a>
              </div>

              {prospect.linkedin_url && (
                <div>
                  <div className="text-gray-600 mb-1">LinkedIn</div>
                  <a
                    href={prospect.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-blue-600 hover:underline truncate block"
                  >
                    Ver perfil
                  </a>
                </div>
              )}

              <div>
                <div className="text-gray-600 mb-1">Ubicación</div>
                <div className="font-medium text-gray-900">
                  {prospect.city}, {prospect.country}
                </div>
              </div>

              <div>
                <div className="text-gray-600 mb-1">Producto</div>
                <div className="font-medium text-gray-900">
                  {prospect.product_target === 'shieldai' ? 'ShieldAI' : '2laps'}
                </div>
              </div>
            </div>
          </div>

          {/* Status & Actions */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Estado</h2>

            <div className="mb-4">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${statusColors[prospect.status]}`}>
                {statusLabels[prospect.status]}
              </span>
            </div>

            <div className="text-sm text-gray-600 space-y-2 mb-4">
              <div>
                <span className="font-medium">Touchpoints:</span> {prospect.touchpoints}
              </div>
              <div>
                <span className="font-medium">Creado:</span> {new Date(prospect.created_at).toLocaleDateString('es-ES')}
              </div>
              {prospect.last_contact_at && (
                <div>
                  <span className="font-medium">Último contacto:</span> {new Date(prospect.last_contact_at).toLocaleDateString('es-ES')}
                </div>
              )}
              {prospect.next_contact_at && (
                <div>
                  <span className="font-medium">Próximo contacto:</span> {new Date(prospect.next_contact_at).toLocaleDateString('es-ES')}
                </div>
              )}
            </div>

            <select
              value={prospect.status}
              onChange={e => handleStatusChange(e.target.value)}
              disabled={isUpdating}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {Object.entries(statusLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Right: Email Draft */}
        <div className="lg:col-span-2 space-y-4">
          {prospect.draft_subject && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Borrador de email</h2>

              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-600 mb-2">Asunto</div>
                  <div className="px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 font-medium text-gray-900">
                    {prospect.draft_subject}
                  </div>
                </div>

                <div>
                  <div className="text-sm text-gray-600 mb-2">Cuerpo</div>
                  <div className="px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 text-gray-900 whitespace-pre-wrap text-sm">
                    {prospect.draft_body}
                  </div>
                </div>

                {prospect.draft_channel && (
                  <div>
                    <div className="text-sm text-gray-600 mb-2">Canal</div>
                    <div className="px-3 py-1 bg-gray-100 rounded text-sm font-medium text-gray-900 inline-block">
                      {prospect.draft_channel === 'email' ? '📧 Email' : '🔗 LinkedIn'}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Historial de cadencia</h2>

            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                {prospect.touchpoints === 0
                  ? 'Sin contactos aún'
                  : `${prospect.touchpoints} contacto(s) realizado(s)`}
              </div>

              <div className="relative">
                <div className="space-y-3">
                  {[0, 3, 7, 14].map((day, i) => {
                    const isDone = prospect.touchpoints > i
                    return (
                      <div
                        key={day}
                        className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                          isDone
                            ? 'bg-green-50 border border-green-200'
                            : 'bg-gray-50 border border-gray-200'
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                            isDone
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {isDone ? '✓' : i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{cadenceInfo[day]}</div>
                          <div className="text-sm text-gray-500">Día {day}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Notes */}
          {prospect.notes && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="font-semibold text-blue-900 mb-2">Notas</h2>
              <p className="text-blue-800 text-sm whitespace-pre-wrap">{prospect.notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProspectDetail
