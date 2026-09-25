<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createBooking, formatDateHuman, formatPrice, getOccupied, getVenues } from '../api'

const OPEN_HOUR = 8
const CLOSE_HOUR = 22

const route = useRoute()
const router = useRouter()

const venues = ref([])
const venueId = ref(null)
const dateStr = ref(new Date().toISOString().slice(0, 10))
const hours = ref(2)
const start = ref('18:00')
const name = ref('')
const phone = ref('')
const comment = ref('')

const occupied = ref([])
const loadingSlots = ref(false)
const submitting = ref(false)
const error = ref('')
const booking = ref(null)

const today = new Date().toISOString().slice(0, 10)
const maxDate = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
})

const venue = computed(() => venues.value.find((v) => v.id === venueId.value))

const isWeekend = computed(() => {
  const d = new Date(dateStr.value + 'T00:00:00')
  return d.getDay() === 0 || d.getDay() === 6
})

const pricePerHour = computed(() => {
  if (!venue.value) return 0
  return isWeekend.value ? venue.value.price_weekend : venue.value.price_weekday
})

const total = computed(() => pricePerHour.value * hours.value)

const endTime = computed(() => {
  const [h, m] = start.value.split(':').map(Number)
  const total = h * 60 + m + hours.value * 60
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
})

// Часовые слоты от открытия до закрытия
const allSlots = computed(() => {
  const slots = []
  for (let h = OPEN_HOUR; h < CLOSE_HOUR; h++) {
    slots.push(`${String(h).padStart(2, '0')}:00`)
  }
  return slots
})

// Проверка пересечения выбранного интервала с занятыми
function intervalOverlaps(startMin, endMin) {
  return occupied.value.some((b) => {
    const [bh, bm] = b.start_time.split(':').map(Number)
    const [eh, em] = b.end_time.split(':').map(Number)
    const bStart = bh * 60 + bm
    const bEnd = eh * 60 + em
    return startMin < bEnd && endMin > bStart
  })
}

const slotState = computed(() => {
  const map = {}
  for (const s of allSlots.value) {
    const [h] = s.split(':').map(Number)
    const startMin = h * 60
    const endMin = startMin + hours.value * 60
    let state = 'free'
    if (endMin > CLOSE_HOUR * 60) state = 'closed'
    else if (intervalOverlaps(startMin, endMin)) state = 'busy'
    map[s] = state
  }
  return map
})

async function loadOccupied() {
  if (!venueId.value) return
  loadingSlots.value = true
  try {
    occupied.value = await getOccupied(venueId.value, dateStr.value)
  } finally {
    loadingSlots.value = false
  }
}

watch([venueId, dateStr], loadOccupied)
watch(hours, () => {
  // при изменении длительности старт может стать невалидным
  if (slotState.value[start.value] !== 'free') {
    const firstFree = allSlots.value.find((s) => slotState.value[s] === 'free')
    if (firstFree) start.value = firstFree
  }
})

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    booking.value = await createBooking({
      venue_id: venueId.value,
      date: dateStr.value,
      start_time: start.value,
      hours: hours.value,
      customer_name: name.value,
      phone: phone.value,
      comment: comment.value,
    })
    router.push(`/booking/${booking.value.code}`)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  venues.value = await getVenues()
  const bySlug = venues.value.find((v) => v.slug === route.query.venue)
  venueId.value = bySlug ? bySlug.id : venues.value[0]?.id
  await loadOccupied()
})
</script>

<template>
  <div class="container section booking-page">
    <div v-if="booking" class="card success-card">
      <h2>Бронь создана! 🎉</h2>
      <p>Код вашей брони: <strong class="code">{{ booking.code }}</strong></p>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="booking-layout">
      <div class="card form-card">
        <div class="grid-2">
          <div class="field">
            <label>Зал</label>
            <select v-model="venueId">
              <option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>Дата</label>
            <input type="date" v-model="dateStr" :min="today" :max="maxDate" />
          </div>
          <div class="field">
            <label>Начало</label>
            <select v-model="start">
              <option v-for="(state, s) in slotState" :key="s" :value="s" :disabled="state !== 'free'">
                {{ s }} {{ state === 'busy' ? '— занято' : state === 'closed' ? '— не хватает времени до закрытия' : '— свободно' }}
              </option>
            </select>
          </div>
          <div class="field">
            <label>Длительность</label>
            <select v-model.number="hours">
              <option :value="1">1 час</option>
              <option :value="2">2 часа</option>
              <option :value="3">3 часа</option>
              <option :value="4">4 часа</option>
            </select>
          </div>
        </div>

        <h3>Ваши данные</h3>
        <div class="grid-2">
          <div class="field">
            <label>Имя и фамилия *</label>
            <input v-model="name" placeholder="Айдана Смагулова" />
          </div>
          <div class="field">
            <label>Телефон *</label>
            <input v-model="phone" placeholder="+7 (7XX) XXX-XX-XX" />
          </div>
          <div class="field">
            <label>Комментарий</label>
            <input v-model="comment" placeholder="Например: турнир по волейболу" />
          </div>
        </div>
      </div>

      <aside class="card summary">
        <h3>Ваша бронь</h3>
        <div v-if="venue" class="sum-venue">
          <img :src="venue.image" :alt="venue.name" />
          <strong>{{ venue.name }}</strong>
        </div>
        <ul class="sum-list">
          <li><span>Дата</span><strong>{{ formatDateHuman(dateStr) }}</strong></li>
          <li><span>Время</span><strong>{{ start }}–{{ endTime }}</strong></li>
          <li><span>Длительность</span><strong>{{ hours }} ч</strong></li>
          <li>
            <span>Стоимость часа</span>
            <strong>{{ formatPrice(pricePerHour) }}{{ isWeekend ? ' (вых.)' : '' }}</strong>
          </li>
          <li class="sum-total"><span>Итого</span><strong>{{ formatPrice(total) }}</strong></li>
        </ul>
        <button class="btn btn-gold btn-block" :disabled="submitting || !name || !phone" @click="submit">
          {{ submitting ? 'Отправляем…' : 'Забронировать' }}
        </button>
        <p class="muted small">
          Оплата на месте. Бронь действует до подтверждения администратором.
        </p>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.booking-page { max-width: 1100px; margin-left: auto; margin-right: auto; }
.booking-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; margin-top: 22px; align-items: start; }
.form-card { padding: 24px 26px; }
.summary { padding: 22px 24px; position: sticky; top: 84px; }
.sum-venue img { width: 100%; height: 130px; object-fit: cover; border-radius: 10px; margin-bottom: 10px; }
.sum-list { list-style: none; padding: 0; margin: 14px 0 18px; }
.sum-list li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px dashed var(--gray); font-size: 14.5px; }
.sum-list span { color: var(--muted); }
.sum-total { font-size: 17px; }
.sum-total strong { color: var(--navy); }
.btn-block { width: 100%; }
.small { font-size: 12.5px; margin-top: 10px; }
.success-card { padding: 20px 24px; margin-top: 18px; }
.code { font-size: 20px; color: var(--navy); }

@media (max-width: 900px) {
  .booking-layout { grid-template-columns: 1fr; }
  .summary { position: static; }
}
</style>
