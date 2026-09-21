const BASE = ''

export async function api(path, options = {}) {
  const { headers, ...rest } = options
  const res = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
  })
  if (!res.ok) {
    let detail = `Ошибка ${res.status}`
    try {
      const data = await res.json()
      if (Array.isArray(data.detail)) {
        detail = data.detail.map((d) => d.msg).join('; ')
      } else if (typeof data.detail === 'string') {
        detail = data.detail
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export function getVenues() {
  return api('/api/venues')
}

export function getVenue(slug) {
  return api(`/api/venues/${slug}`)
}

export function getOccupied(venueId, date) {
  return api(`/api/bookings/occupied?venue_id=${venueId}&date=${date}`)
}

export function createBooking(payload) {
  return api('/api/bookings', { method: 'POST', body: JSON.stringify(payload) })
}

export function getBooking(code) {
  return api(`/api/bookings/${code}`)
}

export function formatPrice(value) {
  return new Intl.NumberFormat('ru-RU').format(value) + ' ₸'
}

export function formatDateHuman(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
}
