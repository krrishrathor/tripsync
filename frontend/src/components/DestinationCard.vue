<template>
  <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col">
    <!-- Image + Score Badge -->
    <div class="relative h-48 bg-gray-100 overflow-hidden shrink-0">
      <img
        v-if="scored.destination.image_url"
        :src="scored.destination.image_url"
        :alt="scored.destination.name"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-4xl">🗺️</div>

      <!-- Rank badge -->
      <div class="absolute top-3 left-3 bg-white rounded-full w-8 h-8 flex items-center justify-center text-xs font-bold text-gray-700 shadow-sm">
        #{{ rank }}
      </div>

      <!-- Score ring -->
      <div class="absolute top-3 right-3">
        <div class="relative w-14 h-14 bg-white/20 rounded-full backdrop-blur-sm">
          <svg class="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2.5"/>
            <circle cx="18" cy="18" r="15.9" fill="none"
              :stroke="scoreColor" stroke-width="2.5"
              :stroke-dasharray="`${scored.overall} ${100 - scored.overall}`"
              stroke-linecap="round"/>
          </svg>
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-xs font-bold text-white drop-shadow-md">{{ scored.overall }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-5 flex-1 flex flex-col">
      <div class="flex items-start justify-between mb-1">
        <h3 class="font-bold text-gray-900 text-lg leading-tight">{{ scored.destination.name }}</h3>
        <span class="text-xs text-gray-400 ml-2 mt-1 whitespace-nowrap">{{ scored.destination.region }}</span>
      </div>

      <!-- Cost estimate -->
      <p class="text-sm text-blue-600 font-medium mb-2">
        ₹{{ scored.destination.estimated_daily_cost_min.toLocaleString('en-IN') }}–{{ scored.destination.estimated_daily_cost_max.toLocaleString('en-IN') }}/day
      </p>

      <!-- Description -->
      <p class="text-xs text-gray-500 mb-4 line-clamp-2">{{ scored.destination.description }}</p>

      <!-- Factor scores -->
      <div class="space-y-1.5 mb-4">
        <FactorBar label="Budget" :score="scored.budget.score" />
        <FactorBar label="Interests" :score="scored.interest.score" />
        <FactorBar label="Activity" :score="scored.activity.score" />
      </div>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1 mb-4">
        <span
          v-for="tag in scored.destination.tags.slice(0,4)"
          :key="tag"
          class="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600 capitalize"
        >{{ tag }}</span>
      </div>

      <div class="flex-1"></div>

      <!-- Match label -->
      <div class="flex items-center justify-between mb-4">
        <span class="text-xs font-semibold px-2.5 py-1 rounded-full" :class="matchClass">
          {{ matchLabel }}
        </span>
        <span class="text-xs text-gray-400">{{ scored.destination.typical_duration_days_min }}–{{ scored.destination.typical_duration_days_max }} days</span>
      </div>

      <!-- Voting Section -->
      <div class="border-t border-gray-100 pt-4 mt-auto">
        <div class="flex items-center justify-between mb-3">
          <div class="text-sm font-medium text-gray-700">
            Votes: <span class="text-indigo-600">{{ voteCount }}</span>
          </div>
          <div v-if="voters.length" class="flex -space-x-2">
            <div v-for="(voter, i) in voters.slice(0, 5)" :key="i"
                 class="w-6 h-6 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-[10px] font-bold text-gray-600 uppercase"
                 :title="voter.first_name || voter.username">
              {{ (voter.first_name || voter.username).charAt(0) }}
            </div>
            <div v-if="voters.length > 5" class="w-6 h-6 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-[10px] text-gray-500">
              +{{ voters.length - 5 }}
            </div>
          </div>
        </div>

        <div v-if="tripStatus === 'PLANNING'" class="flex flex-col gap-2">
          <!-- User Vote Button -->
          <button
            @click="$emit('vote')"
            :disabled="isVoting"
            class="w-full py-2 rounded-lg text-sm font-medium transition-colors"
            :class="isMyVote 
              ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200' 
              : 'border border-gray-300 text-gray-700 hover:bg-gray-50'"
          >
            <span v-if="isVoting" class="inline-block animate-spin mr-1">⌛</span>
            {{ isMyVote ? '✓ You Voted For This' : 'Vote for this' }}
          </button>

          <!-- Owner Select Button -->
          <button
            v-if="isOwner"
            @click="$emit('select-final')"
            class="w-full py-2 rounded-lg text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors"
          >
            Lock in as Final Destination
          </button>
        </div>
        <div v-else-if="tripStatus === 'DESTINATION_SELECTED' && isSelected" class="w-full py-2 rounded-lg text-sm font-bold bg-green-100 text-green-800 text-center">
          🎉 Selected Destination
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h } from 'vue';

const props = defineProps({
  scored: { type: Object, required: true },
  rank: { type: Number, required: true },
  
  // Voting props
  voteCount: { type: Number, default: 0 },
  voters: { type: Array, default: () => [] },
  isMyVote: { type: Boolean, default: false },
  isOwner: { type: Boolean, default: false },
  tripStatus: { type: String, default: 'PLANNING' },
  isVoting: { type: Boolean, default: false },
  isSelected: { type: Boolean, default: false },
});

defineEmits(['vote', 'select-final']);

const scoreColor = computed(() => {
  const s = props.scored.overall;
  if (s >= 75) return '#4ade80'; // brighter green for dark bg ring
  if (s >= 55) return '#fbbf24'; // brighter yellow
  return '#f87171'; // brighter red
});

const matchLabel = computed(() => {
  const s = props.scored.overall;
  if (s >= 80) return '🎯 Excellent Match';
  if (s >= 65) return '✅ Good Match';
  if (s >= 50) return '🤝 Fair Match';
  return '⚠️ Poor Match';
});

const matchClass = computed(() => {
  const s = props.scored.overall;
  if (s >= 80) return 'bg-green-100 text-green-800';
  if (s >= 65) return 'bg-blue-100 text-blue-800';
  if (s >= 50) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
});

// Inline mini-component for factor bars
const FactorBar = defineComponent({
  props: {
    label: String,
    score: Number,  // 0-100
  },
  setup(props) {
    const pct = computed(() => Math.round(props.score || 0));
    const color = computed(() => {
      if (pct.value >= 75) return 'bg-green-500';
      if (pct.value >= 50) return 'bg-yellow-400';
      return 'bg-red-400';
    });
    return () => h('div', { class: 'flex items-center gap-2' }, [
      h('span', { class: 'text-xs text-gray-500 w-14 shrink-0' }, props.label),
      h('div', { class: 'flex-1 bg-gray-100 rounded-full h-1.5' },
        [h('div', { class: `h-1.5 rounded-full transition-all ${color.value}`, style: { width: `${pct.value}%` } })]
      ),
      h('span', { class: 'text-xs text-gray-500 w-8 text-right font-medium' }, `${pct.value}%`),
    ]);
  },
});
</script>
