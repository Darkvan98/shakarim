<script setup>
import { ref } from 'vue'
import { getVenues, getOccupied, formatDateHuman, formatPrice } from '../api'

const venues = ref([])
const loading = ref(true)
const expanded = ref(null)
const occupied = ref([])
const occLoading = ref(false)
const occDate = ref(new Date().toISOString().slice(0, 10))

async function toggle(v) {
  if (expanded.value === v.id) {
    expanded.value = null
    return
  }
  expanded.value = v.id
  occLoading.value = true
  try {
    occupied.value = await getOccupied(v.id, occDate.value)
  } finally {
    occLoading.value = false
  }
}

async function refreshOccupied() {
  if (expanded.value == null) return
  occLoading.value = true
  try {
    occupied.value = await getOccupied(expanded.value, occDate.value)
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
    <p class="lead">
      Стоимость указана за час аренды: в будни и в выходные. В цену входит уборка после занятия.
    </p>

    <div v-if="loading" class="muted">Загрузка…</div>

    <div v-else class="venue-list">
      <div v-for="v in venues" :key="v.id" class="card venue">
        <div class="venue-row">
          <img :src="v.image" :alt="v.name" />
          <div class="venue-info">
            <h2>{{ v.name }}</h2>
            <p class="muted">{{ v.description }}</p>
            <div class="features">
              <span v-for="f in v.features" :key="f" class="feature">{{ f }}</span>
            </div>
            <div class="prices">
              <div class="price-box">
                <small>Будни (пн–пт)</small>
                <strong>{{ formatPrice(v.price_weekday) }}/час</strong>
              </div>
              <div class="price-box">
                <small>Выходные (сб–вс)</small>
                <strong>{{ formatPrice(v.price_weekend) }}/час</strong>
              </div>
              <div class="price-box">
                <small>Вместимость</small>
                <strong>до {{ v.capacity }} чел.</strong>
              </div>
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
              <input type="date" v-model="occDate" :min="new Date().toISOString().slice(0, 10)" @change="refreshOccupied" />
            </label>
            <span class="muted">{{ formatDateHuman(occDate) }}</span>
          </div>
          <div v-if="occLoading" class="muted">Загрузка расписания…</div>
          <div v-else-if="occupied.length === 0" class="success-text">
            На эту дату всё свободно — можно бронировать любое время 08:00–22:00!
          </div>
          <div v-else class="occ-slots">
            <div v-for="s in occupied" :key="s.start_time" class="occ-slot" :class="s.status">
              {{ s.start_time }}–{{ s.end_time }}
              <small>{{ s.status === 'pending' ? 'ожидает подтверждения' : 'подтверждено' }}</small>
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
.prices { display: flex; gap: 18px; flex-wrap: wrap; margin-bottom: 18px; }
.price-box {
  background: var(--bg);
  border: 1px solid var(--gray);
  border-radius: 10px;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
}
.price-box small { color: var(--muted); }
.price-box strong { color: var(--navy); font-size: 17px; }
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
}
.occ-slot small { font-weight: 500; font-size: 11.5px; }
.occ-slot.pending { background: #fdf3d7; color: #8a6d1a; }
.occ-slot.confirmed { background: #fbe4e4; color: #8a2020; }

@media (max-width: 820px) {
  .venue-row { grid-template-columns: 1fr; }
  .venue-row img { height: 200px; min-height: 0; }
}
</style>
