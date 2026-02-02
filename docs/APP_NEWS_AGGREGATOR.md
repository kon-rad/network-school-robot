# Personal News Intelligence Agent

A personalized crypto and AI news aggregator that recognizes individuals, remembers their interests, and delivers tailored briefings through conversational interaction.

## Core Concept

The robot acts as your **personal news analyst** - not just reading headlines, but understanding what matters to *you* specifically, remembering your portfolio, tracking topics you care about, and having ongoing conversations about developments in crypto and AI.

---

## User Recognition & Profiles

### How Recognition Works

1. **Voice Recognition** - Identifies users by voice patterns
2. **Wake Phrase** - "Hey [robot name], it's [Name]"
3. **Face Recognition** - Camera identifies known users (optional)
4. **Explicit Identification** - User states their name

### User Profile Structure

```json
{
  "user_id": "konrad_001",
  "name": "Konrad",
  "voice_print": "...",
  "face_embedding": "...",
  "created_at": "2025-01-15",
  "last_interaction": "2025-02-02",

  "interests": {
    "crypto": {
      "tokens": ["ETH", "SOL", "LINK", "ARB"],
      "protocols": ["Uniswap", "Aave", "Eigenlayer"],
      "topics": ["DeFi", "L2 scaling", "MEV", "restaking"],
      "chains": ["Ethereum", "Solana", "Base"]
    },
    "ai": {
      "topics": ["agents", "robotics", "open source models", "multimodal"],
      "companies": ["Anthropic", "OpenAI", "Mistral", "Hugging Face"],
      "applications": ["coding assistants", "autonomous agents"]
    },
    "general": {
      "topics": ["longevity", "network states", "founder stories"]
    }
  },

  "portfolio": {
    "holdings": ["ETH", "SOL", "LINK"],
    "watchlist": ["ARB", "OP", "EIGEN"],
    "alert_thresholds": {
      "ETH": { "above": 5000, "below": 2000 }
    }
  },

  "preferences": {
    "briefing_depth": "detailed",  // "headlines" | "summary" | "detailed"
    "briefing_time": "09:00",
    "personality": "analytical",   // matches robot personality
    "skepticism_level": "high"     // how critical to be of news
  },

  "conversation_history": [
    {
      "date": "2025-02-01",
      "topics_discussed": ["Ethereum roadmap", "Claude 3.5"],
      "opinions_expressed": {
        "ETH_scaling": "bullish on L2s, skeptical of sharding timeline"
      },
      "questions_asked": ["What's the status of EIP-4844?"],
      "follow_ups_promised": ["Track Dencun upgrade progress"]
    }
  ]
}
```

---

## News Sources & Aggregation

### Crypto News Sources

| Source | Type | API/Method | Update Frequency |
|--------|------|------------|------------------|
| CoinDesk | News | RSS/Scrape | Real-time |
| The Block | News | RSS/Scrape | Real-time |
| Bankless | Analysis | RSS | Daily |
| On-chain data | Metrics | Dune/DeFiLlama API | Hourly |
| Crypto Twitter | Social | Twitter API | Real-time |
| Farcaster | Social | Neynar API | Real-time |
| Governance | Proposals | Snapshot/Tally API | As needed |
| GitHub | Development | GitHub API | Daily |

### AI News Sources

| Source | Type | API/Method | Update Frequency |
|--------|------|------------|------------------|
| arXiv | Papers | arXiv API | Daily |
| Hacker News | Discussion | HN API | Hourly |
| AI Twitter | Social | Twitter API | Real-time |
| Company blogs | Announcements | RSS | As published |
| Hugging Face | Models | HF API | Daily |
| Product Hunt | Launches | PH API | Daily |

### News Processing Pipeline

```
Raw Sources → Deduplication → Relevance Scoring → Summarization → Storage
                                    ↓
                            User Interest Matching
                                    ↓
                            Personalized Queue
```

---

## Conversation Modes

### 1. Morning Briefing

**Trigger:** Scheduled time or "Give me my morning briefing"

**Flow:**
```
Robot: "Good morning, Konrad. I have 3 important updates for you today.

First, Ethereum - gas fees dropped 40% overnight after the latest
blob capacity increase. This affects your L2 positions positively.

Second, Anthropic announced Claude 4 with improved agentic capabilities.
Given your interest in AI agents, I thought you'd want to know early.

Third, there's a governance vote on Uniswap about fee switch activation.
You mentioned caring about this last month. Voting ends in 48 hours.

Want me to go deeper on any of these?"
```

**Physical behavior:** Alert posture, gestures toward user, antenna movements to emphasize points

### 2. Topic Deep Dive

**Trigger:** "Tell me more about [topic]" or "What's happening with [protocol]?"

**Flow:**
```
User: "What's happening with Eigenlayer?"

Robot: "Eigenlayer has had a busy week. Three main developments:

[Tilts head thoughtfully]

The restaking TVL crossed $15 billion, up 20% this month. However,
there's growing debate about systemic risk - Vitalik posted concerns
about consensus overload.

[Nods]

They also announced support for Cosmos chains, which expands the
addressable market significantly.

Lastly, the EIGEN token unlock is in 3 weeks. Based on your skepticism
about token unlocks we discussed before, you might want to watch for
selling pressure.

Should I set an alert for the unlock date?"
```

### 3. Opinion & Analysis Request

**Trigger:** "What do you think about [topic]?" or "Should I be worried about [event]?"

**Flow:**
```
User: "Should I be worried about the SEC lawsuit against [exchange]?"

Robot: [Pauses, antenna droop slightly]

"Based on historical patterns, these cases typically take 18-24 months
to resolve. The immediate price impact is usually short-term.

However, I know you hold tokens that might be classified as securities
in your portfolio. The precedent matters more than this specific case.

[Straightens up]

My honest take: The regulatory clarity, even if painful, might actually
be bullish long-term. But I'd want to know your time horizon before
giving specific thoughts on your positions.

What's your thinking?"
```

### 4. Quick Check

**Trigger:** "Quick update on [token/topic]" or "Price of [token]?"

**Flow:**
```
User: "Quick update on ETH"

Robot: "$3,247, up 2.3% today. Network activity normal.
No major news since your last check. [Brief nod]"
```

### 5. Follow-Up & Memory

**Trigger:** Robot proactively follows up on previous conversations

**Flow:**
```
Robot: "Konrad, quick follow-up - remember last week you asked about
the Arbitrum Stylus launch? It went live yesterday. Early benchmarks
show 10x gas savings for compute-heavy contracts.

Given your interest in L2 development, thought you'd want to know.
Want the technical details?"
```

---

## Memory & Learning

### What the Robot Remembers

**Per User:**
- Topics they've asked about
- Opinions they've expressed
- Tokens/protocols they care about
- Questions they've asked (for follow-up)
- Preferred briefing style
- How skeptical/optimistic they are
- Their knowledge level on topics

**Across Users:**
- What topics are trending in the community
- Common questions being asked
- Sentiment shifts over time

### Learning Loop

```
Interaction → Extract Interests → Update Profile → Better Personalization
      ↓
  Feedback (explicit or implicit)
      ↓
  Adjust relevance scoring
```

### Explicit Feedback

- "That's not relevant to me" → Reduce weight on topic
- "Tell me more about this" → Increase weight
- "Add [token] to my watchlist" → Direct profile update
- "I don't care about [topic]" → Exclude from future briefings

---

## Alert System

### Alert Types

| Type | Trigger | Example |
|------|---------|---------|
| Price Alert | Threshold crossed | "ETH just broke $4,000" |
| News Alert | High-relevance story | "Breaking: Major protocol hack" |
| Governance | Vote deadline approaching | "Uniswap vote ends in 6 hours" |
| Follow-up | Previous conversation topic | "Update on that thing you asked about" |
| Portfolio | Significant movement | "Your watchlist token ARB is up 15%" |

### Alert Delivery

- **Immediate:** Critical news (hacks, major announcements)
- **Batched:** Regular updates grouped into briefings
- **Scheduled:** Morning/evening briefings at user-preferred times

---

## Technical Implementation

### New Services Needed

```
backend/app/services/
├── news_aggregator_service.py    # Fetches and processes news
├── user_profile_service.py       # Manages user profiles and memory
├── relevance_scoring_service.py  # Matches news to user interests
└── alert_service.py              # Manages alerts and notifications
```

### Data Storage

```
backend/data/
├── users/
│   ├── konrad_001.json           # User profile
│   ├── alice_002.json
│   └── ...
├── news/
│   ├── crypto/
│   │   └── 2025-02-02.json       # Daily news cache
│   └── ai/
│       └── 2025-02-02.json
└── conversations/
    ├── konrad_001/
    │   └── 2025-02-02.json       # Daily conversation log
    └── ...
```

### API Endpoints

```python
# User management
POST   /api/users/identify          # Identify user (voice/face/name)
GET    /api/users/{user_id}/profile # Get user profile
PATCH  /api/users/{user_id}/profile # Update interests/preferences

# News
GET    /api/news/briefing/{user_id} # Get personalized briefing
GET    /api/news/topic/{topic}      # Get news on specific topic
POST   /api/news/refresh            # Force refresh news sources

# Alerts
GET    /api/alerts/{user_id}        # Get pending alerts
POST   /api/alerts/{user_id}        # Create new alert
DELETE /api/alerts/{alert_id}       # Remove alert
```

### Integration with Existing Services

```python
# In chat_service.py - Add news context to conversations

async def get_chat_response(user_id: str, message: str):
    # Load user profile for personalization
    user_profile = await user_profile_service.get_profile(user_id)

    # Check if this is a news-related query
    if is_news_query(message):
        news_context = await news_aggregator_service.get_relevant_news(
            user_id=user_id,
            query=message,
            interests=user_profile.interests
        )

    # Include conversation history for continuity
    history = await get_conversation_history(user_id, limit=10)

    # Generate response with full context
    response = await openai_service.chat(
        message=message,
        system_prompt=build_news_analyst_prompt(user_profile),
        context={
            "news": news_context,
            "history": history,
            "user_interests": user_profile.interests
        }
    )

    # Log conversation for memory
    await log_conversation(user_id, message, response)

    return response
```

---

## Sample Interactions

### First Meeting

```
User: "Hey robot, I'm Konrad"

Robot: "Nice to meet you, Konrad! I'm your personal news analyst.

To give you the best briefings, I'd like to learn what you're
interested in.

Are you more focused on crypto, AI, or both?
And within crypto - are you a DeFi person, NFTs, infrastructure,
or something else?

[Attentive posture, slight head tilt]"
```

### Returning User

```
User: "Good morning"

Robot: "Morning, Konrad! [Perks up]

Quick heads up before your briefing - that Arbitrum proposal you
were tracking? It passed with 78% approval.

Ready for your full morning update, or want to start with coffee first?"
```

### Building Context Over Time

```
# Week 1
User: "What's happening with Solana?"
Robot: [Gives general Solana news]

# Week 4 (after many conversations)
User: "What's happening with Solana?"
Robot: "Three things relevant to your Solana interests:

The Firedancer client hit testnet - you mentioned caring about
client diversity last month.

Jupiter launched a new perps product, which matters for your
DeFi focus.

And there's drama about the foundation's token sales, but knowing
your 'ignore the noise' philosophy, I'll skip the details unless
you want them.

[Knowing head tilt]"
```

---

## Privacy & Data Handling

### User Controls

- View all stored data about them
- Delete conversation history
- Modify interest profiles
- Opt out of specific tracking
- Export their data

### Data Retention

- Conversation summaries: Indefinite (user can delete)
- Raw conversations: 30 days
- News cache: 7 days
- Voice/face data: Local only, never transmitted

### Transparency

- Robot explains what it remembers when asked
- "What do you know about me?" triggers profile summary
- Clear about when it's using stored context

---

## Roadmap

### Phase 1: Basic News Aggregation
- [ ] News source integrations (RSS, APIs)
- [ ] Basic summarization pipeline
- [ ] Generic briefing mode

### Phase 2: User Profiles
- [ ] User identification system
- [ ] Profile storage and management
- [ ] Interest tracking

### Phase 3: Personalization
- [ ] Relevance scoring per user
- [ ] Conversation memory
- [ ] Learning from feedback

### Phase 4: Proactive Features
- [ ] Scheduled briefings
- [ ] Alert system
- [ ] Follow-up on past conversations

### Phase 5: Advanced
- [ ] Voice recognition for identification
- [ ] Community-wide trend analysis
- [ ] Multi-user context awareness

---

*This application transforms the robot from a generic assistant into a personalized intelligence partner that grows more valuable the more you interact with it.*
