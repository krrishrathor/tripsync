<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center">
      <div v-if="loading">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">Joining trip...</p>
      </div>
      <div v-else-if="success">
        <svg class="mx-auto h-12 w-12 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <h2 class="mt-4 text-2xl font-bold text-gray-900">Successfully Joined!</h2>
        <p class="mt-2 text-gray-600">You are now a member of the trip.</p>
        <button @click="$router.push(`/trips/${tripId}`)" class="mt-6 w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          Go to Trip Dashboard
        </button>
      </div>
      <div v-else>
        <svg class="mx-auto h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        <h2 class="mt-4 text-2xl font-bold text-gray-900">Failed to join</h2>
        <p class="mt-2 text-gray-600">{{ error }}</p>
        <button @click="$router.push('/dashboard')" class="mt-6 w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200">
          Return to Dashboard
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useTripStore } from '@/stores/trip';

const route = useRoute();
const router = useRouter();
const tripStore = useTripStore();

const loading = ref(true);
const success = ref(false);
const error = ref('');
const tripId = ref(null);

onMounted(async () => {
  const code = route.params.code;
  try {
    const data = await tripStore.joinTrip(code);
    success.value = true;
    tripId.value = data.trip_id;
  } catch (err) {
    success.value = false;
    error.value = err.response?.data?.detail || 'Invalid or expired invite link.';
  } finally {
    loading.value = false;
  }
});
</script>
