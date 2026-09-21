<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, formatDateHuman, formatPrice, getVenues } from '../api'

const token = ref(localStorage.getItem('adminToken') || '')
const logged = ref(false)
const password = ref('')
const error = ref('')

const tab = ref('bookings') // bookings | venues

// ----- bookings -----
const bookings = ref([])
const stats = ref({ total: 0, pending: 0, confirmed: 0, revenue: 0 })
const filter = ref('all')
const loading = ref(false)

const filtered = computed(() =>
  filter.value === 'all' ? bookings.value : bookings.value.filter((b) => b.status === filter.value)
)

const statusLabels = {
  pending: 'Ожидает',
  confirmed: 'Подтверждена',
  cancelled: 'Отменена',
}

// ----- venues -----
const venues = ref([])
const venueEditing = ref(null) // объект зала или "new"
const venueForm = ref(emptyVenueForm())
const venueSaving = ref(false)
const venueError = ref('')
const uploading = ref(false)
const fileInput = ref(null)
const featureInput = ref('')

function emptyVenueForm() {
  return {
    name: '',
    description: '',
    capacity: 0,
    area_m2: 0,
    image: '',
    features: [],
    price_weekday: 0,
    price_weekend: 0,
    sort_order: 0,
  }
}

const venueTitle = computed(() =>
  venueEditing.value === 'new' ? 'Новый зал' : `Редактирование: ${venueForm.value.name}`
)

function authHeaders() {
  return { 'X-Admin-Token': token.value }
}

async function login() {
  error.value = ''
  localStorage.setItem('adminToken', password.value)
  token.value = password.value
  await load()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    bookings.value = await api('/api/admin/bookings', { headers: authHeaders() })
    stats.value = await api('/api/admin/stats', { headers: authHeaders() })
    venues.value = await api('/api/admin/venues', { headers: authHeaders() })
    logged.value = true
  } catch (e) {
    error.value = e.message
    logged.value = false
    localStorage.removeItem('adminToken')
  } finally {
    loading.value = false
  }
}

async function refreshStats() {
  stats.value = await api('/api/admin/stats', { headers: authHeaders() })
}

async function setStatus(b, status) {
  try {
    const updated = await api(`/api/admin/bookings/${b.id}/status`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify({ status }),
    })
    Object.assign(b, updated)
    await refreshStats()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(b) {
  if (!confirm(`Удалить бронь ${b.code}?`)) return
  try {
    await api(`/api/admin/bookings/${b.id}`, { method: 'DELETE', headers: authHeaders() })
    bookings.value = bookings.value.filter((x) => x.id !== b.id)
    await refreshStats()
  } catch (e) {
    error.value = e.message
  }
}

function startCreateVenue() {
  venueEditing.value = 'new'
  venueForm.value = emptyVenueForm()
  featureInput.value = ''
  venueError.value = ''
}

function startEditVenue(v) {
  venueEditing.value = v.id
  venueForm.value = { ...v }
  featureInput.value = ''
  venueError.value = ''
}

function cancelVenueForm() {
  venueEditing.value = null
  venueError.value = ''
}

function addFeature() {
  const f = featureInput.value.trim()
  if (!f) return
  if (!venueForm.value.features.includes(f)) venueForm.value.features.push(f)
  featureInput.value = ''
}

function removeFeature(f) {
  venueForm.value.features = venueForm.value.features.filter((x) => x !== f)
}

async function uploadImage(file) {
  if (!file) return
  uploading.value = true
  venueError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch('/api/admin/uploads', {
      method: 'POST',
      headers: { 'X-Admin-Token': token.value },
      body: fd,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Ошибка ${res.status}`)
    }
    const { path } = await res.json()
    venueForm.value.image = path
  } catch (e) {
    venueError.value = e.message
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function saveVenue() {
  venueSaving.value = true
  venueError.value = ''
  try {
    const body = JSON.stringify(venueForm.value)
    if (venueEditing.value === 'new') {
      const created = await api('/api/admin/venues', { method: 'POST', headers: authHeaders(), body })
      venues.value.push(created)
    } else {
      const updated = await api(`/api/admin/venues/${venueEditing.value}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body,
      })
      const idx = venues.value.findIndex((v) => v.id === updated.id)
      if (idx >= 0) venues.value.splice(idx, 1, updated)
    }
    venueEditing.value = null
  } catch (e) {
    venueError.value = e.message
  } finally {
    venueSaving.value = false
  }
}

async function removeVenue(v) {
  if (!confirm(`Удалить зал «${v.name}»?`)) return
  venueError.value = ''
  try {
    await api(`/api/admin/venues/${v.id}`, { method: 'DELETE', headers: authHeaders() })
    venues.value = venues.value.filter((x) => x.id !== v.id)
  } catch (e) {
    venueError.value = e.message
  }
}

onMounted(() => {
  if (token.value) load()
})
</script>

<template>
  <div class="container section">
    <span class="eyebrow">Для администраторов</span>
    <h1>Панель управления</h1>

    <!-- LOGIN -->
    <div v-if="!logged" class="card login-card">
      <h3>Вход</h3>
      <p class="muted">Введите админ-токен (по умолчанию: shakarim-admin)</p>
      <div class="field">
        <input v-model="password" type="password" placeholder="Токен" @keyup.enter="login" />
      </div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <button class="btn btn-primary" :disabled="!password || loading" @click="login">
        {{ loading ? 'Проверяем…' : 'Войти' }}
      </button>
    </div>

    <!-- DASHBOARD -->
    <template v-else>
      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'bookings' }" @click="tab = 'bookings'">
          Брони <span class="tab-count">{{ stats.total }}</span>
        </button>
        <button class="tab" :class="{ active: tab === 'venues' }" @click="tab = 'venues'">
          Залы <span class="tab-count">{{ venues.length }}</span>
        </button>
      </div>

      <!-- ===== BOOKINGS TAB ===== -->
      <div v-if="tab === 'bookings'">
        <div class="stats">
          <div class="card stat">
            <span class="muted">Всего броней</span>
            <strong>{{ stats.total }}</strong>
          </div>
          <div class="card stat">
            <span class="muted">Ожидают</span>
            <strong class="gold">{{ stats.pending }}</strong>
          </div>
          <div class="card stat">
            <span class="muted">Подтверждено</span>
            <strong class="ok">{{ stats.confirmed }}</strong>
          </div>
          <div class="card stat">
            <span class="muted">Ожидаемая выручка</span>
            <strong>{{ formatPrice(stats.revenue) }}</strong>
          </div>
        </div>

        <div class="toolbar">
          <select v-model="filter">
            <option value="all">Все статусы</option>
            <option value="pending">Ожидают</option>
            <option value="confirmed">Подтверждённые</option>
            <option value="cancelled">Отменённые</option>
          </select>
        </div>

        <div class="table-wrap card">
          <table>
            <thead>
              <tr>
                <th>Код</th>
                <th>Зал</th>
                <th>Дата / время</th>
                <th>Клиент</th>
                <th>Сумма</th>
                <th>Статус</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in filtered" :key="b.id">
                <td><router-link :to="`/booking/${b.code}`" class="code">{{ b.code }}</router-link></td>
                <td>{{ b.venue_name }}</td>
                <td>
                  {{ formatDateHuman(b.date) }}<br />
                  <small class="muted">{{ b.start_time }}–{{ b.end_time }}</small>
                </td>
                <td>
                  {{ b.customer_name }}<br />
                  <small class="muted">{{ b.phone }}</small>
                </td>
                <td>{{ formatPrice(b.total_price) }}</td>
                <td><span class="badge" :class="`badge-${b.status}`">{{ statusLabels[b.status] || b.status }}</span></td>
                <td class="actions">
                  <button v-if="b.status !== 'confirmed'" class="btn btn-sm btn-primary" @click="setStatus(b, 'confirmed')">✓</button>
                  <button v-if="b.status !== 'cancelled'" class="btn btn-sm btn-outline" @click="setStatus(b, 'cancelled')">✕</button>
                  <button class="btn btn-sm btn-danger" @click="remove(b)">🗑</button>
                </td>
              </tr>
              <tr v-if="filtered.length === 0">
                <td colspan="7" class="muted">Броней нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ===== VENUES TAB ===== -->
      <div v-else>
        <div v-if="venueEditing === null">
          <div class="toolbar venues-toolbar">
            <button class="btn btn-gold" @click="startCreateVenue">+ Добавить зал</button>
          </div>

          <div v-if="venueError" class="alert alert-error">{{ venueError }}</div>

          <div class="table-wrap card">
            <table>
              <thead>
                <tr>
                  <th>Фото</th>
                  <th>Название</th>
                  <th>Цены (будни / вых.)</th>
                  <th>Вместимость</th>
                  <th>Площадь</th>
                  <th>Порядок</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in venues" :key="v.id">
                  <td><img :src="v.image" :alt="v.name" class="venue-thumb" /></td>
                  <td>
                    <strong>{{ v.name }}</strong><br />
                    <small class="muted">/{{ v.slug }}</small>
                  </td>
                  <td>{{ formatPrice(v.price_weekday) }} / {{ formatPrice(v.price_weekend) }}</td>
                  <td>до {{ v.capacity }} чел.</td>
                  <td>{{ v.area_m2 }} м²</td>
                  <td>{{ v.sort_order }}</td>
                  <td class="actions">
                    <button class="btn btn-sm btn-primary" @click="startEditVenue(v)">✎</button>
                    <button class="btn btn-sm btn-danger" @click="removeVenue(v)">🗑</button>
                  </td>
                </tr>
                <tr v-if="venues.length === 0">
                  <td colspan="7" class="muted">Залов пока нет</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- venue edit/create form -->
        <div v-else class="card venue-form">
          <h3>{{ venueTitle }}</h3>
          <div v-if="venueError" class="alert alert-error">{{ venueError }}</div>

          <div class="grid-3">
            <div class="field">
              <label>Название *</label>
              <input v-model="venueForm.name" placeholder="Универсальный зал" />
            </div>
            <div class="field">
              <label>Цена будни, ₸/час *</label>
              <input v-model.number="venueForm.price_weekday" type="number" min="0" />
            </div>
            <div class="field">
              <label>Цена выходные, ₸/час *</label>
              <input v-model.number="venueForm.price_weekend" type="number" min="0" />
            </div>
            <div class="field">
              <label>Вместимость, чел.</label>
              <input v-model.number="venueForm.capacity" type="number" min="0" />
            </div>
            <div class="field">
              <label>Площадь, м²</label>
              <input v-model.number="venueForm.area_m2" type="number" min="0" />
            </div>
            <div class="field">
              <label>Порядок сортировки</label>
              <input v-model.number="venueForm.sort_order" type="number" min="0" />
            </div>
          </div>

          <div class="field">
            <label>Описание</label>
            <textarea v-model="venueForm.description" rows="3" placeholder="Кратко о зале, покрытии, оснащении…"></textarea>
          </div>

          <div class="field">
            <label>Особенности (добавляйте по одной)</label>
            <div class="feature-add">
              <input v-model="featureInput" placeholder="Например: Трибуны" @keyup.enter="addFeature" />
              <button class="btn btn-outline" @click="addFeature">+ Добавить</button>
            </div>
            <div class="features">
              <span v-for="f in venueForm.features" :key="f" class="feature" @click="removeFeature(f)">
                {{ f }} ✕
              </span>
              <span v-if="venueForm.features.length === 0" class="muted small-note">Пока нет</span>
            </div>
          </div>

          <div class="field">
            <label>Фото зала</label>
            <div class="image-row">
              <img v-if="venueForm.image" :src="venueForm.image" alt="Фото зала" class="venue-preview" />
              <div class="image-actions">
                <input ref="fileInput" type="file" accept="image/*" class="visually-hidden" @change="uploadImage($event.target.files[0])" />
                <button class="btn btn-outline" :disabled="uploading" @click="fileInput?.click()">
                  {{ uploading ? 'Загружаем…' : '📷 Загрузить фото' }}
                </button>
                <input v-model="venueForm.image" placeholder="/images/… или URL" />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-primary" :disabled="venueSaving || !venueForm.name" @click="saveVenue">
              {{ venueSaving ? 'Сохраняем…' : 'Сохранить' }}
            </button>
            <button class="btn btn-outline" @click="cancelVenueForm">Отмена</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.login-card { max-width: 420px; padding: 24px 28px; margin-top: 18px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }
.stat { padding: 18px 20px; display: flex; flex-direction: column; }
.stat strong { font-size: 26px; color: var(--navy); }
.stat .ok { color: #1f7a4d; }
.toolbar { margin-bottom: 14px; }
.toolbar select { padding: 9px 12px; border: 1.5px solid var(--gray); border-radius: 10px; font: inherit; }
.venues-toolbar { display: flex; justify-content: flex-end; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14.5px; }
th, td { text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--gray); vertical-align: top; }
th { color: var(--muted); font-size: 12.5px; text-transform: uppercase; letter-spacing: 0.05em; }
.code { font-weight: 700; color: var(--navy); }
.actions { white-space: nowrap; }
.actions .btn { margin-right: 6px; }
.btn-danger { background: #fbe4e4; color: #a33; border: none; }

/* tabs */
.tabs { display: flex; gap: 8px; margin: 18px 0 4px; border-bottom: 2px solid var(--gray); }
.tab {
  background: none; border: none; padding: 10px 18px; font: inherit; font-weight: 700;
  color: var(--muted); cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px;
}
.tab.active { color: var(--navy); border-bottom-color: var(--gold); }
.tab-count { font-size: 12px; background: var(--bg); border-radius: 999px; padding: 2px 8px; margin-left: 4px; }

/* venues */
.venue-thumb { width: 74px; height: 50px; object-fit: cover; border-radius: 8px; }
.venue-form { padding: 22px 26px; margin-top: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
.feature-add { display: flex; gap: 8px; }
.feature-add input { flex: 1; }
.features { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.feature { background: #eef1f6; color: var(--navy); border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 600; cursor: pointer; }
.small-note { font-size: 13px; }
.image-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.venue-preview { width: 180px; height: 110px; object-fit: cover; border-radius: 10px; }
.image-actions { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 220px; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.form-actions { display: flex; gap: 12px; margin-top: 18px; }
textarea { width: 100%; font: inherit; padding: 10px 12px; border: 1.5px solid var(--gray); border-radius: 10px; resize: vertical; }
</style>
