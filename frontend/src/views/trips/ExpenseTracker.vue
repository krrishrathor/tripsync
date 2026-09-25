<template>
  <div class="max-w-6xl mx-auto py-8 px-4">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <button @click="$router.push(`/trips/${route.params.id}`)" class="text-gray-500 hover:text-gray-700 mb-2 inline-block">
          ← Back to Trip Dashboard
        </button>
        <h2 class="text-3xl font-bold text-gray-900">Trip Expenses</h2>
        <p class="text-gray-500 mt-1">Track spending and settle debts automatically.</p>
      </div>
      <div>
        <button
          @click="showAddModal = true"
          class="bg-indigo-600 text-white px-5 py-2.5 rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-2 shadow-sm"
        >
          <span>➕</span> Add Expense
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          @click="activeTab = 'list'"
          :class="[activeTab === 'list' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm']"
        >
          All Expenses
        </button>
        <button
          @click="activeTab = 'settlements'"
          :class="[activeTab === 'settlements' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300', 'whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm']"
        >
          Balances & Settlements
        </button>
      </nav>
    </div>

    <div v-if="loading && !expenses.length" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
    </div>

    <!-- Expenses List Tab -->
    <div v-else-if="activeTab === 'list'">
      <div v-if="expenses.length === 0" class="text-center py-16 bg-white rounded-xl border border-dashed border-gray-300">
        <div class="text-4xl mb-3">💸</div>
        <h3 class="text-lg font-medium text-gray-900">No expenses yet</h3>
        <p class="text-gray-500 mt-1">Add your first expense to start tracking.</p>
      </div>
      
      <div v-else class="space-y-4">
        <div v-for="expense in expenses" :key="expense.id" class="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-lg">
              {{ getCategoryEmoji(expense.category) }}
            </div>
            <div>
              <h4 class="font-bold text-gray-900">{{ expense.description }}</h4>
              <p class="text-sm text-gray-500">
                Paid by <span class="font-medium text-gray-700">{{ expense.paid_by.first_name || expense.paid_by.username }}</span>
                on {{ new Date(expense.date).toLocaleDateString() }}
              </p>
            </div>
          </div>
          <div class="text-right">
            <div class="text-xl font-bold text-gray-900">₹{{ parseFloat(expense.amount).toLocaleString('en-IN') }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ expense.splits.length }} people involved</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Settlements Tab -->
    <div v-else-if="activeTab === 'settlements'">
      <div v-if="settlements.length === 0" class="text-center py-16 bg-white rounded-xl border border-dashed border-gray-300">
        <div class="text-4xl mb-3">🎉</div>
        <h3 class="text-lg font-medium text-gray-900">You're all settled up!</h3>
        <p class="text-gray-500 mt-1">No one owes anything right now.</p>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="(settlement, index) in settlements" :key="index" class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full bg-red-100 text-red-700 flex items-center justify-center font-bold">
              {{ settlement.from_user_name.charAt(0).toUpperCase() }}
            </div>
            <div class="text-gray-400">→</div>
            <div class="w-10 h-10 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-bold">
              {{ settlement.to_user_name.charAt(0).toUpperCase() }}
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm text-gray-500">
              <span class="font-bold text-gray-900">{{ settlement.from_user_name }}</span> owes <span class="font-bold text-gray-900">{{ settlement.to_user_name }}</span>
            </div>
            <div class="text-2xl font-bold text-indigo-600">₹{{ parseFloat(settlement.amount).toLocaleString('en-IN') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Expense Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h3 class="font-bold text-gray-900">Add an Expense</h3>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        
        <form @submit.prevent="submitExpense" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <input v-model="newExpense.description" type="text" required placeholder="e.g. Dinner at Mario's" class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" />
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Amount (₹)</label>
              <input v-model.number="newExpense.amount" type="number" step="0.01" min="1" required class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select v-model="newExpense.category" class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                <option value="Food">Food 🍔</option>
                <option value="Transport">Transport 🚕</option>
                <option value="Accommodation">Accommodation 🏨</option>
                <option value="Activities">Activities 🎟️</option>
                <option value="Other">Other 🛒</option>
              </select>
            </div>
          </div>

          <div class="pt-4 border-t border-gray-100">
            <h4 class="text-sm font-medium text-gray-900 mb-2">Split exactly among:</h4>
            <div class="space-y-2 max-h-48 overflow-y-auto pr-2">
              <div v-for="member in tripMembers" :key="member.user.id" class="flex items-center justify-between text-sm">
                <div class="flex items-center gap-2">
                  <input type="checkbox" :id="'user_'+member.user.id" v-model="splitSelections[member.user.id].included" @change="recalculateSplits" class="rounded text-indigo-600 focus:ring-indigo-500" />
                  <label :for="'user_'+member.user.id" class="text-gray-700">{{ member.user.first_name || member.user.username }}</label>
                </div>
                <div v-if="splitSelections[member.user.id].included" class="w-24 relative">
                  <span class="absolute left-2 top-1.5 text-gray-400">₹</span>
                  <input v-model.number="splitSelections[member.user.id].amount" type="number" step="0.01" class="w-full pl-6 py-1 text-sm rounded border-gray-300 focus:border-indigo-500 focus:ring-indigo-500" />
                </div>
              </div>
            </div>
          </div>

          <div v-if="splitError" class="text-xs text-red-600 font-medium">
            {{ splitError }}
          </div>

          <div class="pt-4 mt-2 flex justify-end gap-3">
            <button type="button" @click="closeModal" class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-md border border-gray-300">Cancel</button>
            <button type="submit" :disabled="expenseStore.loading" class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md shadow-sm">
              Save Expense
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useExpenseStore } from '@/stores/expense';
import { useTripStore } from '@/stores/trip';

const route = useRoute();
const expenseStore = useExpenseStore();
const tripStore = useTripStore();

const activeTab = ref('list');
const showAddModal = ref(false);
const splitError = ref('');

const expenses = computed(() => expenseStore.expenses);
const settlements = computed(() => expenseStore.settlements);
const loading = computed(() => expenseStore.loading);
const tripMembers = computed(() => tripStore.currentTrip?.members || []);

const newExpense = reactive({
  description: '',
  amount: null,
  category: 'Food',
});

// A map of user_id -> { included: true/false, amount: number }
const splitSelections = reactive({});

onMounted(async () => {
  const tripId = route.params.id;
  await tripStore.fetchTripDetail(tripId);
  await expenseStore.fetchExpenses(tripId);
  await expenseStore.fetchSettlements(tripId);
  
  initSplitSelections();
});

const initSplitSelections = () => {
  tripMembers.value.forEach(m => {
    splitSelections[m.user.id] = { included: true, amount: 0 };
  });
};

watch(() => newExpense.amount, () => {
  recalculateSplits();
});

const recalculateSplits = () => {
  if (!newExpense.amount) return;
  const includedIds = Object.keys(splitSelections).filter(id => splitSelections[id].included);
  if (includedIds.length === 0) return;
  
  const perPerson = parseFloat((newExpense.amount / includedIds.length).toFixed(2));
  let remaining = newExpense.amount;
  
  includedIds.forEach((id, index) => {
    if (index === includedIds.length - 1) {
      splitSelections[id].amount = parseFloat(remaining.toFixed(2));
    } else {
      splitSelections[id].amount = perPerson;
      remaining -= perPerson;
    }
  });
};

const getCategoryEmoji = (category) => {
  const map = { Food: '🍔', Transport: '🚕', Accommodation: '🏨', Activities: '🎟️', Other: '🛒' };
  return map[category] || '💸';
};

const closeModal = () => {
  showAddModal.value = false;
  newExpense.description = '';
  newExpense.amount = null;
  newExpense.category = 'Food';
  initSplitSelections();
  splitError.value = '';
};

const submitExpense = async () => {
  splitError.value = '';
  
  // Calculate total from inputs
  let totalSplits = 0;
  const finalSplits = [];
  
  for (const [id, data] of Object.entries(splitSelections)) {
    if (data.included && data.amount > 0) {
      totalSplits += data.amount;
      finalSplits.push({ user_id: parseInt(id), amount: data.amount });
    }
  }
  
  if (Math.abs(totalSplits - newExpense.amount) > 0.05) {
    splitError.value = `Split amounts (₹${totalSplits.toFixed(2)}) do not match the total expense (₹${newExpense.amount}).`;
    return;
  }
  
  if (finalSplits.length === 0) {
    splitError.value = "You must split the expense with at least one person.";
    return;
  }

  try {
    await expenseStore.addExpense(route.params.id, {
      ...newExpense,
      splits: finalSplits
    });
    closeModal();
  } catch (err) {
    splitError.value = err.response?.data?.detail || "An error occurred while adding the expense.";
  }
};
</script>
