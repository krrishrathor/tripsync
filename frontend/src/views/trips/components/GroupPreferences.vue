<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <h3 class="text-lg font-bold text-gray-900 mb-4 flex justify-between items-center">
      <span>Group Preferences</span>
      <button @click="fetchData" class="text-sm text-blue-600 hover:text-blue-800">Refresh</button>
    </h3>
    
    <div v-if="preferenceStore.loading" class="text-center py-4">
      <span class="text-gray-500">Loading...</span>
    </div>
    
    <div v-else-if="!data || data.status === 'no_data'" class="text-center py-4 text-gray-500">
      No preferences submitted yet.
    </div>
    
    <div v-else class="space-y-4">
      <div class="flex justify-between items-center pb-2 border-b">
        <span class="text-sm text-gray-600">Completion</span>
        <span class="font-medium text-sm">{{ data.submitted_count }} / {{ data.total_members }} Members</span>
      </div>
      
      <div>
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Budget ({{ currency }})</h4>
        <div class="flex space-x-4 text-sm">
          <div><span class="text-gray-500">Avg Max:</span> {{ data.budget.average_max }}</div>
          <div><span class="text-gray-500">Min Acceptable:</span> <span class="font-bold text-red-600">{{ data.budget.min_acceptable }}</span></div>
        </div>
      </div>
      
      <div>
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Shared Interests</h4>
        <div class="flex flex-wrap gap-2">
          <span v-for="interest in data.interests.common" :key="interest" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            {{ interest }}
          </span>
          <span v-if="!data.interests.common.length" class="text-xs text-gray-500">None yet</span>
        </div>
      </div>
      
      <div>
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Dietary Requirements</h4>
        <div class="flex flex-wrap gap-2">
          <span v-for="food in data.food_requirements" :key="food" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
            {{ food }}
          </span>
          <span v-if="!data.food_requirements.length" class="text-xs text-gray-500">None</span>
        </div>
      </div>
      
      <div v-if="data.conflicts && data.conflicts.length > 0" class="mt-4 p-3 bg-red-50 rounded-md border border-red-100">
        <h4 class="text-xs font-bold text-red-800 uppercase tracking-wider mb-2">Conflicts Detected</h4>
        <ul class="list-disc pl-4 text-xs text-red-700 space-y-1">
          <li v-for="(conflict, i) in data.conflicts" :key="i">{{ conflict }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
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

const preferenceStore = usePreferenceStore();
const data = computed(() => preferenceStore.groupPreferences);

const fetchData = async () => {
  await preferenceStore.fetchGroupPreferences(props.tripId);
};

onMounted(() => {
  fetchData();
});

// Expose fetchData so parent can call it when individual preferences update
defineExpose({ fetchData });
</script>
