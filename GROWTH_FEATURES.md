# Growth Features Documentation

## Overview

The Growth Features system helps streamers increase engagement and track community growth through several integrated features:

1. **New Viewer Welcome** - Automatically welcome first-time chatters
2. **Follower Goal Progress** - Display progress toward subscriber goals
3. **Community Challenges** - Create goal-based engagement challenges
4. **Viewer Callouts** - Recognize and highlight active/loyal viewers
5. **Referral System** (Coming Soon) - Reward viewers who bring friends

## Features Explained

### 1. New Viewer Welcome 🎉

**What it does:** The bot automatically detects first-time chatters and posts a special welcome message.

**How it works:**
- When a new username appears in chat, the bot recognizes them as a first-time viewer
- A special welcome message is automatically posted
- The viewer is added to a persistent list to avoid repeated welcomes

**Example:**
```
User: "hey everyone!"
Bot: "🎉 Welcome to the stream! Glad to have you here! This is your first time chatting - hope you enjoy! 💙 - ValoMate"
```

**Configuration:**
- Automatically enabled when the bot starts
- No additional setup required

---

### 2. Follower Goal Progress 📈

**What it does:** Announces progress toward your subscriber goal at regular intervals.

**How it works:**
- Tracks current subscriber count from YouTube
- Compares against your set goal
- Posts progress announcements every 60 minutes (configurable)

**Example:**
```
Bot: "📈 LOKI is 247 followers away from 2000! Let's help reach the goal! (87.7%)"
```

**Commands:**
```
!setgoal <number>
```

**Example:**
```
!setgoal 2000
```

**Configuration:**
- Default goal: 2000
- Announcement interval: Every 60 minutes
- Can be customized via `!setgoal` command

---

### 3. Community Challenges 🎯

**What it does:** Creates chat-wide goals to motivate engagement and reward the community.

**How it works:**
- Streamer sets a message count target
- Specifies a reward for reaching the goal
- Bot tracks total messages during the stream
- When goal is met, bot announces the completion
- Community members work together toward a common goal

**Example Setup:**
```
Streamer: !challenge 500 "I'll do 50 pushups"
Bot: "🎯 Community Challenge: If chat reaches 500 messages, I'll do 50 pushups! Let's go! 🔥"
```

**Commands:**
```
!challenge <message_count> <reward_text>
!cancelchallenge              # Stop current challenge
!challengeprogress            # Check progress
```

**Example Usage:**
```
!challenge 1000 "raid the next raid target"
!challenge 300 "play ranked instead of unranked"
!challenge 750 "play with subscribers only"
```

**Configuration:**
- Message target: You set (e.g., 500, 1000)
- Reward text: You define (e.g., "do a giveaway")
- Automatically tracks progress during stream
- Can be cancelled at any time

---

### 4. Viewer Callouts 🌟

**What it does:** Periodically recognizes the most active viewers in chat.

**How it works:**
- Bot tracks message count for each viewer
- Every 30 minutes (configurable), mentions the top 3 most active chatters
- Encourages community participation and builds loyalty

**Example:**
```
Bot: "🌟 Huge thanks to john_gaming, sarah_streamer, and mike_plays for being amazing! 💪 - ValoMate"
```

**Commands:**
```
!growthstats    # View current growth statistics
!gstats         # Alias for growthstats
```

**Output Example:**
```
📊 Growth Stats: | New Viewers: 47 | Active Chatters: 23 | Top Chatter: john_gaming | Follower Goal: 247 more to 2000 | Challenge Active: Yes
```

**Configuration:**
- Callout interval: Every 30 minutes
- Top chatters recognized: Top 3
- Automatically enabled

---

## Growth Features Commands Summary

| Command | Description | Usage |
|---------|-------------|-------|
| `!setgoal` | Set follower goal | `!setgoal 2000` |
| `!goal` | Alias for setgoal | `!goal 3000` |
| `!challenge` | Start community challenge | `!challenge 500 do giveaway` |
| `!startchallenge` | Alias for challenge | `!startchallenge 1000 play ranked` |
| `!challengeprogress` | Check challenge status | `!challengeprogress` |
| `!cprogress` | Alias for challengeprogress | `!cprogress` |
| `!cancelchallenge` | Stop current challenge | `!cancelchallenge` |
| `!stopchallenge` | Alias for cancelchallenge | `!stopchallenge` |
| `!growthstats` | View growth statistics | `!growthstats` |
| `!gstats` | Alias for growthstats | `!gstats` |

---

## Configuration File

Growth features store configuration in `growth_config.json`:

```json
{
  "follower_goal": 2000,
  "new_viewers": [
    "john_gaming",
    "sarah_streamer",
    "mike_plays"
  ],
  "challenge": {
    "active": true,
    "message_target": 500,
    "reward_text": "I'll do 50 pushups",
    "start_time": 1234567890.123,
    "start_message_count": 150
  }
}
```

---

## Implementation Details

### How New Viewers Are Tracked

1. Every message that arrives is checked against stored new viewers list
2. If username not found → marked as new viewer
3. Welcome message is posted automatically
4. Username is added to persistent storage

### How Messages Are Counted

- Every message in chat increments the viewer's personal message count
- Total message count is tracked for challenge progress
- Message tracking is automatic - no configuration needed

### Timing & Intervals

- **New Viewer Welcome:** Immediate (on first message)
- **Viewer Callouts:** Every 30 minutes (configurable)
- **Follower Progress:** Every 60 minutes (configurable)
- **Challenge Progress:** Continuous (shown via `!challengeprogress`)

### Subscriber Count Updates

- Updated every 60 seconds from YouTube API
- Stored in `self.growth.current_followers`
- Used for progress calculations
- Requires valid YouTube API credentials

---

## Example Stream Scenario

```
[10:00 AM] Stream starts
[10:01] New viewer "alice" joins chat
Bot: "🎉 Welcome to the stream alice! Glad to have you here! 💙"

[10:05] Streamer posts challenge
Streamer: !challenge 400 "raid everyone"
Bot: "🎯 Community Challenge: If chat reaches 400 messages, raid everyone! Let's go! 🔥"

[10:30] Viewer callout time
Bot: "🌟 Shoutout to alice, bob, and charlie for keeping chat alive! 💙"

[10:45] Chat reaches 400 messages
Bot: "🎉 Challenge Complete! Chat reached 412 messages! raid everyone! 🎊"

[11:00] Follower progress announcement
Bot: "📈 LOKI is 180 followers away from 2000! Let's help reach the goal! (91.0%)"

[11:30] Another viewer callout
Bot: "🌟 Huge thanks to david, alice, and eve for being amazing! 💪"
```

---

## Best Practices

### Setting Effective Goals

- **Follower Goals:** Set realistic milestones (100-500 followers apart)
- **Message Challenges:** Base on typical chat activity (200-1000 messages)
- **Rewards:** Make them attainable but meaningful

### Timing Challenges

- **Start time:** Early in stream for maximum participation
- **Duration:** 20-40 minute challenges work well
- **Frequency:** 1-2 per stream for best engagement

### Maximizing Engagement

1. **Announce challenges clearly** - Explain what viewers need to do
2. **Show progress** - Use `!challengeprogress` to keep momentum
3. **Celebrate wins** - React when challenges complete
4. **Mix reward types:**
   - Gameplay (play ranked, try new game)
   - Social (raid, follow someone)
   - Entertainment (dance, song request)
   - Accessibility (slower gameplay, help new players)

---

## Troubleshooting

### Viewer not recognized as new

**Issue:** A returning viewer was welcomed as new  
**Solution:** Check `growth_config.json` to manually add them to new_viewers list

### Challenge not completing

**Issue:** Challenge message count not tracking  
**Solution:** Ensure YouTube API is working (`!ping` to test)

### Follower progress not updating

**Issue:** Subscriber count shows as 0  
**Solution:** 
- Verify YouTube API credentials are valid
- Check that OAuth token is fresh
- Ensure bot has access to channel statistics

### Commands not working

**Issue:** `!setgoal`, `!challenge` not responding  
**Solution:**
- Verify commands are registered in chat bridge
- Check bot has permission to post messages
- Review logs for errors

---

## Future Enhancements

Upcoming features for Growth Features system:

1. **Referral System** - Track who brought friends
2. **Loyalty Points** - Award points for participation
3. **Leaderboards** - Top viewers by messages/activity
4. **Custom Milestones** - More flexible challenge types
5. **Statistics Export** - Track growth over time
6. **Goal Reminders** - Notifications when milestones approach

---

## Files Modified/Created

- `app/skills/growth_features.py` - Core growth features module
- `app/commands/growth.py` - Growth features commands
- `app/youtube_integration/chat_bridge.py` - Integration with bot
- `growth_config.json` - Configuration storage

---

## Questions?

For issues or questions, check the main README.md or review the code comments in `growth_features.py`.
