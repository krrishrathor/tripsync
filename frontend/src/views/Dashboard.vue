<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <nav class="bg-white shadow-sm border-b border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-600">TripSync</h1>
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-700" v-if="authStore.user">Welcome, {{ authStore.user.first_name }}</span>
          <button @click="logout" class="text-sm text-gray-500 hover:text-gray-700">Logout</button>
        </div>
      </div>
    </nav>
    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <p class="text-gray-600">You are successfully authenticated!</p>
        <p class="mt-4 text-sm text-gray-500">Trip management will be added in Phase 3.</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser();
  }
});

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>
