<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { formatDateHuman, formatPrice, getBooking } from '../api'

const route = useRoute()
const booking = ref(null)
const error = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    booking.value = await getBooking(route.params.code)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const statusLabels = {
  pending: 'Ожидает подтверждения',
  confirmed: 'Подтверждена',
  cancelled: 'Отменена',
}
</script>

<template>
  <div class="container section narrow">
    <span class="eyebrow">Ваша бронь</span>
    <h1>Бронь {{ route.params.code }}</h1>

    <div v-if="loading" class="muted">Загрузка…</div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <div v-else class="card ticket">
      <div class="ticket-head">
        <span class="badge" :class="`badge-${booking.status}`">{{ statusLabels[booking.status] || booking.status }}</span>
        <strong class="code">{{ booking.code }}</strong>
      </div>
      <h2>{{ booking.venue_name }}</h2>
      <ul class="sum-list">
        <li><span>Дата</span><strong>{{ formatDateHuman(booking.date) }}</strong></li>
        <li><span>Время</span><strong>{{ booking.start_time }}–{{ booking.end_time }}</strong></li>
        <li><span>Длительность</span><strong>{{ booking.hours }} ч</strong></li>
        <li><span>Итого к оплате на месте</span><strong>{{ formatPrice(booking.total_price) }}</strong></li>
        <li><span>Имя</span><strong>{{ booking.customer_name }}</strong></li>
        <li><span>Телефон</span><strong>{{ booking.phone }}</strong></li>
      </ul>
      <div class="qr-hint muted">
        Назовите код брони <strong>{{ booking.code }}</strong> на входе в спорткомплекс.
      </div>
    </div>
  </div>
</template>

<style scoped>
.narrow { max-width: 640px; }
.ticket { padding: 26px 30px; margin-top: 16px; }
.ticket-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.code { font-size: 18px; color: var(--navy); letter-spacing: 0.06em; }
.qr-hint { margin-top: 14px; padding: 12px 16px; background: #eef1f6; border-radius: 10px; }
</style>
