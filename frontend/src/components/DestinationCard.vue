<template>
  <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
    <!-- Image + Score Badge -->
    <div class="relative h-48 bg-gray-100 overflow-hidden">
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
        <div class="relative w-14 h-14">
          <svg class="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="2.5"/>
            <circle cx="18" cy="18" r="15.9" fill="none"
              :stroke="scoreColor" stroke-width="2.5"
              :stroke-dasharray="`${scored.overall} ${100 - scored.overall}`"
              stroke-linecap="round"/>
          </svg>
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-xs font-bold text-white drop-shadow">{{ scored.overall }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-5">
      <div class="flex items-start justify-between mb-1">
        <h3 class="font-bold text-gray-900 text-lg leading-tight">{{ scored.destination.name }}</h3>
        <span class="text-xs text-gray-400 ml-2 mt-1 whitespace-nowrap">{{ scored.destination.region }}</span>
      </div>

      <!-- Cost estimate -->
      <p class="text-sm text-blue-600 font-medium mb-2">
        ₹{{ scored.destination.estimated_daily_cost_min.toLocaleString('en-IN') }}–{{ scored.destination.estimated_daily_cost_max.toLocaleString('en-IN') }}/day per person
      </p>

      <!-- Description -->
      <p class="text-xs text-gray-500 mb-4 line-clamp-2">{{ scored.destination.description }}</p>

      <!-- Factor scores -->
      <div class="space-y-1.5 mb-4">
        <FactorBar label="Budget" :score="scored.budget.score" />
        <FactorBar label="Interests" :score="scored.interest.score" />
        <FactorBar label="Activity" :score="scored.activity.score" />
      </div>

      <!-- Highlights -->
      <div v-if="scored.highlights?.length" class="mb-3">
        <p v-for="h in scored.highlights.slice(0,2)" :key="h" class="text-xs text-green-700 flex items-start gap-1">
          <span class="mt-0.5">✓</span><span>{{ h }}</span>
        </p>
      </div>

      <!-- Conflicts -->
      <div v-if="scored.conflicts?.length" class="mb-3">
        <p v-for="c in scored.conflicts.slice(0,2)" :key="c" class="text-xs text-amber-700 flex items-start gap-1">
          <span class="mt-0.5">⚠</span><span class="line-clamp-2">{{ c }}</span>
        </p>
      </div>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1 mb-4">
        <span
          v-for="tag in scored.destination.tags.slice(0,4)"
          :key="tag"
          class="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600 capitalize"
        >{{ tag }}</span>
      </div>

      <!-- Match label -->
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold px-2.5 py-1 rounded-full" :class="matchClass">
          {{ matchLabel }}
        </span>
        <span class="text-xs text-gray-400">{{ scored.destination.typical_duration_days_min }}–{{ scored.destination.typical_duration_days_max }} days</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h } from 'vue';

const props = defineProps({
  scored: { type: Object, required: true },
  rank: { type: Number, required: true },
});

const scoreColor = computed(() => {
  const s = props.scored.overall;
  if (s >= 75) return '#22c55e';
  if (s >= 55) return '#f59e0b';
  return '#ef4444';
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
      h('span', { class: 'text-xs text-gray-500 w-8 text-right' }, `${pct.value}%`),
    ]);
  },
});
</script>
