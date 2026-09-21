<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <nav class="bg-white shadow-sm border-b border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-600 cursor-pointer" @click="$router.push('/dashboard')">TripSync</h1>
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-700" v-if="authStore.user">Welcome, {{ authStore.user.first_name }}</span>
          <button @click="logout" class="text-sm text-gray-500 hover:text-gray-700">Logout</button>
        </div>
      </div>
    </nav>
    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-900">Your Trips</h2>
        <button @click="$router.push('/trips/create')" class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 shadow-sm">
          + New Trip
        </button>
      </div>
      
      <div v-if="tripStore.loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
      
      <div v-else-if="tripStore.trips.length === 0" class="bg-white p-12 text-center rounded-xl shadow-sm border border-gray-100">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No trips yet</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new trip or joining one.</p>
        <div class="mt-6">
          <button @click="$router.push('/trips/create')" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
            Create New Trip
          </button>
        </div>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="trip in tripStore.trips" :key="trip.id" @click="$router.push(`/trips/${trip.id}`)" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition cursor-pointer">
          <div class="flex justify-between items-start">
            <h3 class="text-lg font-bold text-gray-900 truncate">{{ trip.name }}</h3>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {{ trip.status }}
            </span>
          </div>
          <p class="mt-2 text-sm text-gray-500 line-clamp-2">{{ trip.description || 'No description provided.' }}</p>
          <div class="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
            <span>👥 {{ trip.members_count }} Members</span>
            <span v-if="trip.owner.id === authStore.user?.id" class="text-yellow-600 text-xs font-semibold">Owner</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useTripStore } from '@/stores/trip';

const authStore = useAuthStore();
const tripStore = useTripStore();
const router = useRouter();

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser();
  }
  await tripStore.fetchTrips();
});

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>
