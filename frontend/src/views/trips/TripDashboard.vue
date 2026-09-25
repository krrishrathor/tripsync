<template>
  <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <div v-if="tripStore.loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
    </div>
    
    <div v-else-if="trip" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex justify-between items-start">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">{{ trip.name }}</h1>
          <p class="text-gray-500 mt-2">{{ trip.description }}</p>
          <div class="mt-4 flex space-x-4 text-sm text-gray-600">
            <span v-if="trip.start_date">📅 {{ trip.start_date }} to {{ trip.end_date }}</span>
            <span v-if="trip.total_budget">💰 {{ trip.currency }} {{ trip.total_budget }}</span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {{ trip.status }}
            </span>
          </div>
        </div>
        
        <!-- Invite Section -->
        <div class="bg-gray-50 p-4 rounded-lg border border-gray-200 min-w-[250px]">
          <h3 class="text-sm font-medium text-gray-900 mb-2">Invite Friends</h3>
          <div v-if="trip.invite_code">
            <div class="flex items-center space-x-2">
              <input type="text" readonly :value="inviteLink" class="block w-full text-xs border-gray-300 rounded-md shadow-sm bg-white px-2 py-1">
              <button @click="copyInvite" class="p-1 bg-gray-200 rounded hover:bg-gray-300 text-xs font-medium">Copy</button>
            </div>
          </div>
          <div v-else-if="isOwner">
            <button @click="generateInvite" class="w-full text-xs bg-blue-600 text-white px-3 py-2 rounded shadow-sm hover:bg-blue-700">Generate Invite Link</button>
          </div>
          <div v-else class="text-xs text-gray-500">Only the owner can invite.</div>
        </div>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Members List -->
        <div class="col-span-1 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-lg font-bold text-gray-900 border-b pb-3 mb-4">Members ({{ trip.members?.length }})</h2>
          <ul class="space-y-3">
            <li v-for="member in trip.members" :key="member.id" class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-800 font-bold text-sm">
                  {{ member.user.first_name?.[0] || member.user.username[0] }}
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ member.user.first_name }} {{ member.user.last_name }}</p>
                  <p class="text-xs text-gray-500">{{ member.user.username }}</p>
                </div>
              </div>
              <span v-if="member.role === 'OWNER'" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Owner</span>
            </li>
          </ul>
        </div>
        
        <!-- Action Cards / Dashboard Main Area -->
        <div class="col-span-2 space-y-6">
          <!-- Finalized Destination Banner -->
          <div v-if="trip.status === 'DESTINATION_SELECTED' || trip.status === 'ITINERARY_GENERATED'" class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 shadow-sm p-6 relative overflow-hidden">
            <div class="absolute right-0 top-0 opacity-10 text-9xl -mt-4 -mr-4">🎉</div>
            <h2 class="text-xs font-bold text-green-800 uppercase tracking-wider mb-1">Destination Locked In!</h2>
            <h3 class="text-3xl font-bold text-gray-900 mb-2">{{ trip.selected_destination_name || 'Destination Selected' }}</h3>
            <p class="text-sm text-gray-700 max-w-md relative z-10 mb-4">
              The group has spoken and the owner has finalized the destination. 
              The voting phase is now closed. Next up: Itinerary Planning!
            </p>
            <button @click="$router.push(`/trips/${trip.id}/itinerary`)"
              class="relative z-10 bg-green-700 hover:bg-green-800 text-white text-sm font-semibold px-5 py-2 rounded-lg shadow-sm transition-colors">
              {{ trip.status === 'ITINERARY_GENERATED' ? 'View Itinerary 📅' : 'Generate AI Itinerary ✨' }}
            </button>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- My Preferences -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">🎯</span>
                <h3 class="font-semibold text-gray-900">Your Preferences</h3>
              </div>
              <p class="text-sm text-gray-500 flex-1">Tell the group your budget, interests, and travel style so we can find the perfect destination.</p>
              <button @click="$router.push(`/trips/${trip.id}/preferences`)"
                class="mt-4 w-full text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium">
                Set My Preferences →
              </button>
            </div>

            <!-- Group Compatibility -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">📊</span>
                <h3 class="font-semibold text-gray-900">Group Compatibility</h3>
              </div>
              <p class="text-sm text-gray-500 flex-1">See how well the group's preferences align — budgets, interests, diet, and detected conflicts.</p>
              <button @click="$router.push(`/trips/${trip.id}/group-compatibility`)"
                class="mt-4 w-full text-sm bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700 font-medium">
                View Group Report →
              </button>
            </div>

            <!-- Destination Discovery & Voting -->
            <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col col-span-1 sm:col-span-2">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">🗺️</span>
                <h3 class="font-semibold text-gray-900">Destination Discovery & Voting</h3>
              </div>
              <p class="text-sm text-gray-500 flex-1">
                <span v-if="trip.status === 'PLANNING'">Browse destinations ranked by compatibility with your group's preferences, then vote for your favourites.</span>
                <span v-else>View the destinations and the final voting results.</span>
              </p>
              <button @click="$router.push(`/trips/${trip.id}/destinations`)"
                class="mt-4 w-full text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium">
                {{ trip.status === 'PLANNING' ? 'Discover & Vote →' : 'View Final Results →' }}
              </button>
            </div>

            <!-- Expenses & Settlements -->
            <div v-if="trip.status === 'DESTINATION_SELECTED' || trip.status === 'ITINERARY_GENERATED'" class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col col-span-1 sm:col-span-2">
              <div class="flex items-center gap-3 mb-3">
                <span class="text-2xl">💸</span>
                <h3 class="font-semibold text-gray-900">Expenses & Settlements</h3>
              </div>
              <p class="text-sm text-gray-500 flex-1">
                Log trip expenses, split them with the group, and automatically calculate who owes whom.
              </p>
              <button @click="$router.push(`/trips/${trip.id}/expenses`)"
                class="mt-4 w-full text-sm bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 font-medium">
                Track Expenses →
              </button>
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
import { useTripStore } from '@/stores/trip';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const tripStore = useTripStore();
const authStore = useAuthStore();

const trip = computed(() => tripStore.currentTrip);
const isOwner = computed(() => trip.value?.owner?.id === authStore.user?.id);

const inviteLink = computed(() => {
  if (!trip.value?.invite_code) return '';
  return `${window.location.origin}/join/${trip.value.invite_code}`;
});

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser();
  }
  await tripStore.fetchTripDetail(route.params.id);
});

const generateInvite = async () => {
  await tripStore.generateInvite(trip.value.id);
};

const copyInvite = () => {
  navigator.clipboard.writeText(inviteLink.value);
  alert('Invite link copied!');
};
</script>
