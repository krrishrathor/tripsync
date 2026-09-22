<template>
  <div class="max-w-3xl mx-auto py-8 px-4">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Your Travel Preferences</h2>
      <p class="text-sm text-gray-500 mt-1">Help the group find the perfect destination — be honest!</p>
    </div>

    <form @submit.prevent="save" class="space-y-8">
      <!-- Budget -->
      <section class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-base font-semibold text-gray-900 mb-4">💰 Budget</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Minimum (₹)</label>
            <input v-model.number="form.min_budget" type="number" min="0"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. 5000" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Maximum (₹)</label>
            <input v-model.number="form.max_budget" type="number" min="0"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. 20000" />
          </div>
        </div>
      </section>

      <!-- Travel Style & Logistics -->
      <section class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-base font-semibold text-gray-900 mb-4">✈️ Travel Style & Logistics</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Travel Style</label>
            <select v-model="form.travel_style"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="budget">Budget Backpacker</option>
              <option value="mid_range">Mid Range</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Preferred Transport</label>
            <select v-model="form.preferred_transport"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="flight">Flight</option>
              <option value="train">Train</option>
              <option value="bus">Bus</option>
              <option value="road">Road Trip</option>
              <option value="any">No Preference</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Max Travel Hours (one way)</label>
            <input v-model.number="form.max_travel_hours" type="number" min="1" max="72"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. 6" />
          </div>
        </div>
      </section>

      <!-- Interests -->
      <section class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-base font-semibold text-gray-900 mb-1">🎯 Interests</h3>
        <p class="text-xs text-gray-400 mb-4">Select all that excite you</p>
        <div class="grid grid-cols-3 sm:grid-cols-4 gap-3">
          <label v-for="interest in allInterests" :key="interest.value"
            class="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer select-none text-sm transition"
            :class="form.interests.includes(interest.value)
              ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
              : 'border-gray-200 text-gray-600 hover:border-gray-400'">
            <input type="checkbox" class="hidden" :value="interest.value" v-model="form.interests" />
            <span>{{ interest.emoji }} {{ interest.label }}</span>
          </label>
        </div>
      </section>

      <!-- Food Preferences -->
      <section class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-base font-semibold text-gray-900 mb-4">🍽️ Food Preferences</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Diet Type</label>
            <select v-model="form.diet_type"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="non_vegetarian">Non Vegetarian</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="halal">Halal</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Allergies (comma-separated)</label>
            <input v-model="allergiesInput" type="text"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. nuts, gluten, dairy" />
          </div>
        </div>
      </section>

      <!-- Accommodation & Activity -->
      <section class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="text-base font-semibold text-gray-900 mb-4">🏨 Accommodation & Activity Level</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Accommodation Type</label>
            <select v-model="form.accommodation_type"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="hostel">Hostel</option>
              <option value="budget">Budget Hotel</option>
              <option value="mid_range">Mid-Range Hotel</option>
              <option value="luxury">Luxury Hotel / Resort</option>
              <option value="apartment">Apartment / Airbnb</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Activity Intensity</label>
            <div class="grid grid-cols-3 gap-2 mt-1">
              <label v-for="opt in intensityOptions" :key="opt.value"
                class="flex flex-col items-center justify-center p-2 border rounded-lg cursor-pointer text-center transition"
                :class="form.activity_intensity === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-400'">
                <input type="radio" class="hidden" :value="opt.value" v-model="form.activity_intensity" />
                <span class="text-xl">{{ opt.emoji }}</span>
                <span class="text-xs font-medium mt-1">{{ opt.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </section>

      <!-- Error & Submit -->
      <div v-if="errorMsg" class="text-red-600 text-sm text-center bg-red-50 p-3 rounded-lg">{{ errorMsg }}</div>
      <div v-if="saved" class="text-green-600 text-sm text-center bg-green-50 p-3 rounded-lg">✓ Preferences saved successfully!</div>

      <div class="flex justify-end gap-3">
        <button type="button" @click="$router.back()"
          class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm hover:bg-gray-50">
          Cancel
        </button>
        <button type="submit" :disabled="saving"
          class="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {{ saving ? 'Saving...' : 'Save Preferences' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePreferenceStore } from '@/stores/preference';

const route = useRoute();
const router = useRouter();
const prefStore = usePreferenceStore();

const tripId = route.params.id;
const saving = ref(false);
const saved = ref(false);
const errorMsg = ref('');

const form = reactive({
  min_budget: null,
  max_budget: null,
  travel_style: 'mid_range',
  preferred_transport: 'any',
  max_travel_hours: null,
  interests: [],
  diet_type: 'non_vegetarian',
  food_allergies: [],
  accommodation_type: 'mid_range',
  activity_intensity: 'moderate',
});

const allergiesInput = ref('');

const allInterests = [
  { value: 'beaches',     label: 'Beaches',      emoji: '🏖️' },
  { value: 'mountains',   label: 'Mountains',    emoji: '⛰️' },
  { value: 'adventure',   label: 'Adventure',    emoji: '🧗' },
  { value: 'nightlife',   label: 'Nightlife',    emoji: '🎉' },
  { value: 'food',        label: 'Food',         emoji: '🍜' },
  { value: 'photography', label: 'Photography',  emoji: '📷' },
  { value: 'culture',     label: 'Culture',      emoji: '🎭' },
  { value: 'history',     label: 'History',      emoji: '🏛️' },
  { value: 'shopping',    label: 'Shopping',     emoji: '🛍️' },
  { value: 'nature',      label: 'Nature',       emoji: '🌿' },
  { value: 'relaxation',  label: 'Relaxation',   emoji: '💆' },
  { value: 'sports',      label: 'Sports',       emoji: '⚽' },
];

const intensityOptions = [
  { value: 'relaxed',     label: 'Relaxed',     emoji: '😌' },
  { value: 'moderate',    label: 'Moderate',    emoji: '🚶' },
  { value: 'adventurous', label: 'Adventurous', emoji: '🏃' },
];

onMounted(async () => {
  await prefStore.fetchMyPreference(tripId);
  if (prefStore.myPreference) {
    const p = prefStore.myPreference;
    form.min_budget = p.min_budget;
    form.max_budget = p.max_budget;
    form.travel_style = p.travel_style;
    form.preferred_transport = p.preferred_transport;
    form.max_travel_hours = p.max_travel_hours;
    form.interests = p.interests || [];
    form.diet_type = p.diet_type;
    form.food_allergies = p.food_allergies || [];
    form.accommodation_type = p.accommodation_type;
    form.activity_intensity = p.activity_intensity;
    allergiesInput.value = (p.food_allergies || []).join(', ');
  }
});

const save = async () => {
  errorMsg.value = '';
  saved.value = false;
  saving.value = true;

  const payload = {
    ...form,
    food_allergies: allergiesInput.value
      ? allergiesInput.value.split(',').map(s => s.trim()).filter(Boolean)
      : [],
  };
  // Strip nulls for optional fields
  if (!payload.min_budget) delete payload.min_budget;
  if (!payload.max_budget) delete payload.max_budget;
  if (!payload.max_travel_hours) delete payload.max_travel_hours;

  try {
    await prefStore.savePreference(tripId, payload);
    saved.value = true;
    setTimeout(() => router.push(`/trips/${tripId}`), 1500);
  } catch (err) {
    errorMsg.value = JSON.stringify(err.response?.data || 'Failed to save.');
  } finally {
    saving.value = false;
  }
};
</script>
