import { useEffect, useState } from 'react'
import { fetchProspects, updateProspectStatus, updateProspectDraft } from '../lib/supabase'

function SendQueue() {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editSubject, setEditSubject] = useState('')
  const [editBody, setEditBody] = useState('')

  useEffect(() => {
    loadQueue()
  }, [])

  const loadQueue = async () => {
    try {
      setLoading(true)
      const data = await fetchProspects({ status: 'drafted' })
      setQueue(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (item) => {
    setEditingId(item.id)
    setEditSubject(item.draft_subject)
    setEditBody(item.draft_body)
  }

  const handleSave = async (id) => {
    try {
      await updateProspectDraft(id, editSubject, editBody)
      setEditingId(null)
      loadQueue()
    } catch (err) {
      alert('Error: ' + err.message)
    }
  }

  const handleApprove = async (id) => {
    try {
      await updateProspectStatus(id, 'sent')
      loadQueue()
    } catch (err) {
      alert('Error: ' + err.message)
    }
  }

  const handleDiscard = async (id) => {
    if (!confirm('¿Descartar este borrador?')) return
    try {
      await updateProspectStatus(id, 'new')
      loadQueue()
    } catch (err) {
      alert('Error: ' + err.message)
    }
  }

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

  if (queue.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
        No hay borradores pendientes
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Cola de envío</h1>
        <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
          {queue.length} pendientes
        </div>
      </div>

      <div className="space-y-4">
        {queue.map(item => (
          <div key={item.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">
                  {item.first_name} {item.last_name}
                </h3>
                <div className="text-sm text-gray-600">{item.company_name} · {item.job_title}</div>
              </div>
              <div className="text-right text-sm text-gray-600">
                <div>{item.email}</div>
                <div className="font-semibold text-gray-900">
                  {item.product_target === 'shieldai' ? 'ShieldAI' : '2laps'}
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {editingId === item.id ? (
                // Edit Mode
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Asunto</label>
                    <input
                      type="text"
                      value={editSubject}
                      onChange={e => setEditSubject(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Cuerpo</label>
                    <textarea
                      value={editBody}
                      onChange={e => setEditBody(e.target.value)}
                      rows="8"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    />
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSave(item.id)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
                    >
                      Guardar cambios
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-300"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : (
                // View Mode
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-2 font-medium">Asunto</div>
                    <div className="px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 text-gray-900">
                      {item.draft_subject}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-gray-600 mb-2 font-medium">Cuerpo</div>
                    <div className="px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 text-gray-900 whitespace-pre-wrap text-sm max-h-48 overflow-y-auto">
                      {item.draft_body}
                    </div>
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => handleApprove(item.id)}
                      className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600"
                    >
                      ✓ Aprobar y enviar
                    </button>
                    <button
                      onClick={() => handleEdit(item)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600"
                    >
                      ✏️ Editar
                    </button>
                    <button
                      onClick={() => handleDiscard(item.id)}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200"
                    >
                      🗑️ Descartar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SendQueue
