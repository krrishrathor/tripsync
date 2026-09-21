<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <h3 class="text-lg font-bold text-gray-900 mb-4">My Travel Preferences</h3>
    <form @submit.prevent="savePreferences" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Max Budget ({{ currency }})</label>
        <input type="number" v-model="form.max_budget" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm border px-3 py-2" placeholder="0.00" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Interests (Comma separated)</label>
        <input type="text" v-model="interestsInput" class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm border px-3 py-2" placeholder="e.g. beaches, hiking, food, history" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Dietary Requirements (Comma separated)</label>
        <input type="text" v-model="foodInput" class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm border px-3 py-2" placeholder="e.g. vegetarian, gluten-free" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Travel Style</label>
        <select v-model="form.travel_style" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm border px-3 py-2">
          <option value="">Select a style</option>
          <option value="relaxed">Relaxed & Chill</option>
          <option value="moderate">Moderate Pacing</option>
          <option value="packed">Action Packed</option>
        </select>
      </div>
      
      <div v-if="successMsg" class="text-green-600 text-sm">{{ successMsg }}</div>

      <div class="flex justify-end pt-4">
        <button type="submit" :disabled="loading" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          {{ loading ? 'Saving...' : 'Save Preferences' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { usePreferenceStore } from '@/stores/preference';

const props = defineProps({
  tripId: {
    type: String,
    required: true
  },
  currency: {
    type: String,
    default: 'INR'
  }
});

const emit = defineEmits(['saved']);
const preferenceStore = usePreferenceStore();

const loading = ref(false);
const successMsg = ref('');
const interestsInput = ref('');
const foodInput = ref('');

const form = reactive({
  max_budget: '',
  travel_style: '',
  interests: [],
  food_preferences: []
});

onMounted(async () => {
  await preferenceStore.fetchMyPreferences(props.tripId);
  if (preferenceStore.myPreferences) {
    form.max_budget = preferenceStore.myPreferences.max_budget;
    form.travel_style = preferenceStore.myPreferences.travel_style;
    interestsInput.value = preferenceStore.myPreferences.interests.join(', ');
    foodInput.value = preferenceStore.myPreferences.food_preferences.join(', ');
  }
});

const savePreferences = async () => {
  loading.value = true;
  successMsg.value = '';
  
  form.interests = interestsInput.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  form.food_preferences = foodInput.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  
  try {
    await preferenceStore.saveMyPreferences(props.tripId, form);
    successMsg.value = 'Preferences saved successfully!';
    emit('saved');
    setTimeout(() => successMsg.value = '', 3000);
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>
