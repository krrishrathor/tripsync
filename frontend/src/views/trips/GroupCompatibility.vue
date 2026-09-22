<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Group Compatibility</h2>
      <p class="text-sm text-gray-500 mt-1">What the group looks like as a whole</p>
    </div>

    <div v-if="prefStore.aggregateLoading" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
    </div>

    <div v-else-if="agg" class="space-y-6">

      <!-- Completion Card -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-gray-900">Preferences Submitted</h3>
          <span class="text-2xl font-bold text-blue-600">{{ agg.completion_pct }}%</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-3">
          <div class="bg-blue-600 h-3 rounded-full transition-all duration-500"
            :style="{ width: agg.completion_pct + '%' }"></div>
        </div>
        <p class="text-xs text-gray-500 mt-2">
          {{ agg.preferences_submitted }} of {{ agg.member_count }} members have submitted preferences
        </p>
      </div>

      <!-- Conflicts -->
      <div v-if="agg.conflicts?.length" class="space-y-3">
        <h3 class="font-semibold text-gray-700 text-sm uppercase tracking-wide">⚠️ Group Conflicts Detected</h3>
        <div v-for="conflict in agg.conflicts" :key="conflict.type"
          class="flex gap-3 p-4 rounded-lg"
          :class="conflict.severity === 'warning' ? 'bg-amber-50 border border-amber-200' : 'bg-blue-50 border border-blue-200'">
          <span class="text-lg">{{ conflict.severity === 'warning' ? '⚠️' : 'ℹ️' }}</span>
          <p class="text-sm text-gray-700">{{ conflict.message }}</p>
        </div>
      </div>
      <div v-else-if="agg.preferences_submitted > 0"
        class="bg-green-50 border border-green-200 p-4 rounded-lg text-sm text-green-700">
        ✅ No major conflicts detected in the group!
      </div>

      <!-- Budget -->
      <div v-if="agg.budget" class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="font-semibold text-gray-900 mb-4">💰 Budget Summary</h3>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-xs text-gray-500 mb-1">Median Max</p>
            <p class="text-lg font-bold text-gray-900">₹{{ fmt(agg.budget.median_max_budget) }}</p>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-xs text-gray-500 mb-1">Lowest Max</p>
            <p class="text-lg font-bold text-amber-600">₹{{ fmt(agg.budget.lowest_max_budget) }}</p>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-xs text-gray-500 mb-1">Highest Max</p>
            <p class="text-lg font-bold text-green-600">₹{{ fmt(agg.budget.highest_max_budget) }}</p>
          </div>
          <div class="text-center p-3 bg-blue-50 rounded-lg">
            <p class="text-xs text-blue-600 mb-1">Plan Around</p>
            <p class="text-lg font-bold text-blue-700">₹{{ fmt(agg.budget.group_min_acceptable) }}</p>
          </div>
        </div>
      </div>

      <!-- Interests -->
      <div v-if="agg.interests" class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 class="font-semibold text-gray-900 mb-4">🎯 Interest Compatibility</h3>
        <div class="space-y-2">
          <div v-for="item in agg.interests.all_ranked" :key="item.interest" class="flex items-center gap-3">
            <span class="w-24 text-sm text-gray-700 capitalize">{{ item.interest }}</span>
            <div class="flex-1 bg-gray-100 rounded-full h-2">
              <div class="h-2 rounded-full transition-all duration-500"
                :class="item.pct >= 50 ? 'bg-blue-500' : 'bg-gray-300'"
                :style="{ width: item.pct + '%' }"></div>
            </div>
            <span class="text-xs text-gray-500 w-12 text-right">{{ item.count }} / {{ agg.preferences_submitted }}</span>
          </div>
        </div>
      </div>

      <!-- Distribution cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 class="font-semibold text-gray-900 mb-3">🏨 Accommodation</h3>
          <DistributionPills :distribution="agg.accommodation?.distribution" />
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 class="font-semibold text-gray-900 mb-3">🏃 Activity Level</h3>
          <DistributionPills :distribution="agg.activity_intensity?.distribution" />
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 class="font-semibold text-gray-900 mb-3">✈️ Travel Style</h3>
          <DistributionPills :distribution="agg.travel_style?.distribution" />
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 class="font-semibold text-gray-900 mb-3">🍽️ Diet</h3>
          <DistributionPills :distribution="agg.diet?.distribution" />
          <div v-if="agg.diet?.allergies?.length" class="mt-3">
            <p class="text-xs text-gray-500 mb-1">Allergies to note:</p>
            <div class="flex flex-wrap gap-1">
              <span v-for="a in agg.diet.allergies" :key="a.item"
                class="px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-xs">
                {{ a.item }} ({{ a.count }})
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="bg-white p-12 rounded-xl border border-gray-100 text-center text-gray-500">
      No preferences submitted yet.
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, defineComponent, h } from 'vue';
import { useRoute } from 'vue-router';
import { usePreferenceStore } from '@/stores/preference';

const route = useRoute();
const prefStore = usePreferenceStore();
const agg = computed(() => prefStore.groupAggregate);

onMounted(() => prefStore.fetchAggregate(route.params.id));

const fmt = (n) => Number(n).toLocaleString('en-IN');

// Inline helper component for distribution pills
const DistributionPills = defineComponent({
  props: { distribution: Object },
  setup(props) {
    return () => {
      if (!props.distribution) return h('p', { class: 'text-sm text-gray-400' }, 'No data');
      return h('div', { class: 'flex flex-wrap gap-2' },
        Object.entries(props.distribution).map(([k, v]) =>
          h('span', { class: 'px-2 py-1 bg-gray-100 rounded-full text-xs text-gray-700' },
            `${k}: ${v}`)
        )
      );
    };
  },
});
</script>
