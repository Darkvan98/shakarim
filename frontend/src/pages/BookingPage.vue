<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createBooking, formatDateHuman, getOccupied, getVenues } from '../api'

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
const phoneWarning = ref('')
const prevDigitCount = ref(0)
const booking = ref(null)

const today = new Date().toISOString().slice(0, 10)
const maxDate = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
})

const venue = computed(() => venues.value.find((v) => v.id === venueId.value))

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

// Проверка пересечения интервала с занятыми
function intervalOverlaps(startMin, endMin) {
  return occupied.value.some((b) => {
    const [bh, bm] = b.start_time.split(':').map(Number)
    const [eh, em] = b.end_time.split(':').map(Number)
    const bStart = bh * 60 + bm
    const bEnd = eh * 60 + em
    return startMin < bEnd && endMin > bStart
  })
}

function formatTime(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Информация о каждом часе: статус и до скольки занято (если перекрыт броней).
const slotInfo = computed(() => {
  const map = {}
  for (const s of allSlots.value) {
    const [h] = s.split(':').map(Number)
    const slotStart = h * 60
    const slotEnd = slotStart + 60
    let occupiedUntil = null
    for (const b of occupied.value) {
      const [bh, bm] = b.start_time.split(':').map(Number)
      const [eh, em] = b.end_time.split(':').map(Number)
      const bStart = bh * 60 + bm
      const bEnd = eh * 60 + em
      if (slotStart < bEnd && slotEnd > bStart) {
        // час перекрыт этой броней — возьмём максимальный bEnd среди перекрывающих
        if (bEnd > (occupiedUntil || 0)) occupiedUntil = bEnd
      }
    }
    map[s] = {
      status: occupiedUntil ? 'busy' : 'free',
      occupiedUntil,
    }
  }
  return map
})

// Можно ли начать бронирование с выбранного часа на выбранную длительность
const canStartAt = computed(() => {
  const [h] = start.value.split(':').map(Number)
  const startMin = h * 60
  const endMin = startMin + hours.value * 60
  if (endMin > CLOSE_HOUR * 60) return false
  return !intervalOverlaps(startMin, endMin)
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

const canBook = computed(() => canStartAt.value)

watch(start, (newStart) => {
  // если выбранный час занят — найдём ближайший свободный после него
  if (slotInfo.value[newStart] && slotInfo.value[newStart].status !== 'free') {
    const idx = allSlots.value.indexOf(newStart)
    const replacement = allSlots.value.slice(idx + 1).find((s) => slotInfo.value[s].status === 'free')
    if (replacement) start.value = replacement
  }
  // если при текущем start и hours валидация не проходит — подберём ближайший подходящий
  if (!canStartAt.value) {
    for (const s of allSlots.value) {
      const [h] = s.split(':').map(Number)
      const startMin = h * 60
      const endMin = startMin + hours.value * 60
      if (endMin <= CLOSE_HOUR * 60 && !intervalOverlaps(startMin, endMin)) {
        start.value = s
        break
      }
    }
  }
})

function onPhoneInput(e) {
  const raw = e.target.value
  const cleaned = raw.replace(/[^0-9+]/g, '')
  phoneWarning.value = ''

  if (cleaned === '') {
    phoneWarning.value = 'Введите номер телефона цифрами'
    prevDigitCount.value = 0
    phone.value = ''
    return
  }

  const hasLetters = raw.replace(/[^a-zA-Z]/g, '') !== ''
  if (hasLetters) {
    phoneWarning.value = 'В номере телефона буквы не используются — оставлены только цифры'
  }

  // Определяем: код страны и цифры номера
  let countryCode = ''
  let digits = ''

  if (cleaned.startsWith('+')) {
    const afterPlus = cleaned.slice(1)
    if (afterPlus.startsWith('7')) {
      countryCode = '+7'
      digits = afterPlus.slice(1)
    } else {
      countryCode = '+'
      digits = afterPlus
    }
  } else if (cleaned.startsWith('7')) {
    countryCode = '+7'
    digits = cleaned.slice(1)
  } else if (cleaned.startsWith('8')) {
    countryCode = '+7'
    digits = cleaned.slice(1)
  } else {
    digits = cleaned
  }

  // Ограничиваем номер 10 цифрами
  if (digits.length > 10) digits = digits.slice(0, 10)

  const isRemoval = digits.length < prevDigitCount.value
  prevDigitCount.value = digits.length

  // Форматируем: скобки появляются когда есть минимум 3 цифры, тире — когда больше 6
  if (digits.length === 0) {
    phone.value = countryCode || cleaned
    return
  }

  let formatted
  if (digits.length < 3) {
    formatted = (countryCode ? countryCode + ' ' : '') + '(' + digits + ')'
  } else {
    formatted = (countryCode ? countryCode + ' ' : '') + '(' + digits.slice(0, 3) + ')'
    if (digits.length > 3) formatted += ' ' + digits.slice(3, 6)
    if (digits.length > 6) formatted += '-' + digits.slice(6, 8)
    if (digits.length > 8) formatted += '-' + digits.slice(8, 10)
  }

  phone.value = formatted
}

async function submit() {
  error.value = ''
  if (!canBook.value) {
    error.value = 'Это время уже занято — выберите другое.'
    return
  }
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
              <option v-for="(info, s) in slotInfo" :key="s" :value="s" :disabled="info.status !== 'free'">
                {{ s }}
                {{ info.status === 'busy' ? '— занято до ' + formatTime(info.occupiedUntil) : '— свободно' }}
              </option>
            </select>
            <small v-if="!canBook" class="error-text">
              {{ slotInfo[start.value]?.status === 'busy' ? 'Этот час занят' : 'Не хватает времени до закрытия' }}
            </small>
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
            <input
              type="tel"
              v-model="phone"
              @input="onPhoneInput"
              placeholder="+7 (7XX) XXX-XX-XX"
            />
            <small v-if="phoneWarning" class="error-text">{{ phoneWarning }}</small>
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
          <li class="sum-total"><span>Итого</span><strong>по договору</strong></li>
        </ul>
        <button class="btn btn-gold btn-block" :disabled="submitting || !name || !phone" @click="submit">
          {{ submitting ? 'Отправляем…' : 'Забронировать' }}
        </button>
        <p class="muted small">
          Бронь действует до подтверждения администратором.
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
