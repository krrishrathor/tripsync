<template>
  <div class="max-w-2xl mx-auto py-8 px-4">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">Create a New Trip</h2>
      <form @submit.prevent="submitForm" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700">Trip Name</label>
          <input v-model="form.name" type="text" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border" placeholder="e.g. Summer in Goa 2026">
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Description</label>
          <textarea v-model="form.description" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border" placeholder="What's this trip about?"></textarea>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Start Date (Optional)</label>
            <input v-model="form.start_date" type="date" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">End Date (Optional)</label>
            <input v-model="form.end_date" type="date" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border">
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">Total Group Budget (Approximate)</label>
          <div class="mt-1 relative rounded-md shadow-sm">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span class="text-gray-500 sm:text-sm">₹</span>
            </div>
            <input v-model="form.total_budget" type="number" class="block w-full pl-7 rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border" placeholder="0.00">
          </div>
        </div>
        
        <div v-if="error" class="text-red-500 text-sm">
          {{ error }}
        </div>
        
        <div class="flex justify-end space-x-3">
          <button type="button" @click="$router.push('/dashboard')" class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
          <button type="submit" :disabled="loading" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
            {{ loading ? 'Creating...' : 'Create Trip' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useTripStore } from '@/stores/trip';

const router = useRouter();
const tripStore = useTripStore();

const form = reactive({
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  total_budget: ''
});
const error = ref(null);
const loading = ref(false);

const submitForm = async () => {
  error.value = null;
  loading.value = true;
  
  const payload = { ...form };
  if (!payload.start_date) delete payload.start_date;
  if (!payload.end_date) delete payload.end_date;
  if (!payload.total_budget) delete payload.total_budget;
  
  try {
    const trip = await tripStore.createTrip(payload);
    router.push(`/trips/${trip.id}`);
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create trip.';
  } finally {
    loading.value = false;
  }
};
</script>
