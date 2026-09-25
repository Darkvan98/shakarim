<script setup>
import { ref } from 'vue'

const menuOpen = ref(false)

const links = [
  { to: '/', label: 'Главная' },
  { to: '/venues', label: 'Залы и цены' },
  { to: '/booking', label: 'Бронирование' },
]
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="container header-inner">
        <router-link to="/" class="logo">
          <span class="logo-mark"><img class="logo-img" src="/images/logo.png" alt="Shakarim University" /></span>
          <span class="logo-text">
            <strong>SHAKARIM SPORT</strong>
            <small>аренда спорткомплекса</small>
          </span>
        </router-link>

        <nav class="nav" :class="{ open: menuOpen }">
          <router-link v-for="l in links" :key="l.to" :to="l.to" @click="menuOpen = false">
            {{ l.label }}
          </router-link>
          <router-link to="/booking" class="btn btn-gold btn-sm nav-cta" @click="menuOpen = false">
            Забронировать
          </router-link>
        </nav>

        <button class="burger" aria-label="Меню" @click="menuOpen = !menuOpen">☰</button>
      </div>
    </header>

    <main>
      <router-view />
    </main>

    <footer class="footer">
      <div class="container footer-grid">
        <div>
          <h4>Контакты</h4>
          <p class="muted">
            г. Семей, ул. Глинки 1А<br />
            +7 (700) 000-00-00<br />
            sport@shakarim.kz
          </p>
        </div>
      </div>
      <div class="container copyright muted">
        © {{ new Date().getFullYear() }} Shakarim University · Спортивный комплекс
      </div>
    </footer>
  </div>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--gray);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 66px;
}
.logo { display: flex; align-items: center; gap: 10px; }
.logo-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--navy);
  display: grid;
  place-items: center;
  padding: 5px;
  flex: none;
}
.logo-img { width: 100%; height: 100%; object-fit: contain; display: block; }
.logo-text { display: flex; flex-direction: column; line-height: 1.15; }
.logo-text strong { color: var(--navy); font-size: 15px; letter-spacing: 0.04em; }
.logo-text small { color: var(--muted); font-size: 11.5px; }

.nav { display: flex; align-items: center; gap: 22px; }
.nav a { color: var(--navy); font-weight: 600; font-size: 15px; }
.nav a.router-link-active:not(.nav-cta) { color: var(--gold); }
.nav-cta { margin-left: 6px; }

.burger {
  display: none;
  background: none;
  border: none;
  font-size: 24px;
  color: var(--navy);
  cursor: pointer;
}

@media (max-width: 760px) {
  .burger { display: block; }
  .nav {
    display: none;
    position: absolute;
    top: 66px;
    left: 0;
    right: 0;
    background: #fff;
    flex-direction: column;
    padding: 18px 20px;
    border-bottom: 1px solid var(--gray);
    box-shadow: var(--shadow);
  }
  .nav.open { display: flex; }
}

.footer { background: var(--navy); color: #cfd6e4; margin-top: 60px; }
.footer h3, .footer h4 { color: #fff; }
.footer a { color: var(--gold); }
.footer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 28px;
  padding: 40px 20px 24px;
}
.copyright { padding: 14px 20px 22px; font-size: 13px; border-top: 1px solid rgba(255, 255, 255, 0.12); }
</style>
