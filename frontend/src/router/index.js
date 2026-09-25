import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trips/create',
    name: 'CreateTrip',
    component: () => import('@/views/trips/CreateTrip.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trips/:id',
    name: 'TripDashboard',
    component: () => import('@/views/trips/TripDashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/join/:code',
    name: 'JoinTrip',
    component: () => import('@/views/trips/JoinTrip.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trips/:id/preferences',
    name: 'Preferences',
    component: () => import('@/views/trips/Preferences.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trips/:id/group-compatibility',
    name: 'GroupCompatibility',
    component: () => import('@/views/trips/GroupCompatibility.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/trips/:id/destinations',
    name: 'DestinationDiscovery',
    component: () => import('@/views/trips/DestinationDiscovery.vue'),
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next('/dashboard');
  } else {
    next();
  }
});

export default router;
