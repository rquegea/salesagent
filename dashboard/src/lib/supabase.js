import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://nnehagxifkhhkmnejbwk.supabase.co'
const supabaseAnonKey = 'sb_publishable_lLFlFlt8dOH8n3Lk07pDhA_2NyJc'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const fetchProspects = async (filters = {}) => {
  let query = supabase.from('prospects').select('*')

  if (filters.status) {
    query = query.eq('status', filters.status)
  }
  if (filters.product) {
    query = query.eq('product_target', filters.product)
  }
  if (filters.search) {
    query = query.or(
      `first_name.ilike.%${filters.search}%,last_name.ilike.%${filters.search}%,company_name.ilike.%${filters.search}%,email.ilike.%${filters.search}%`
    )
  }

  const { data, error } = await query.order('created_at', { ascending: false })

  if (error) throw error
  return data
}

export const fetchProspectById = async (id) => {
  const { data, error } = await supabase
    .from('prospects')
    .select('*')
    .eq('id', id)
    .single()

  if (error) throw error
  return data
}

export const updateProspectStatus = async (id, status) => {
  const { error } = await supabase
    .from('prospects')
    .update({ status, updated_at: new Date() })
    .eq('id', id)

  if (error) throw error
}

export const updateProspectDraft = async (id, subject, body) => {
  const { error } = await supabase
    .from('prospects')
    .update({ draft_subject: subject, draft_body: body, updated_at: new Date() })
    .eq('id', id)

  if (error) throw error
}

export const getProspectsStats = async () => {
  const { data, error } = await supabase.from('prospects').select('status, product_target, created_at')

  if (error) throw error

  const stats = {
    total: data.length,
    new: data.filter(p => p.status === 'new').length,
    drafted: data.filter(p => p.status === 'drafted').length,
    sent: data.filter(p => p.status === 'sent').length,
    replied: data.filter(p => p.status === 'replied').length,
    shieldai: data.filter(p => p.product_target === 'shieldai').length,
    twolaps: data.filter(p => p.product_target === 'twolaps').length,
  }

  // Calculate response rate
  const contacted = data.filter(p => ['sent', 'followed_up_1', 'followed_up_2', 'replied', 'meeting', 'closed'].includes(p.status))
  stats.responseRate = contacted.length > 0 ? ((stats.replied / contacted.length) * 100).toFixed(1) : 0

  // Activity by day (last 7 days)
  const today = new Date()
  const activityByDay = {}
  for (let i = 0; i < 7; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    activityByDay[dateStr] = data.filter(p => p.created_at?.startsWith(dateStr)).length
  }

  stats.activityByDay = activityByDay

  return stats
}
