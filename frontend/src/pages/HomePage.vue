<script setup>
import { ref } from 'vue'
import { getVenues, formatPrice } from '../api'
</script>

<template>
  <div>
    <!-- HERO -->
    <section class="hero">
      <div class="container hero-inner">
        <div class="hero-text">
          <span class="eyebrow">Спорткомплекс Shakarim University</span>
          <h1>Аренда спортивных залов<br />в Семее</h1>
          <p class="lead">
            Универсальный игровой зал, малый зал и тренажёрный зал — для тренировок,
            секций, турниров и корпоративных игр. Онлайн-бронирование за пару минут.
          </p>
          <div class="hero-actions">
            <router-link to="/booking" class="btn btn-gold">Забронировать зал</router-link>
            <a href="#venues" class="btn btn-outline hero-outline">Посмотреть залы</a>
          </div>
          <div class="hero-stats">
            <div><strong>3</strong><span>зала</span></div>
            <div><strong>08–22</strong><span>ежедневно</span></div>
            <div><strong>от 8 000 ₸</strong><span>за час</span></div>
          </div>
        </div>
        <div class="hero-photo card">
          <img src="/images/hall-universal.jpeg" alt="Универсальный игровой зал" />
        </div>
      </div>
    </section>

    <!-- VENUES -->
    <section id="venues" class="section">
      <div class="container">
        <span class="eyebrow">Наши залы</span>
        <h2>Выберите площадку</h2>
        <p class="lead">Три зала под разные задачи — от турниров до персональных тренировок.</p>

        <div v-if="loading" class="muted">Загрузка…</div>
        <div v-else class="grid-3">
          <router-link
            v-for="v in venues"
            :key="v.id"
            :to="{ path: '/booking', query: { venue: v.slug } }"
            class="venue-card card"
          >
            <img :src="v.image" :alt="v.name" />
            <div class="venue-body">
              <h3>{{ v.name }}</h3>
              <p class="muted">{{ v.description }}</p>
              <div class="venue-meta">
                <span>до {{ v.capacity }} чел.</span>
                <span>{{ v.area_m2 }} м²</span>
              </div>
              <div class="venue-price">
                от <strong>{{ formatPrice(Math.min(v.price_weekday, v.price_weekend)) }}</strong> / час
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS -->
    <section class="section section-alt">
      <div class="container">
        <span class="eyebrow">Как это работает</span>
        <h2>Бронирование за 3 шага</h2>
        <div class="grid-3 steps">
          <div class="step">
            <div class="step-num">1</div>
            <h3>Выберите зал и дату</h3>
            <p class="muted">Свободные слоты видны сразу — занятое время подсвечено.</p>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <h3>Оставьте контакты</h3>
            <p class="muted">Имя и телефон — мы перезвоним для подтверждения брони.</p>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <h3>Получите код брони</h3>
            <p class="muted">Покажите код на входе в спорткомплекс. Готово!</p>
          </div>
        </div>
      </div>
    </section>

    <!-- GALLERY -->
    <section class="section">
      <div class="container">
        <span class="eyebrow">Галерея</span>
        <h2>Наш комплекс изнутри</h2>
        <div class="gallery">
          <img
            v-for="n in 9"
            :key="n"
            :src="`/images/gallery/photo-${n}.jpeg`"
            :alt="`Фото спорткомплекса ${n}`"
            loading="lazy"
            @click="openLightbox(n)"
          />
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="section section-alt">
      <div class="container cta-box">
        <div>
          <h2>Готовы к игре?</h2>
          <p class="lead">Проверьте свободное время и забронируйте зал онлайн.</p>
        </div>
        <router-link to="/booking" class="btn btn-primary">Перейти к бронированию</router-link>
      </div>
    </section>

    <!-- LIGHTBOX -->
    <div v-if="lightbox" class="lightbox" @click="lightbox = null">
      <img :src="`/images/gallery/photo-${lightbox}.jpeg`" alt="Фото зала" />
      <button class="lightbox-close" aria-label="Закрыть">×</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return { venues: [], loading: true, lightbox: null }
  },
  async mounted() {
    try {
      this.venues = await getVenues()
    } finally {
      this.loading = false
    }
  },
  methods: {
    openLightbox(n) {
      this.lightbox = n
    },
    formatPrice,
  },
}
</script>

<style scoped>
.hero { background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%); color: #fff; }
.hero-inner {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 40px;
  align-items: center;
  padding: 64px 20px;
}
.hero h1 { color: #fff; }
.hero .lead { color: #dbe3f0; }
.hero-outline { border-color: rgba(255, 255, 255, 0.6); color: #fff; }
.hero-outline:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
.hero-actions { display: flex; gap: 14px; margin: 22px 0 30px; flex-wrap: wrap; }
.hero-stats { display: flex; gap: 34px; flex-wrap: wrap; }
.hero-stats div { display: flex; flex-direction: column; }
.hero-stats strong { font-size: 24px; color: var(--gold); }
.hero-stats span { font-size: 13px; color: #c9d3e4; }
.hero-photo img { width: 100%; height: 340px; object-fit: cover; display: block; }

.venue-card { display: block; color: inherit; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.venue-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(50, 66, 102, 0.18); }
.venue-card img { width: 100%; height: 200px; object-fit: cover; display: block; }
.venue-body { padding: 18px 20px 20px; }
.venue-meta { display: flex; gap: 14px; color: var(--muted); font-size: 13.5px; margin: 8px 0; }
.venue-price strong { color: var(--navy); }

.steps { counter-reset: step; }
.step { text-align: left; padding: 22px; background: var(--bg); border-radius: var(--radius); }
.step-num {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--gold);
  color: var(--navy);
  font-weight: 800;
  font-size: 19px;
  display: grid;
  place-items: center;
  margin-bottom: 12px;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.gallery img {
  width: 100%;
  height: 170px;
  object-fit: cover;
  border-radius: 10px;
  cursor: zoom-in;
  transition: transform 0.18s ease;
}
.gallery img:hover { transform: scale(1.03); }

.cta-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: var(--navy);
  border-radius: 18px;
  padding: 36px 40px;
  color: #fff;
  flex-wrap: wrap;
}
.cta-box h2 { color: #fff; margin: 0; }
.cta-box .lead { color: #c9d3e4; margin: 0; }

.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(20, 26, 40, 0.88);
  display: grid;
  place-items: center;
  z-index: 100;
  cursor: zoom-out;
  padding: 24px;
}
.lightbox img { max-width: 92vw; max-height: 88vh; border-radius: 12px; }
.lightbox-close {
  position: absolute;
  top: 18px;
  right: 26px;
  background: none;
  border: none;
  color: #fff;
  font-size: 40px;
  cursor: pointer;
}

@media (max-width: 860px) {
  .hero-inner { grid-template-columns: 1fr; padding: 44px 20px; }
  .hero-photo img { height: 240px; }
  .cta-box { justify-content: center; text-align: center; }
}
</style>
