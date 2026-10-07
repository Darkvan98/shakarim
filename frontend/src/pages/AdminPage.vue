<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, formatDateHuman, getVenues } from '../api'

// ----- gallery -----
const gallery = ref([])
const galleryEditing = ref(null) // id группы или 'new'
const galleryForm = ref(emptyGalleryForm())
const gallerySaving = ref(false)
const galleryError = ref('')
const galleryPhotoInput = ref('')
const galleryFileInputs = ref({})
const galleryUploading = ref('') // src фото, которое сейчас грузится, или ''

function emptyGalleryForm() {
  return { title: '', subtitle: '', photos: [], sort_order: 0 }
}

function startCreateGallery() {
  const maxOrder = gallery.value.reduce((m, g) => Math.max(m, g.sort_order), 0)
  galleryForm.value = { ...emptyGalleryForm(), sort_order: maxOrder + 1 }
  galleryEditing.value = 'new'
  galleryError.value = ''
}

function startEditGallery(g) {
  galleryForm.value = { title: g.title, subtitle: g.subtitle, photos: [...g.photos], sort_order: g.sort_order }
  galleryEditing.value = g.id
  galleryError.value = ''
}

function cancelGalleryForm() {
  galleryEditing.value = null
  galleryError.value = ''
}

function addGalleryPhoto() {
  const src = galleryPhotoInput.value.trim()
  if (!src) return
  if (!galleryForm.value.photos.includes(src)) galleryForm.value.photos.push(src)
  galleryPhotoInput.value = ''
}

function removeGalleryPhoto(src) {
  galleryForm.value.photos = galleryForm.value.photos.filter((p) => p !== src)
}

function moveGalleryPhoto(idx, dir) {
  const photos = galleryForm.value.photos
  const target = idx + dir
  if (target < 0 || target >= photos.length) return
  ;[photos[idx], photos[target]] = [photos[target], photos[idx]]
}

async function uploadGalleryPhoto(file) {
  if (!file) return
  galleryUploading.value = 'file'
  galleryError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch('/api/admin/uploads', {
      method: 'POST',
      headers: authHeaders(),
      body: fd,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Ошибка ${res.status}`)
    }
    const { path } = await res.json()
    galleryForm.value.photos.push(path)
  } catch (e) {
    galleryError.value = e.message
  } finally {
    galleryUploading.value = ''
  }
}

async function replaceGalleryPhoto(idx, file) {
  if (!file) return
  galleryUploading.value = galleryForm.value.photos[idx]
  galleryError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch('/api/admin/uploads', {
      method: 'POST',
      headers: authHeaders(),
      body: fd,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Ошибка ${res.status}`)
    }
    const { path } = await res.json()
    galleryForm.value.photos.splice(idx, 1, path)
  } catch (e) {
    galleryError.value = e.message
  } finally {
    galleryUploading.value = ''
  }
}

async function saveGallery() {
  gallerySaving.value = true
  galleryError.value = ''
  try {
    const body = JSON.stringify(galleryForm.value)
    if (galleryEditing.value === 'new') {
      const created = await api('/api/admin/gallery', { method: 'POST', headers: authHeaders(), body })
      gallery.value.push(created)
    } else {
      const updated = await api(`/api/admin/gallery/${galleryEditing.value}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body,
      })
      const idx = gallery.value.findIndex((g) => g.id === updated.id)
      if (idx >= 0) gallery.value.splice(idx, 1, updated)
    }
    galleryEditing.value = null
  } catch (e) {
    galleryError.value = e.message
  } finally {
    gallerySaving.value = false
  }
}

async function removeGalleryGroup(g) {
  if (!confirm(`Удалить группу «${g.title}» вместе со всеми её фото из галереи?`)) return
  galleryError.value = ''
  try {
    await api(`/api/admin/gallery/${g.id}`, { method: 'DELETE', headers: authHeaders() })
    gallery.value = gallery.value.filter((x) => x.id !== g.id)
  } catch (e) {
    galleryError.value = e.message
  }
}

function triggerGalleryFile(idx) {
  galleryFileInputs.value[idx]?.click()
}

const token = ref(localStorage.getItem('adminToken') || '')
const logged = ref(false)
const username = ref('')
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
    sports_complex: '',
    description: '',
    capacity: 0,
    area_m2: 0,
    image: '',
    features: [],
    sort_order: 0,
  }
}

const venueTitle = computed(() =>
  venueEditing.value === 'new' ? 'Новый зал' : `Редактирование: ${venueForm.value.name}`
)

function authHeaders() {
  return { Authorization: `Bearer ${token.value}` }
}

async function login() {
  error.value = ''
  loading.value = true
  try {
    const { token: sessionToken } = await api('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    })
    token.value = sessionToken
    localStorage.setItem('adminToken', sessionToken)
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function logout() {
  token.value = ''
  logged.value = false
  localStorage.removeItem('adminToken')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    bookings.value = await api('/api/admin/bookings', { headers: authHeaders() })
    stats.value = await api('/api/admin/stats', { headers: authHeaders() })
    venues.value = await api('/api/admin/venues', { headers: authHeaders() })
    gallery.value = await api('/api/gallery')
    logged.value = true
  } catch (e) {
    error.value = e.message
    logged.value = false
    if (!username.value) {
      // протухшая сессия — покажем форму входа
      localStorage.removeItem('adminToken')
      token.value = ''
    }
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
      headers: authHeaders(),
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

// ----- blocks (ручная занятость) -----
const blockVenueId = ref(null)
const blockDate = ref(new Date().toISOString().slice(0, 10))
const blocks = ref([])
const blockForm = ref(emptyBlockForm())
const blockSaving = ref(false)
const blockError = ref('')
const blocksLoading = ref(false)

function emptyBlockForm() {
  return { start_time: '08:00', end_time: '09:00', label: '' }
}

function openBlocksTab() {
  tab.value = 'blocks'
  if (!blockVenueId.value && venues.value.length) {
    blockVenueId.value = venues.value[0].id
  }
  if (blockVenueId.value) loadBlocks()
}

function openBlocksForVenue(venueId) {
  venueEditing.value = null
  tab.value = 'blocks'
  blockVenueId.value = venueId
  loadBlocks()
}

async function loadBlocks() {
  if (!blockVenueId.value) return
  blocksLoading.value = true
  blockError.value = ''
  try {
    blocks.value = await api(`/api/admin/venues/${blockVenueId.value}/blocks?date=${blockDate.value}`, {
      headers: authHeaders(),
    })
  } catch (e) {
    blockError.value = e.message
  } finally {
    blocksLoading.value = false
  }
}

async function addBlock() {
  blockSaving.value = true
  blockError.value = ''
  try {
    await api(`/api/admin/venues/${blockVenueId.value}/blocks`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ date: blockDate.value, ...blockForm.value }),
    })
    blockForm.value = emptyBlockForm()
    await loadBlocks()
  } catch (e) {
    blockError.value = e.message
  } finally {
    blockSaving.value = false
  }
}

async function removeBlock(blk) {
  if (!confirm(`Убрать блокировку ${blk.start_time}–${blk.end_time}?`)) return
  blockError.value = ''
  try {
    await api(`/api/admin/blocks/${blk.id}`, { method: 'DELETE', headers: authHeaders() })
    blocks.value = blocks.value.filter((x) => x.id !== blk.id)
  } catch (e) {
    blockError.value = e.message
  }
}

onMounted(() => {
  if (token.value) load()
})
</script>

<template>
  <div class="container section">
    <h1>Панель управления</h1>

    <!-- LOGIN -->
    <div v-if="!logged" class="card login-card">
      <h3>Вход</h3>
      <p class="muted">Введите логин и пароль администратора</p>
      <div class="field">
        <label>Логин</label>
        <input v-model="username" autocomplete="username" placeholder="admin" @keyup.enter="login" />
      </div>
      <div class="field">
        <label>Пароль</label>
        <input v-model="password" type="password" autocomplete="current-password" placeholder="••••••••" @keyup.enter="login" />
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <button class="btn btn-primary" :disabled="!username || !password || loading" @click="login">
        {{ loading ? 'Проверяем…' : 'Войти' }}
      </button>
    </div>

    <!-- DASHBOARD -->
    <template v-else>
      <div class="toolbar admin-logout-row">

        <button class="btn btn-outline btn-sm" @click="logout">Выйти</button>
      </div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'bookings' }" @click="tab = 'bookings'">
          Брони <span class="tab-count">{{ stats.total }}</span>
        </button>
        <button class="tab" :class="{ active: tab === 'venues' }" @click="tab = 'venues'">
          Залы <span class="tab-count">{{ venues.length }}</span>
        </button>
        <button class="tab" :class="{ active: tab === 'blocks' }" @click="openBlocksTab">
          Занятость
        </button>
        <button class="tab" :class="{ active: tab === 'gallery' }" @click="tab = 'gallery'">
          Галерея <span class="tab-count">{{ gallery.length }}</span>
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
      <div v-else-if="tab === 'venues'">
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
                  <th>Спорткомплекс</th>
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
                  <td>{{ v.sports_complex || '—' }}</td>
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

          <div class="grid-2">
            <div class="field">
              <label>Название (необязательно)</label>
              <input v-model="venueForm.name" placeholder="Универсальный зал" />
            </div>
            <div class="field">
              <label>Какой это спорткомплекс</label>
              <input v-model="venueForm.sports_complex" placeholder="например: Шакарим" />
            </div>
          </div>
          <div class="grid-2">
            <div class="field">
              <label>Вместимость, чел.</label>
              <input v-model.number="venueForm.capacity" type="number" min="0" />
            </div>
            <div class="field">
              <label>Площадь, м²</label>
              <input v-model.number="venueForm.area_m2" type="number" min="0" />
            </div>
          </div>
          <div class="grid-2">
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
            <button class="btn btn-primary" :disabled="venueSaving" @click="saveVenue">
              {{ venueSaving ? 'Сохраняем…' : 'Сохранить' }}
            </button>
            <button v-if="venueEditing !== 'new'" class="btn btn-outline" @click="openBlocksForVenue(venueEditing)">
              📅 Занятость зала
            </button>
            <button class="btn btn-outline" @click="cancelVenueForm">Отмена</button>
          </div>
        </div>
      </div>

      <!-- ===== OCCUPANCY (BLOCKS) TAB ===== -->
      <div v-else-if="tab === 'blocks'">
        <div class="grid-3">
          <div class="field">
            <label>Зал</label>
            <select v-model.number="blockVenueId" @change="loadBlocks">
              <option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name || v.slug }}</option>
            </select>
          </div>
          <div class="field">
            <label>Дата</label>
            <input v-model="blockDate" type="date" @change="loadBlocks" />
          </div>
        </div>

        <div v-if="blockError" class="alert alert-error">{{ blockError }}</div>

        <div v-if="blockVenueId" class="card venue-form">
          <h3>Заблокировать время</h3>
          <p class="muted small-note">
            Заблокированное время будет недоступно для бронирования и покажется как занято в расписании.
          </p>
          <div class="grid-3">
            <div class="field">
              <label>С</label>
              <input v-model="blockForm.start_time" type="time" />
            </div>
            <div class="field">
              <label>До</label>
              <input v-model="blockForm.end_time" type="time" />
            </div>
            <div class="field">
              <label>Кем занято</label>
              <input v-model="blockForm.label" placeholder="Например: Соревнования, секция…" @keyup.enter="addBlock" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="blockSaving" @click="addBlock">
              {{ blockSaving ? 'Сохраняем…' : '🔒 Заблокировать' }}
            </button>
          </div>
        </div>

        <div v-if="blockVenueId" class="table-wrap card">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Время</th>
                <th>Кем занято</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="blk in blocks" :key="blk.id">
                <td>{{ formatDateHuman(blk.date) }}</td>
                <td>{{ blk.start_time }}–{{ blk.end_time }}</td>
                <td>{{ blk.label || '—' }}</td>
                <td class="actions">
                  <button class="btn btn-sm btn-danger" @click="removeBlock(blk)">🗑</button>
                </td>
              </tr>
              <tr v-if="!blocksLoading && blocks.length === 0">
                <td colspan="4" class="muted">Блокировок на эту дату нет</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="venues.length === 0" class="muted">Сначала создайте зал</div>
      </div>

      <!-- ===== GALLERY TAB ===== -->
      <div v-else-if="tab === 'gallery'">
        <div v-if="galleryEditing === null">
          <div class="toolbar venues-toolbar">
            <button class="btn btn-gold" @click="startCreateGallery">+ Добавить группу</button>
          </div>

          <div v-if="galleryError" class="alert alert-error">{{ galleryError }}</div>

          <div class="gallery-admin-list">
            <div v-for="g in gallery" :key="g.id" class="card gallery-admin-card">
              <div class="gallery-admin-head">
                <div>
                  <strong>{{ g.title }}</strong>
                  <small class="muted"> {{ g.subtitle }}</small>
                </div>
                <div class="actions">
                  <span class="muted small-note">порядок: {{ g.sort_order }}</span>
                  <button class="btn btn-sm btn-primary" @click="startEditGallery(g)">✎</button>
                  <button class="btn btn-sm btn-danger" @click="removeGalleryGroup(g)">🗑</button>
                </div>
              </div>
              <div class="gallery-admin-photos">
                <img v-for="src in g.photos" :key="src" :src="src" :alt="g.title" />
              </div>
            </div>
            <div v-if="gallery.length === 0" class="muted">Групп пока нет</div>
          </div>
        </div>

        <!-- gallery edit/create form -->
        <div v-else class="card venue-form">
          <h3>{{ galleryEditing === 'new' ? 'Новая группа фото' : `Редактирование: ${galleryForm.title}` }}</h3>
          <div v-if="galleryError" class="alert alert-error">{{ galleryError }}</div>

          <div class="grid-3">
            <div class="field">
              <label>Заголовок *</label>
              <input v-model="galleryForm.title" placeholder="Спорткомплекс 1" />
            </div>
            <div class="field">
              <label>Подпись</label>
              <input v-model="galleryForm.subtitle" placeholder="первые 2 фото" />
            </div>
            <div class="field">
              <label>Порядок сортировки</label>
              <input v-model.number="galleryForm.sort_order" type="number" min="0" />
            </div>
          </div>

          <div class="field">
            <label>Фотографии группы</label>
            <div class="gallery-edit-photos">
              <div v-for="(src, idx) in galleryForm.photos" :key="`${src}-${idx}`" class="gallery-edit-item">
                <img :src="src" alt="Фото группы" />
                <div class="gallery-edit-controls">
                  <button class="btn btn-sm btn-outline" :disabled="idx === 0" @click="moveGalleryPhoto(idx, -1)">←</button>
                  <button class="btn btn-sm btn-outline" :disabled="idx === galleryForm.photos.length - 1" @click="moveGalleryPhoto(idx, 1)">→</button>
                  <input
                    ref="galleryFileInputs"
                    type="file"
                    accept="image/*"
                    class="visually-hidden"
                    @change="replaceGalleryPhoto(idx, $event.target.files[0]); $event.target.value = ''"
                  />
                  <button class="btn btn-sm btn-outline" :disabled="galleryUploading !== ''" @click="triggerGalleryFile(idx)">
                    {{ galleryUploading === galleryForm.photos[idx] ? '…' : '📷' }}
                  </button>
                  <button class="btn btn-sm btn-danger" @click="removeGalleryPhoto(src)">✕</button>
                </div>
              </div>
              <div v-if="galleryForm.photos.length === 0" class="muted small-note">Фото пока нет</div>
            </div>

            <div class="gallery-add-row">
              <input v-model="galleryPhotoInput" placeholder="/images/gallery/… или URL" @keyup.enter="addGalleryPhoto" />
              <button class="btn btn-outline" @click="addGalleryPhoto">+ Добавить путь</button>
              <input
                type="file"
                accept="image/*"
                class="visually-hidden"
                @change="uploadGalleryPhoto($event.target.files[0]); $event.target.value = ''"
              />
              <button class="btn btn-outline" :disabled="galleryUploading !== ''" @click="$event.currentTarget.previousElementSibling.click()">
                {{ galleryUploading === 'file' ? 'Загружаем…' : '📷 Загрузить файл' }}
              </button>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-primary" :disabled="gallerySaving || !galleryForm.title" @click="saveGallery">
              {{ gallerySaving ? 'Сохраняем…' : 'Сохранить' }}
            </button>
            <button class="btn btn-outline" @click="cancelGalleryForm">Отмена</button>
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

.admin-logout-row { display: flex; justify-content: flex-end; align-items: center; gap: 12px; }
.daily-code-chip {
  background: var(--bg);
  border: 1px solid var(--gray);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13.5px;
  margin-right: auto;
}
.daily-code-chip strong { color: var(--navy); letter-spacing: 0.08em; }

/* gallery admin */
.gallery-admin-list { display: flex; flex-direction: column; gap: 16px; margin-top: 6px; }
.gallery-admin-card { padding: 16px 20px; }
.gallery-admin-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.gallery-admin-head strong { color: var(--navy); }
.gallery-admin-photos { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.gallery-admin-photos img { width: 100%; height: 100px; object-fit: cover; border-radius: 8px; }
.gallery-edit-photos { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.gallery-edit-item { width: 170px; }
.gallery-edit-item img { width: 100%; height: 110px; object-fit: cover; border-radius: 8px; display: block; }
.gallery-edit-controls { display: flex; gap: 4px; margin-top: 6px; }
.gallery-edit-controls .btn { padding: 4px 8px; }
.gallery-add-row { display: flex; gap: 8px; flex-wrap: wrap; }
.gallery-add-row input { flex: 1; min-width: 220px; }

.notfound { text-align: center; padding: 80px 20px; }
.notfound h1 { font-size: 72px; margin: 0; color: var(--navy); }
</style>
