import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DestinationCard from '@/components/DestinationCard.vue'

describe('DestinationCard', () => {
  const mockProps = {
    scored: {
      destination: {
        id: 1,
        name: 'Tokyo',
        country: 'Japan',
        image_url: null,
        estimated_daily_cost_min: 5000,
        estimated_daily_cost_max: 10000,
        tags: ['City', 'Culture']
      },
      match_percentage: 95.5,
      budget: { score: 9 },
      interest: { score: 10 },
      activity: { score: 8 },
      transport: { score: 7 },
      accommodation: { score: 9 },
      duration: { score: 10 },
      season_modifier: 1.0,
      conflict_flags: [],
      overall: 96
    },
    rank: 1,
    voteCount: 3,
    voters: [{ first_name: 'A' }, { first_name: 'B' }],
    isMyVote: false,
    isOwner: true,
    tripStatus: 'PLANNING',
    isVoting: false,
    isSelected: false
  }

  it('renders destination name and match percentage properly', () => {
    const wrapper = mount(DestinationCard, {
      props: mockProps
    })
    
    expect(wrapper.text()).toContain('Tokyo')
    expect(wrapper.text()).toContain('96%') // Note: scored.overall is missing from mock, I should add it.
  })

  it('emits vote event when vote button is clicked', async () => {
    const wrapper = mount(DestinationCard, {
      props: mockProps
    })
    
    // Find button by text instead of fragile class
    const buttons = wrapper.findAll('button')
    const voteBtn = buttons.find(b => b.text().includes('Vote for this'))
    
    await voteBtn.trigger('click')
    
    expect(wrapper.emitted()).toHaveProperty('vote')
  })

  it('shows Lock In button if user is owner', () => {
    const wrapper = mount(DestinationCard, {
      props: mockProps
    })
    
    expect(wrapper.text()).toContain('Lock in')
  })
})
