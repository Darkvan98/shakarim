import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './pages/HomePage.vue'
import Venues from './pages/VenuesPage.vue'
import Booking from './pages/BookingPage.vue'
import MyBooking from './pages/MyBookingPage.vue'
import Admin from './pages/AdminPage.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/venues', name: 'venues', component: Venues },
    { path: '/booking', name: 'booking', component: Booking },
    { path: '/booking/:code', name: 'my-booking', component: MyBooking },
    { path: '/admin', name: 'admin', component: Admin },
  ],
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

createApp(App).use(router).mount('#app')
