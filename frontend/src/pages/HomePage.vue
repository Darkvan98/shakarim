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
          <div class="hero-actions">
            <router-link to="/booking" class="btn btn-gold">Забронировать зал</router-link>
            <a href="#venues" class="btn btn-outline hero-outline">Посмотреть залы</a>
          </div>
        </div>
        <div class="hero-photo card">
          <img src="/images/hero-gym-wide.jpg" alt="Спорткомплекс Shakarim University — светлый спортивный зал с деревянным полом" />
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

        <div class="gallery-group" v-for="group in galleryGroups" :key="group.key">
          <div class="gallery-group-head">
            <h3>{{ group.title }}</h3>
            <p class="muted">{{ group.subtitle }}</p>
          </div>
          <div class="gallery">
            <img
              v-for="n in group.photos"
              :key="n"
              :src="group.src(n)"
              :alt="group.alt(n)"
              loading="lazy"
              @click="openLightbox(n)"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- LIGHTBOX -->
    <div v-if="lightbox" class="lightbox" @click="lightbox = null">
      <img :src="`/images/gallery/photo-${lightbox}.jpeg`" alt="Фото зала" />
      <button class="lightbox-close" aria-label="Закрыть">×</button>
      <div class="lightbox-caption" v-if="lightboxCaption">{{ lightboxCaption }}</div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      venues: [],
      loading: true,
      lightbox: null,
      lightboxCaption: null,
      // Группы фото по площадкам. Некоторые фото общие для нескольких залов.
      // Файлы переименованы в формат: photo-<N>-sport-<ключ>.jpeg
      // Например: photo-1-sport-1.jpeg, photo-3-sport-2-football.jpeg, photo-9-sport-2-volleyball.jpeg, photo-9-sport-2-tennis.jpeg
      galleryGroups: [
        {
          key: 'sport-1',
          title: 'Спорткомплекс 1',
          subtitle: 'первые 2 фото',
          photos: [1, 2],
          src: (n) => `/images/gallery/photo-${n}-sport-1.jpeg`,
          alt: (n) => `Фото Спорткомплекс 1, фото ${n}`,
        },
        {
          key: 'sport-2-1',
          title: 'Спорткомплекс 2, 1 этаж, футзал',
          subtitle: 'фото с 3 по 8',
          photos: [3, 4, 5, 6, 7, 8],
          src: (n) => `/images/gallery/photo-${n}-sport-2-football.jpeg`,
          alt: (n) => `Фото Спорткомплекс 2, 1 этаж, футзал, фото ${n}`,
        },
        {
          key: 'sport-2-2-volleyball',
          title: '2-й спорткомплекс, 2 этаж, зал волейбола',
          subtitle: 'фото с 9 по 10',
          photos: [9, 10],
          src: (n) => `/images/gallery/photo-${n}-sport-2-volleyball.jpeg`,
          alt: (n) => `Фото 2-й спорткомплекс, 2 этаж, зал волейбола, фото ${n}`,
        },
        {
          key: 'sport-2-1-tennis',
          title: '2-й спорткомплекс, 1 этаж, теннисный зал',
          subtitle: 'последние 3 фото',
          photos: [9, 10, 11],
          src: (n) => `/images/gallery/photo-${n}-sport-2-tennis.jpeg`,
          alt: (n) => `Фото 2-й спорткомплекс, 1 этаж, теннисный зал, фото ${n}`,
        },
      ],
    }
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
      this.lightboxCaption = this.findCaptionFor(n)
    },
    findCaptionFor(n) {
      for (const g of this.galleryGroups) {
        if (g.photos.includes(n)) {
          return g.title
        }
      }
      return null
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
.hero-actions { display: flex; gap: 14px; margin: 22px 0 0; flex-wrap: wrap; }
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
}    @media (max-width: 860px) {
  .hero-inner { grid-template-columns: 1fr; padding: 44px 20px; }
  .hero-photo img { height: 240px; }
}

.gallery-group { margin-bottom: 28px; }
.gallery-group-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.gallery-group-head h3 {
  margin: 0;
  font-size: 18px;
  color: var(--navy);
}
.gallery-group-head .muted {
  display: block;
  margin: 0;
  font-size: 13px;
}
.lightbox-caption {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 26, 40, 0.85);
  color: #fff;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 14px;
  white-space: nowrap;
}
</style>
