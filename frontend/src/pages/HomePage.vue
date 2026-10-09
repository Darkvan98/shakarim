<script setup>
import { ref } from 'vue'
import { getGallery, getVenues } from '../api'
</script>

<template>
  <div>
    <!-- HERO -->
    <section class="hero">
      <div class="container hero-inner">
        <div class="hero-text">
          <span class="eyebrow">Спорткомплексы Shakarim University</span>
          <h1>Бронирование спортивных залов<br />в Семее</h1>
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

        <div v-if="loading" class="muted">Загрузка…</div>
        <div v-else class="grid-3">
          <router-link
            v-for="v in venues"
            :key="v.id"
            :to="{ path: '/booking', query: { venue: v.slug } }"
            class="venue-card card"
          >
            <!-- Карусель фото: несколько снимков, листаются стрелками влево/вправо -->
            <div v-if="venuePhotos(v).length" class="venue-carousel">
              <img
                v-for="(p, i) in venuePhotos(v)"
                :key="p"
                :src="p"
                :alt="v.name"
                class="venue-photo"
                :class="{ active: i === currentPhotoIdx(v) }"
              />
              <template v-if="venuePhotos(v).length > 1">
                <button class="car-btn prev" aria-label="Предыдущее фото" @click.prevent="movePhoto(v, -1)">‹</button>
                <button class="car-btn next" aria-label="Следующее фото" @click.prevent="movePhoto(v, 1)">›</button>
                <span class="car-counter">{{ currentPhotoIdx(v) + 1 }} / {{ venuePhotos(v).length }}</span>
              </template>
            </div>
            <div v-else class="venue-no-photo">Фото пока нет</div>
            <div class="venue-body">
              <h3>{{ v.name }}</h3>
              <p class="muted">{{ v.description }}</p>
              <div class="venue-meta">
                <span>до {{ v.capacity }} чел.</span>
                <span>{{ v.area_m2 }} м²</span>
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

        <div class="gallery-group" v-for="group in galleryGroups" :key="group.id">
          <div class="gallery-group-head">
            <h3>{{ group.title }}</h3>
            <p class="muted">{{ group.subtitle }}</p>
          </div>
          <div class="gallery">
            <img
              v-for="src in group.photos"
              :key="src"
              :src="src"
              :alt="`${group.title} — фото`"
              loading="lazy"
              @click="openLightbox(src, group.title)"
            />
          </div>
        </div>
        <div v-if="!loading && galleryGroups.length === 0" class="muted">
          Фотографии скоро появятся
        </div>
      </div>
    </section>

    <!-- LIGHTBOX -->
    <div v-if="lightbox" class="lightbox" @click="lightbox = null">
      <img :src="lightbox" alt="Фото зала" />
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
      galleryGroups: [],
      photoIdx: {},
      loading: true,
      lightbox: null,
      lightboxCaption: null,
    }
  },
  async mounted() {
    try {
      this.venues = await getVenues()
      this.galleryGroups = await getGallery()
    } finally {
      this.loading = false
    }
  },
  methods: {
    venuePhotos(v) {
      const list = Array.isArray(v.images) && v.images.length > 0 ? v.images : v.image ? [v.image] : []
      return list.filter(Boolean)
    },
    currentPhotoIdx(v) {
      const idx = this.photoIdx[v.id] || 0
      const len = this.venuePhotos(v).length
      return len ? Math.min(idx, len - 1) : 0
    },
    movePhoto(v, dir) {
      const len = this.venuePhotos(v).length
      if (!len) return
      const cur = this.currentPhotoIdx(v)
      this.photoIdx = { ...this.photoIdx, [v.id]: (cur + dir + len) % len }
    },
    openLightbox(src, title) {
      this.lightbox = src
      this.lightboxCaption = title
    },

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

/* карусель фото зала на карточке */
.venue-carousel { position: relative; height: 200px; overflow: hidden; }
.venue-photo {
  position: absolute; inset: 0;
  width: 100%; height: 200px; object-fit: cover; display: block;
  opacity: 0; transition: opacity 0.25s ease;
}
.venue-photo.active { opacity: 1; }
.car-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 32px; height: 32px; border-radius: 50%;
  border: none; cursor: pointer; font-size: 18px; line-height: 1;
  background: rgba(255, 255, 255, 0.9); color: var(--navy);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  display: flex; align-items: center; justify-content: center;
}
.car-btn:hover { background: #fff; }
.car-btn.prev { left: 8px; }
.car-btn.next { right: 8px; }
.car-counter {
  position: absolute; bottom: 8px; right: 10px;
  background: rgba(0, 0, 0, 0.55); color: #fff;
  border-radius: 999px; padding: 2px 9px; font-size: 11.5px; font-weight: 600;
}
.venue-no-photo {
  height: 200px; display: flex; align-items: center; justify-content: center;
  background: #eef1f6; color: var(--muted); font-size: 14px;
}
.venue-body { padding: 18px 20px 20px; }
.venue-meta { display: flex; gap: 14px; color: var(--muted); font-size: 13.5px; margin: 8px 0; }


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
