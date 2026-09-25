<template>
  <div class="max-w-5xl mx-auto py-8 px-4">
    <!-- Header & Action -->
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <button @click="$router.push(`/trips/${route.params.id}`)" class="text-gray-500 hover:text-gray-700 mb-2 inline-block">
          ← Back to Trip Dashboard
        </button>
        <h2 class="text-3xl font-bold text-gray-900">Trip Itinerary</h2>
        <p class="text-gray-500 mt-1">Personalized day-by-day plan crafted by AI</p>
      </div>

      <div v-if="isOwner && (!itinerary || !itinerary.days?.length)">
        <button
          @click="generateItinerary"
          :disabled="generating"
          class="bg-indigo-600 text-white px-6 py-2.5 rounded-lg hover:bg-indigo-700 font-semibold shadow-sm flex items-center gap-2"
        >
          <span v-if="generating" class="animate-spin">⌛</span>
          <span v-else>✨</span>
          {{ generating ? 'Generating AI Itinerary...' : 'Generate Itinerary' }}
        </button>
      </div>
    </div>

    <!-- Error States -->
    <div v-if="error" class="bg-red-50 text-red-700 p-4 rounded-lg mb-6 border border-red-200">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="loading || generating" class="space-y-8">
      <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-pulse">
        <div class="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div class="space-y-3">
          <div class="h-4 bg-gray-100 rounded w-full"></div>
          <div class="h-4 bg-gray-100 rounded w-5/6"></div>
          <div class="h-4 bg-gray-100 rounded w-4/6"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!itinerary || !itinerary.days?.length" class="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
      <div class="text-6xl mb-4">🗓️</div>
      <h3 class="text-xl font-bold text-gray-900 mb-2">No itinerary yet</h3>
      <p class="text-gray-500 max-w-md mx-auto mb-6">
        The destination is selected, but the itinerary hasn't been generated.
        <span v-if="isOwner">Click the button above to let AI craft the perfect plan based on your group's preferences.</span>
        <span v-else>Wait for the trip owner to generate the itinerary.</span>
      </p>
    </div>

    <!-- Itinerary Display -->
    <div v-else class="space-y-8">
      <div
        v-for="day in itinerary.days"
        :key="day.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
      >
        <!-- Day Header -->
        <div class="bg-indigo-50 border-b border-indigo-100 px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 class="text-xl font-bold text-indigo-900">Day {{ day.day_number }}: {{ day.theme }}</h3>
            <p v-if="day.date" class="text-sm text-indigo-700 mt-0.5">{{ new Date(day.date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' }) }}</p>
          </div>
          <div v-if="day.notes" class="text-xs font-medium text-indigo-600 bg-indigo-100 px-3 py-1.5 rounded-md max-w-sm">
            💡 {{ day.notes }}
          </div>
        </div>

        <!-- Activities -->
        <div class="p-6">
          <div v-if="!day.activities.length" class="text-sm text-gray-500 italic">No activities planned for this day.</div>
          <div class="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
            
            <div
              v-for="(activity, idx) in day.activities"
              :key="activity.id"
              class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active"
            >
              <!-- Timeline dot -->
              <div class="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-indigo-100 text-indigo-600 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10 text-xs font-bold uppercase">
                <span v-if="activity.time_of_day === 'Morning'">☀️</span>
                <span v-else-if="activity.time_of_day === 'Afternoon'">🌤️</span>
                <span v-else-if="activity.time_of_day === 'Evening'">🌅</span>
                <span v-else>🌙</span>
              </div>
              
              <!-- Card -->
              <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white border border-gray-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-1">
                  <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">{{ activity.time_of_day }}</span>
                  <span v-if="activity.estimated_cost && parseFloat(activity.estimated_cost) > 0" class="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded">
                    ~₹{{ parseFloat(activity.estimated_cost).toLocaleString('en-IN') }}
                  </span>
                </div>
                <h4 class="font-bold text-gray-900 text-lg mb-1">{{ activity.title }}</h4>
                <p v-if="activity.location" class="text-sm text-gray-500 mb-2 flex items-center gap-1">
                  📍 {{ activity.location }}
                </p>
                <p class="text-sm text-gray-700 leading-relaxed">{{ activity.description }}</p>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useItineraryStore } from '@/stores/itinerary';
import { useTripStore } from '@/stores/trip';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const itineraryStore = useItineraryStore();
const tripStore = useTripStore();
const authStore = useAuthStore();

const itinerary = computed(() => itineraryStore.itinerary);
const loading = computed(() => itineraryStore.loading || tripStore.loading);
const generating = computed(() => tripStore.currentTrip?.status === 'GENERATING_ITINERARY' || itineraryStore.generating);
const error = computed(() => itineraryStore.error);

const isOwner = computed(() => tripStore.currentTrip?.owner?.id === authStore.user?.id);

let pollInterval = null;

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser();
  }
  const tripId = route.params.id;
  await tripStore.fetchTripDetail(tripId);
  await itineraryStore.fetchItinerary(tripId);
  
  if (tripStore.currentTrip?.status === 'GENERATING_ITINERARY') {
    startPolling(tripId);
  }
});

const startPolling = (tripId) => {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    await tripStore.fetchTripDetail(tripId);
    if (tripStore.currentTrip?.status === 'ITINERARY_GENERATED') {
      clearInterval(pollInterval);
      await itineraryStore.fetchItinerary(tripId);
    } else if (tripStore.currentTrip?.status !== 'GENERATING_ITINERARY') {
      // Something failed or changed state back
      clearInterval(pollInterval);
    }
  }, 3000);
};

const generateItinerary = async () => {
  const tripId = route.params.id;
  await itineraryStore.generateItinerary(tripId);
  await tripStore.fetchTripDetail(tripId);
  startPolling(tripId);
};

import { onUnmounted } from 'vue';
onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>
