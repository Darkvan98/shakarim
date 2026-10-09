<script setup>
import { ref } from 'vue'
import { formatDateHuman, getBookingsByName } from '../api'

const nameQuery = ref('')
const bookings = ref([])
const error = ref('')
const searched = ref('')
const loading = ref(false)

async function search() {
  const q = nameQuery.value.trim()
  if (q.length < 2) {
    error.value = 'Введите имя (минимум 2 символа)'
    return
  }
  error.value = ''
  loading.value = true
  searched.value = q
  try {
    bookings.value = await getBookingsByName(q)
  } catch (e) {
    error.value = e.message
    bookings.value = []
  } finally {
    loading.value = false
  }
}

const statusLabels = {
  pending: 'Ожидает подтверждения',
  confirmed: 'Подтверждена',
  cancelled: 'Отменена',
}
</script>

<template>
  <div class="container section narrow">
    <span class="eyebrow">Мои брони</span>
    <h1>Найти бронь по имени</h1>
    <p class="muted">Введите имя и фамилию, которые вы указали при бронировании.</p>

    <div class="find-row card">
      <input
        v-model="nameQuery"
        placeholder="Например: Айдана Смагулова"
        @keyup.enter="search"
      />
      <button class="btn btn-primary" :disabled="loading" @click="search">
        {{ loading ? 'Ищем…' : 'Найти' }}
      </button>
    </div>

    <div v-if="error" class="alert alert-error" style="margin-top:14px">{{ error }}</div>

    <div v-if="searched && !loading && bookings.length === 0 && !error" class="muted" style="margin-top:14px">
      Броней на имя «{{ searched }}» не найдено.
    </div>

    <div v-for="b in bookings" :key="b.id" class="card ticket">
      <div class="ticket-head">
        <span class="badge" :class="`badge-${b.status}`">{{ statusLabels[b.status] || b.status }}</span>
        <strong>{{ b.customer_name }}</strong>
      </div>
      <h2>{{ b.venue_name }}</h2>
      <ul class="sum-list">
        <li><span>Дата</span><strong>{{ formatDateHuman(b.date) }}</strong></li>
        <li><span>Время</span><strong>{{ b.start_time }}–{{ b.end_time }}</strong></li>
        <li><span>Длительность</span><strong>{{ b.hours }} ч</strong></li>
        <li><span>Телефон</span><strong>{{ b.phone }}</strong></li>
      </ul>
      <div class="qr-hint muted">
        Подтверждение брони — по имени и телефону на входе в спорткомплекс.
      </div>
    </div>
  </div>
</template>

<style scoped>
.narrow { max-width: 640px; }
h1, p { margin-top: 6px; }
.find-row { display: flex; gap: 10px; padding: 16px 18px; margin-top: 14px; }
.find-row input { flex: 1; }
.ticket { padding: 26px 30px; margin-top: 16px; }
.ticket-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.qr-hint { margin-top: 14px; padding: 12px 16px; background: #eef1f6; border-radius: 10px; }
</style>
