<script setup>
import { ref } from 'vue'
import { getSchedule, getVenues, formatDateHuman } from '../api'

const venues = ref([])
const loading = ref(true)
// текущий индекс фото по id зала: { [venueId]: number }
const photoIdx = ref({})
const expanded = ref(null)
const schedule = ref([])
const occLoading = ref(false)
const occDate = ref(new Date().toISOString().slice(0, 10))

function venuePhotos(v) {
  const list = Array.isArray(v.images) && v.images.length > 0 ? v.images : v.image ? [v.image] : []
  return list.filter(Boolean)
}

function currentPhotoIdx(v) {
  const idx = photoIdx.value[v.id] || 0
  const len = venuePhotos(v).length
  return len ? Math.min(idx, len - 1) : 0
}

function movePhoto(v, dir) {
  const len = venuePhotos(v).length
  if (!len) return
  const cur = currentPhotoIdx(v)
  photoIdx.value = { ...photoIdx.value, [v.id]: (cur + dir + len) % len }
}

async function toggle(v) {
  if (expanded.value === v.id) {
    expanded.value = null
    return
  }
  expanded.value = v.id
  occLoading.value = true
  try {
    schedule.value = await getSchedule(v.id, occDate.value)
  } finally {
    occLoading.value = false
  }
}

async function refreshSchedule() {
  if (expanded.value == null) return
  occLoading.value = true
  try {
    schedule.value = await getSchedule(expanded.value, occDate.value)
  } finally {
    occLoading.value = false
  }
}

getVenues()
  .then((data) => (venues.value = data))
  .finally(() => (loading.value = false))
</script>

<template>
  <div class="container section">
    <span class="eyebrow">Залы и цены</span>
    <h1>Площадки спорткомплекса</h1>

    <div v-if="loading" class="muted">Загрузка…</div>

    <div v-else class="venue-list">
      <div v-for="v in venues" :key="v.id" class="card venue">
        <div class="venue-row">
          <!-- Карусель фото: несколько снимков, листаются стрелками влево/вправо -->
          <div
            v-if="venuePhotos(v).length"
            class="venue-carousel"
            @wheel.extra="movePhoto(v, $event.deltaY > 0 ? 1 : -1)"
          >
            <img
              v-for="(p, i) in venuePhotos(v)"
              :key="p"
              :src="p"
              :alt="v.name"
              class="venue-photo"
              :class="{ active: i === currentPhotoIdx(v) }"
            />
            <template v-if="venuePhotos(v).length > 1">
              <button class="car-btn prev" aria-label="Предыдущее фото" @click="movePhoto(v, -1)">‹</button>
              <button class="car-btn next" aria-label="Следующее фото" @click="movePhoto(v, 1)">›</button>
              <span class="car-counter">{{ currentPhotoIdx(v) + 1 }} / {{ venuePhotos(v).length }}</span>
            </template>
          </div>
          <div class="venue-info">
            <h2>{{ v.name }}</h2>
            <p class="muted">{{ v.description }}</p>
            <div class="features">
              <span v-for="f in v.features" :key="f" class="feature">{{ f }}</span>
            </div>
            <div class="features" style="width:100%">
              <span v-for="f in v.features" :key="f" class="feature">{{ f }}</span>
              <span class="feature">до {{ v.capacity }} чел.</span>
            </div>
            <div class="venue-actions">
              <router-link :to="{ path: '/booking', query: { venue: v.slug } }" class="btn btn-primary">
                Забронировать
              </router-link>
              <button class="btn btn-outline" @click="toggle(v)">
                {{ expanded === v.id ? 'Скрыть расписание' : 'Занятость на дату' }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="expanded === v.id" class="occupancy">
          <div class="occ-head">
            <label>
              Дата:
              <input type="date" v-model="occDate" :min="new Date().toISOString().slice(0, 10)" @change="refreshSchedule" />
            </label>
            <span class="muted">{{ formatDateHuman(occDate) }}</span>
          </div>
          <div v-if="occLoading" class="muted">Загрузка расписания…</div>
          <div v-else-if="schedule.length === 0" class="success-text">
            На эту дату всё свободно — можно бронировать любое время 08:00–22:00!
          </div>
          <div v-else class="occ-slots">
            <div
              v-for="s in schedule"
              :key="s.start_time + s.end_time"
              class="occ-slot"
              :class="s.kind"
            >
              <span class="occ-time">{{ s.start_time }}–{{ s.end_time }}</span>
              <small>{{ s.label }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.venue-list { display: flex; flex-direction: column; gap: 26px; margin-top: 24px; }
.venue-row { display: grid; grid-template-columns: 340px 1fr; }
.venue-row img { width: 100%; height: 100%; min-height: 280px; object-fit: cover; }

/* карусель фото зала */
.venue-carousel { position: relative; height: 100%; min-height: 280px; overflow: hidden; }
.venue-photo {
  position: absolute; inset: 0;
  width: 100%; height: 100%; object-fit: cover;
  opacity: 0; transition: opacity 0.25s ease;
}
.venue-photo.active { opacity: 1; }
.car-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 38px; height: 38px; border-radius: 50%;
  border: none; cursor: pointer; font-size: 22px; line-height: 1;
  background: rgba(255, 255, 255, 0.9); color: var(--navy);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  display: flex; align-items: center; justify-content: center;
}
.car-btn:hover { background: #fff; }
.car-btn.prev { left: 10px; }
.car-btn.next { right: 10px; }
.car-counter {
  position: absolute; bottom: 10px; right: 12px;
  background: rgba(0, 0, 0, 0.55); color: #fff;
  border-radius: 999px; padding: 3px 10px; font-size: 12px; font-weight: 600;
}
.venue-info { padding: 22px 26px; }
.features { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 16px; }
.feature {
  background: #eef1f6;
  color: var(--navy);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 600;
}
.venue-actions { display: flex; gap: 12px; flex-wrap: wrap; }

.occupancy { border-top: 1px dashed var(--gray); padding: 18px 26px 24px; background: #fbfbfa; }
.occ-head { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; flex-wrap: wrap; }
.occ-head input { padding: 7px 10px; border: 1.5px solid var(--gray); border-radius: 8px; font: inherit; }
.occ-slots { display: flex; flex-wrap: wrap; gap: 10px; }
.occ-slot {
  border-radius: 10px;
  padding: 8px 14px;
  font-weight: 700;
  display: flex;
  flex-direction: column;
  font-size: 14px;
  min-width: 120px;
}
.occ-slot .occ-time { font-size: 14px; }
.occ-slot small {
  font-weight: 500;
  font-size: 11.5px;
  margin-top: 4px;
}
.occ-slot.free {
  background: #fff;
  color: var(--muted);
  border: 1px dashed var(--gray);
}
.occ-slot.free small { color: var(--muted); }
.occ-slot.occupied {
  background: #fde0e0;
  color: #8a1f1f;
  border: 1px solid #e9b3b3;
}
.occ-slot.occupied small { color: #a12626; }

@media (max-width: 820px) {
  .venue-row { grid-template-columns: 1fr; }
  .venue-carousel { height: 200px; min-height: 0; }
}
</style>
