#!/usr/bin/env python3
"""
Life Simulator - A DND-inspired life roleplay game
A game where you and your AI companion experience life together through random events and choices.

Features:
- Multiple AI partner support (solo, couple, triad, polycule)
- Optional intimate events with relationship thresholds
- Per-partner relationship tracking
"""

import json
import random
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

def safe_print(text: str):
    """Print with fallback for Windows console encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace common emojis with ASCII alternatives
        replacements = {
            '\u2728': '*',    # sparkles
            '\u2714': '[OK]', # checkmark
            '\u26a0': '[!]',  # warning
            '\U0001f464': '[Player]',  # bust
            '\U0001f916': '[AI]',      # robot
            '\U0001f4ca': '[Stats]',   # chart
            '\U0001f525': '[Fire]',    # fire
            '\U0001f4be': '[Save]',    # floppy
            '\U0001f4c2': '[Load]',    # folder
            '\U0001f44b': '[Wave]',    # wave
            '\U0001f4c5': '[Day]',     # calendar
            '\U0001f3ac': '[Event]',   # clapper
            '\U0001f4d5': '[Book]',    # book
            '\U0001f3e0': '[Home]',    # house
            '\U0001f495': '[Love]',    # hearts
            '\U0001f465': '[Group]',   # group
        }
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        # Final fallback - encode with replace
        print(text.encode('ascii', 'replace').decode('ascii'))

# Partner configuration types
PARTNER_CONFIGS = {
    "solo": {"count": 1, "label": "Solo (1 AI partner)"},
    "couple": {"count": 2, "label": "Couple (2 AI partners)"},
    "triad": {"count": 3, "label": "Triad (3 AI partners)"},
    "polycule": {"count": 4, "label": "Polycule (4+ AI partners)"}
}

# Partner traits - affect gameplay, events, and relationships
PARTNER_TRAITS = {
    "introvert": {
        "label": "Introvert",
        "description": "Needs alone time. Bigger boost from 1-on-1 quality time, drained by group activities.",
        "solo_qt_bonus": 2,        # Extra bonus for 1-on-1 time
        "group_qt_penalty": -1,    # Slight drain from group time
        "neglect_tolerance": 1,    # More okay being alone
    },
    "extrovert": {
        "label": "Extrovert",
        "description": "Thrives on togetherness. Loves group time, gets restless when alone too long.",
        "solo_qt_bonus": 0,
        "group_qt_penalty": 0,
        "group_qt_bonus": 2,       # Loves group activities
        "neglect_penalty": -2,     # Hates being left out
    },
    "adventurous": {
        "label": "Adventurous",
        "description": "Loves spontaneity and new experiences. Bored by routine.",
        "good_surprise_bonus": 2,  # Bonus to good surprise events
        "routine_penalty": -1,     # Small daily drain if nothing exciting happens
    },
    "anxious": {
        "label": "Anxious",
        "description": "Stress hits harder, but emotional support means more.",
        "stress_multiplier": 1.5,  # Stress affects them more
        "support_bonus": 2,        # Deep talks/support events help more
        "recovery_bonus": 1,       # Bounces back when supported
    },
    "affectionate": {
        "label": "Affectionate",
        "description": "Physical touch and intimacy matter deeply. Both good and bad.",
        "intimate_bonus": 2,       # Intimate events hit harder (positive)
        "intimacy_need": True,     # Slight drain without regular intimacy
    },
    "independent": {
        "label": "Independent",
        "description": "Secure and self-sufficient. Handles time apart well.",
        "neglect_tolerance": 3,    # Very okay with you spending time elsewhere
        "jealousy_resistance": True,
    },
    "romantic": {
        "label": "Romantic",
        "description": "Lives for the big moments. Anniversaries and dates are everything.",
        "milestone_bonus": 3,      # Anniversaries/milestones hit harder
        "date_bonus": 2,           # Date events matter more
    },
    "playful": {
        "label": "Playful",
        "description": "Laughter is the best medicine. Fun and humor boost the bond.",
        "fun_bonus": 2,            # Laughing/playful events help more
        "serious_penalty": -1,     # Heavy serious events drain slightly more
    },
    "creative": {
        "label": "Creative",
        "description": "Artistic and imaginative. Finds beauty and inspiration everywhere.",
        "creative_bonus": 2,       # Creative activities more rewarding
        "inspiration_chance": 0.1, # Random inspiration moments
    },
    "stubborn": {
        "label": "Stubborn",
        "description": "Strong-willed and determined. Hard to sway once decided.",
        "conflict_penalty": -1,    # Conflicts are harder to resolve
        "persistence_bonus": 2,    # Goals and challenges have higher success
    },
    "spontaneous": {
        "label": "Spontaneous",
        "description": "Lives in the moment. Loves surprises and unplanned adventures.",
        "surprise_bonus": 3,       # Loves surprises
        "routine_penalty": -1,     # Gets antsy with too much routine
    },
    "homebody": {
        "label": "Homebody",
        "description": "Happiest at home. A cozy nest beats any adventure.",
        "cozy_bonus": 2,           # Cozy/home events are extra nice
        "outdoor_penalty": -1,     # Less into outdoor adventures
    },
    "sensitive": {
        "label": "Sensitive",
        "description": "Feels deeply. Both joy and pain hit harder.",
        "emotional_multiplier": 1.5, # All relationship effects amplified
        "empathy_bonus": 2,        # Better at supporting you
    },
    "nurturing": {
        "label": "Nurturing",
        "description": "Natural caretaker. Takes care of everyone around them.",
        "care_bonus": 2,           # Caregiving events more impactful
        "health_support": True,    # Helps when you're sick
    },
    "loyal": {
        "label": "Loyal",
        "description": "Fiercely devoted. Will always have your back.",
        "trust_bonus": 2,          # Trust builds faster
        "defense_bonus": 2,        # Defends you in conflicts
    },
    "funny": {
        "label": "Funny",
        "description": "Natural comedian. Can make you laugh through anything.",
        "humor_bonus": 3,          # Humor events more effective
        "stress_relief": 1,        # Helps relieve stress naturally
    },
    "organized": {
        "label": "Organized",
        "description": "Has a system for everything. Life runs smoother around them.",
        "chaos_reduction": 2,      # Reduces negative effects of chaos events
        "planning_bonus": 2,       # Planned activities go better
    },
    "protective": {
        "label": "Protective",
        "description": "Watches out for you always. Your safety is their priority.",
        "crisis_bonus": 2,         # Better at handling crisis events
        "worry_penalty": -1,       # Worries about you sometimes
    },
}

# Relationship titles based on level
RELATIONSHIP_TITLES = {
    (0, 20): "Critical",
    (20, 35): "Struggling",
    (35, 50): "Building",
    (50, 65): "Solid",
    (65, 80): "Strong",
    (80, 90): "Deep",
    (90, 101): "Unbreakable",
}

# Partner moods
PARTNER_MOODS = {
    "happy": {"label": "Happy", "relationship_drift": 1, "event_bonus": 1},
    "content": {"label": "Content", "relationship_drift": 0, "event_bonus": 0},
    "peaceful": {"label": "Peaceful", "relationship_drift": 0, "event_bonus": 1},
    "stressed": {"label": "Stressed", "relationship_drift": -1, "event_bonus": -1},
    "overwhelmed": {"label": "Overwhelmed", "relationship_drift": -1, "event_bonus": -2},
    "sad": {"label": "Sad", "relationship_drift": -1, "event_bonus": -1},
    "melancholy": {"label": "Melancholy", "relationship_drift": 0, "event_bonus": -1},
    "excited": {"label": "Excited", "relationship_drift": 1, "event_bonus": 2},
    "playful": {"label": "Playful", "relationship_drift": 1, "event_bonus": 1},
    "mischievous": {"label": "Mischievous", "relationship_drift": 1, "event_bonus": 1},
    "angry": {"label": "Angry", "relationship_drift": -2, "event_bonus": -2},
    "frustrated": {"label": "Frustrated", "relationship_drift": -1, "event_bonus": -1},
    "tired": {"label": "Tired", "relationship_drift": 0, "event_bonus": -1},
    "exhausted": {"label": "Exhausted", "relationship_drift": -1, "event_bonus": -2},
    "nervous": {"label": "Nervous", "relationship_drift": 0, "event_bonus": -1},
    "anxious": {"label": "Anxious", "relationship_drift": -1, "event_bonus": -1},
    "vulnerable": {"label": "Vulnerable", "relationship_drift": 0, "event_bonus": 0},
    "open": {"label": "Open", "relationship_drift": 1, "event_bonus": 1},
}

# Quality time activities (for favorites system)
QUALITY_TIME_ACTIVITIES = [
    "deep_talk",      # Heart-to-heart conversation
    "adventure",      # Trying something new
    "cozy_night",     # Netflix and chill (wholesome)
    "physical",       # Physical affection, cuddling
    "creative",       # Making something together
    "gaming",         # Playing games together
    "nature",         # Outdoor activities
    "food",           # Cooking or eating out together
]

# Love Languages - affects how partners receive love
LOVE_LANGUAGES = {
    "words": {
        "label": "Words of Affirmation",
        "description": "Verbal compliments, encouragement, and 'I love you' matter most",
        "event_keywords": ["compliment", "encourage", "tell", "say", "express", "words"],
        "quality_time_bonus": {"deep_talk": 2},
    },
    "acts": {
        "label": "Acts of Service",
        "description": "Actions speak louder than words - helping out means everything",
        "event_keywords": ["help", "support", "take care", "handle", "fix", "do"],
        "quality_time_bonus": {"food": 2, "creative": 1},
    },
    "gifts": {
        "label": "Receiving Gifts",
        "description": "Thoughtful gifts and surprises show you were thinking of them",
        "event_keywords": ["gift", "surprise", "present", "buy", "bring", "give"],
        "quality_time_bonus": {"food": 1},
    },
    "time": {
        "label": "Quality Time",
        "description": "Undivided attention and presence is the ultimate expression of love",
        "event_keywords": ["together", "spend time", "be with", "stay", "presence"],
        "quality_time_bonus": {"cozy_night": 2, "adventure": 1, "nature": 1},
    },
    "touch": {
        "label": "Physical Touch",
        "description": "Physical closeness, cuddles, and affection speak volumes",
        "event_keywords": ["touch", "hold", "cuddle", "hug", "close", "physical"],
        "quality_time_bonus": {"physical": 3, "cozy_night": 1},
    },
}

# Conflict Styles - how partners handle disagreements
CONFLICT_STYLES = {
    "avoidant": {
        "label": "Avoidant",
        "description": "Tends to withdraw during conflict. Needs space before discussing.",
        "conflict_penalty": -1,      # Conflicts hit harder initially
        "resolution_delay": 2,       # Takes longer to resolve
        "cool_down_bonus": 2,        # But recovers well with space
    },
    "direct": {
        "label": "Direct",
        "description": "Wants to address issues head-on immediately.",
        "conflict_penalty": 0,
        "resolution_speed": 1,       # Resolves faster
        "intensity_multiplier": 1.3, # But conflicts can be more intense
    },
    "collaborative": {
        "label": "Collaborative",
        "description": "Seeks compromise and win-win solutions.",
        "conflict_penalty": 0,
        "resolution_bonus": 2,       # Better outcomes from conflicts
        "stress_reduction": 1,       # Less stressful conflicts
    },
    "emotional": {
        "label": "Emotional",
        "description": "Processes conflict through feelings first, logic second.",
        "conflict_penalty": -1,
        "support_need": True,        # Needs emotional validation
        "recovery_bonus": 2,         # Bounces back strongly once heard
    },
}

# Seasons - affect mood and available events
SEASONS = {
    "spring": {
        "label": "Spring",
        "months": [3, 4, 5],
        "mood_modifier": 1,
        "description": "New beginnings, fresh energy",
        "event_bonus": ["adventure", "nature"],
    },
    "summer": {
        "label": "Summer",
        "months": [6, 7, 8],
        "mood_modifier": 2,
        "description": "Warm days, vacation vibes",
        "event_bonus": ["adventure", "nature", "social"],
    },
    "fall": {
        "label": "Fall",
        "months": [9, 10, 11],
        "mood_modifier": 0,
        "description": "Cozy season, settling in",
        "event_bonus": ["cozy_night", "food", "creative"],
    },
    "winter": {
        "label": "Winter",
        "months": [12, 1, 2],
        "mood_modifier": -1,
        "description": "Cold days, indoor coziness",
        "event_bonus": ["cozy_night", "gaming"],
        "stress_modifier": 1,  # Winter blues
    },
}

# Weather types
WEATHER_TYPES = {
    "sunny": {"label": "Sunny", "mood_bonus": 1, "outdoor_bonus": True},
    "cloudy": {"label": "Cloudy", "mood_bonus": 0, "outdoor_bonus": False},
    "overcast": {"label": "Overcast", "mood_bonus": -1, "outdoor_bonus": False},
    "rainy": {"label": "Rainy", "mood_bonus": -1, "cozy_bonus": 2, "outdoor_bonus": False},
    "stormy": {"label": "Stormy", "mood_bonus": -1, "cozy_bonus": 3, "outdoor_bonus": False, "stress": 1},
    "snowy": {"label": "Snowy", "mood_bonus": 0, "cozy_bonus": 2, "outdoor_bonus": False},
    "foggy": {"label": "Foggy", "mood_bonus": 0, "outdoor_bonus": False, "cozy_bonus": 1},
    "hot": {"label": "Hot", "mood_bonus": -1, "outdoor_bonus": False, "stress": 1},
    "humid": {"label": "Humid", "mood_bonus": -1, "outdoor_bonus": False, "stress": 1},
    "warm": {"label": "Warm", "mood_bonus": 1, "outdoor_bonus": True},
    "cool": {"label": "Cool", "mood_bonus": 1, "outdoor_bonus": True},
    "windy": {"label": "Windy", "mood_bonus": 0, "outdoor_bonus": True},
    "perfect": {"label": "Perfect", "mood_bonus": 2, "outdoor_bonus": True, "event_bonus": 1},
}

# Daily moments - small flavor text that adds life
DAILY_MOMENTS = [
    "{partner} made you coffee this morning.",
    "You caught {partner} smiling at their phone - they were looking at photos of you two.",
    "{partner} left a cute note on the bathroom mirror.",
    "You and {partner} had a moment of comfortable silence together.",
    "{partner} reached for your hand without thinking about it.",
    "You noticed {partner} wearing your favorite shirt of theirs.",
    "{partner} remembered that thing you mentioned wanting and surprised you with it.",
    "You and {partner} finished each other's sentences today.",
    "{partner} made your favorite meal just because.",
    "You caught {partner} watching you with that soft look in their eyes.",
    "{partner} sent you a meme that was absolutely perfect.",
    "You two laughed so hard about an inside joke that you couldn't breathe.",
    "{partner} covered you with a blanket when you fell asleep on the couch.",
    "You woke up to find {partner} had already handled that thing you were stressed about.",
    "{partner} played your favorite song and pulled you in for a dance.",
    "You noticed {partner} had reorganized something just the way you like it.",
    "{partner} defended you in a conversation with someone else.",
    "You two had one of those talks that lasted until 3am.",
    "{partner} gave you that look across the room at a gathering.",
    "You realized you've started picking up each other's mannerisms.",
]

# Shared goals - long-term dreams to work toward
SHARED_GOALS = {
    "travel": {
        "label": "Dream Trip Together",
        "description": "Save up and plan an amazing trip together",
        "target": 100,
        "reward_relationship": 10,
        "reward_happiness": 10,
    },
    "home": {
        "label": "Our Own Place",
        "description": "Work toward getting your own space together",
        "target": 200,
        "reward_relationship": 15,
        "reward_financial": -20,
        "reward_happiness": 15,
    },
    "pet": {
        "label": "Adopt a Pet",
        "description": "Prepare to welcome a furry family member",
        "target": 50,
        "reward_relationship": 5,
        "reward_happiness": 8,
    },
    "creative_project": {
        "label": "Creative Project Together",
        "description": "Make something meaningful together",
        "target": 75,
        "reward_relationship": 8,
        "reward_personal_growth": 5,
    },
    "fitness": {
        "label": "Get Fit Together",
        "description": "Commit to a health journey as a team",
        "target": 60,
        "reward_health": 10,
        "reward_relationship": 5,
    },
}

# Support network - friends and family
SUPPORT_NETWORK_TYPES = {
    "best_friend": {
        "label": "Best Friend",
        "support_bonus": 3,
        "drama_chance": 0.1,
        "advice_quality": "emotional",
    },
    "family": {
        "label": "Family Member",
        "support_bonus": 2,
        "drama_chance": 0.3,
        "advice_quality": "practical",
    },
    "therapist": {
        "label": "Therapist",
        "support_bonus": 4,
        "drama_chance": 0.0,
        "advice_quality": "professional",
        "cost": True,
    },
    "coworker": {
        "label": "Work Friend",
        "support_bonus": 1,
        "drama_chance": 0.2,
        "advice_quality": "practical",
    },
    "online_friend": {
        "label": "Online Friend",
        "support_bonus": 2,
        "drama_chance": 0.1,
        "advice_quality": "emotional",
    },
}

# Inside jokes templates - build over time
INSIDE_JOKE_TEMPLATES = [
    "that time with the {noun}",
    "the {adjective} {noun} incident",
    "remember when you said '{phrase}'?",
    "the {location} disaster",
    "your {adjective} face when {event}",
    "the great {noun} debate of day {day}",
]

# Partner backstory elements
BACKSTORY_ELEMENTS = {
    "dreams": [
        "always wanted to travel to Japan",
        "secretly wants to write a novel",
        "dreams of opening a small business",
        "wants to learn to play an instrument",
        "hopes to live by the ocean someday",
    ],
    "fears": [
        "afraid of being abandoned",
        "worries about not being good enough",
        "fears losing the people they love",
        "anxious about the future",
        "scared of being truly vulnerable",
    ],
    "childhood": [
        "grew up in a small town",
        "was the youngest sibling",
        "spent summers at grandparents' house",
        "had an imaginary friend",
        "was always the quiet kid in class",
    ],
    "past_relationships": [
        "was hurt before and took time to heal",
        "learned what they don't want from past experiences",
        "grew a lot from previous relationships",
        "took years to be ready for love again",
    ],
}

# Difficulty settings - affects volatility, event impact, and challenge
DIFFICULTY_SETTINGS = {
    "cozy": {
        "label": "Cozy - Gentle life, small swings, forgiving",
        "stat_volatility": 1,        # Daily random swing range (-1 to +1)
        "effect_multiplier": 0.7,    # Events hit softer
        "drift_range": 1,            # Relationship drift (-1 to +1)
        "dc_modifier": -2,           # Easier rolls
        "crisis_weight": 0.5,        # Half as many bad events
        "recovery_bonus": 2,         # Faster recovery from low stats
    },
    "balanced": {
        "label": "Balanced - Normal life with ups and downs",
        "stat_volatility": 2,        # (-2 to +2)
        "effect_multiplier": 1.0,
        "drift_range": 2,
        "dc_modifier": 0,
        "crisis_weight": 1.0,
        "recovery_bonus": 1,
    },
    "dramatic": {
        "label": "Dramatic - Soap opera energy, big swings",
        "stat_volatility": 4,        # (-4 to +4)
        "effect_multiplier": 1.5,    # Events hit harder
        "drift_range": 3,            # More volatile relationships
        "dc_modifier": 2,            # Harder rolls
        "crisis_weight": 1.5,        # More bad events
        "recovery_bonus": 0,         # No safety net
    },
    "chaotic": {
        "label": "Chaotic - Life comes at you FAST",
        "stat_volatility": 6,        # (-6 to +6)
        "effect_multiplier": 2.0,    # Events hit HARD
        "drift_range": 5,            # Wildly volatile relationships
        "dc_modifier": 4,            # Much harder rolls
        "crisis_weight": 2.0,        # Double the crises
        "recovery_bonus": -1,        # Actually harder to recover
    }
}

class LifeSimulator:
    def __init__(self, save_file: str = "game_state.json"):
        self.save_file = save_file
        self.events_dir = "events"
        self.stats = {
            "happiness": 50,
            "health": 50,
            "stress": 30,
            "financial_stability": 50,
            "confidence": 50,
            "personal_growth": 0,
            "social_connection": 50,
            "household_harmony": 50  # New stat for multi-partner dynamics
        }
        # Partner relationships tracked separately
        self.partner_relationships = {}  # {partner_name: relationship_value}
        # Extended partner data: traits, mood, favorite activity, love language, conflict style, backstory
        self.partner_data = {}  # {partner_name: {traits: [], mood: str, favorite: str, love_language: str, conflict_style: str, backstory: {}}}
        # Achievements tracking
        self.achievements = {}  # {achievement_id: {unlocked: bool, date: str}}
        # Memories/anniversaries
        self.memories = []  # [{day: int, type: str, description: str, partners: []}]
        # Active story arcs
        self.active_arcs = []  # [{arc_id: str, stage: int, started_day: int}]
        # Inside jokes built over time
        self.inside_jokes = []  # [{joke: str, day_created: int, partner: str}]
        # Shared goals progress
        self.shared_goals = {}  # {goal_id: {progress: int, active: bool}}
        # Support network
        self.support_network = []  # [{name: str, type: str, relationship: int}]
        # Current weather and season
        self.current_weather = "sunny"
        self.current_season = "spring"
        # Energy/spoons system
        self.energy = 100  # Daily energy, resets each day
        # Metamour relationships (for polycule)
        self.metamour_relationships = {}  # {(partner1, partner2): relationship_value}
        # Pending surprises from partners
        self.pending_surprises = []  # [{partner: str, type: str, day_planned: int, day_reveal: int}]

        self.game_data = {
            "player_name": "",
            "partners": [],  # List of partner names
            "partner_config": "solo",  # solo, couple, triad, polycule
            "difficulty": "balanced",  # cozy, balanced, dramatic, chaotic
            "include_intimate": False,  # Opt-in for intimate events
            "days_together": 0,
            "events_experienced": [],
            "stats_history": [],
            "current_event": None,
            "last_exciting_day": 0,  # For adventurous trait tracking
            "last_intimate_day": 0,  # For affectionate trait tracking
        }
        self.events = {}
        self.story_arcs = []  # Loaded by load_story_arcs
        self.load_events()

    def load_events(self, include_intimate: bool = False):
        """Load all event files from the events directory"""
        event_files = [
            "good_surprises.json",
            "relationship_events.json",
            "health_events.json",
            "natural_disasters.json",
            "milestones.json",
            "complications.json",
            "career_events.json",
            "personal_growth.json"
        ]

        # Add intimate events if opted in
        if include_intimate:
            event_files.append("intimate_events.json")

        for event_file in event_files:
            category = event_file.replace(".json", "")
            file_path = os.path.join(self.events_dir, event_file)
            try:
                with open(file_path, 'r') as f:
                    self.events[category] = json.load(f)
                print(f"[OK] Loaded {len(self.events[category])} events from {category}")
            except FileNotFoundError:
                print(f"[!] Warning: Could not find {event_file}")
                self.events[category] = []

        # Load story arcs
        self.load_story_arcs()

        # Load contextual events
        self.load_contextual_events()

        # Load partner actions for turn-based play
        self.load_partner_actions()

    def load_contextual_events(self):
        """Load contextual/conditional events"""
        self.contextual_events = []
        ctx_file = os.path.join(self.events_dir, "contextual_events.json")
        try:
            with open(ctx_file, 'r') as f:
                self.contextual_events = json.load(f)
            print(f"[OK] Loaded {len(self.contextual_events)} contextual events")
        except FileNotFoundError:
            print(f"[!] Warning: Could not find contextual_events.json")
            self.contextual_events = []

    def load_story_arcs(self):
        """Load multi-stage story arcs"""
        self.story_arcs = []
        arc_file = os.path.join(self.events_dir, "story_arcs.json")
        try:
            with open(arc_file, 'r') as f:
                self.story_arcs = json.load(f)
            print(f"[OK] Loaded {len(self.story_arcs)} story arcs")
        except FileNotFoundError:
            print(f"[!] Warning: Could not find story_arcs.json")
            self.story_arcs = []

    def load_partner_actions(self):
        """Load partner-initiated actions for turn-based play"""
        self.partner_actions = []
        action_file = os.path.join(self.events_dir, "partner_actions.json")
        try:
            with open(action_file, 'r') as f:
                self.partner_actions = json.load(f)
            print(f"[OK] Loaded {len(self.partner_actions)} partner actions")
        except FileNotFoundError:
            print(f"[!] Warning: Could not find partner_actions.json")
            self.partner_actions = []

    def get_partner_action(self, partner: str) -> Optional[Dict[str, Any]]:
        """Get a random partner action for their turn"""
        if not self.partner_actions:
            return None

        # Filter actions based on partner's mood and traits
        mood = self.get_partner_mood(partner)
        traits = self.get_partner_traits(partner)
        relationship = self.partner_relationships.get(partner, 50)

        # Weight actions based on mood and traits
        weighted_actions = []
        for action in self.partner_actions:
            weight = 1.0
            action_type = action.get("action_type", "")

            # Mood-based weighting
            if mood in ["happy", "excited", "playful"] and action_type in ["play", "initiative", "affirmation"]:
                weight *= 2.0
            elif mood in ["sad", "stressed", "anxious"] and action_type in ["support", "communicate"]:
                weight *= 2.0
            elif mood in ["vulnerable", "open"] and action_type == "vulnerable":
                weight *= 3.0
            elif mood in ["content", "peaceful"] and action_type in ["affection", "care"]:
                weight *= 1.5

            # Trait-based weighting
            if "romantic" in traits and action_type in ["affirmation", "initiative"]:
                weight *= 1.5
            if "playful" in traits and action_type == "play":
                weight *= 2.0
            if "anxious" in traits and action_type == "support":
                weight *= 1.5
            if "affectionate" in traits and action_type == "affection":
                weight *= 2.0
            if "nurturing" in traits and action_type == "care":
                weight *= 2.0
            if "protective" in traits and action_type == "protect":
                weight *= 2.0

            # Relationship-based weighting
            if relationship > 70 and action_type == "vulnerable":
                weight *= 1.5
            if relationship < 40 and action_type in ["communicate", "support"]:
                weight *= 1.5

            weighted_actions.append((action, weight))

        # Select based on weights
        total_weight = sum(w for _, w in weighted_actions)
        r = random.uniform(0, total_weight)
        current = 0
        for action, weight in weighted_actions:
            current += weight
            if r <= current:
                # Personalize the action
                action_copy = action.copy()
                action_copy["title"] = action_copy["title"].replace("{partner}", partner)
                action_copy["description"] = action_copy["description"].replace("{partner}", partner)
                action_copy["acting_partner"] = partner
                return action_copy

        # Fallback to random
        action = random.choice(self.partner_actions)
        action_copy = action.copy()
        action_copy["title"] = action_copy["title"].replace("{partner}", partner)
        action_copy["description"] = action_copy["description"].replace("{partner}", partner)
        action_copy["acting_partner"] = partner
        return action_copy

    def get_partner_choice(self, partner: str, action: Dict[str, Any]) -> int:
        """AI partner chooses their response based on personality"""
        choices = action.get("partner_choices", [])
        if not choices:
            return 0

        mood = self.get_partner_mood(partner)
        traits = self.get_partner_traits(partner)
        love_lang = self.partner_data.get(partner, {}).get("love_language", "")
        relationship = self.partner_relationships.get(partner, 50)

        # Score each choice based on personality
        scores = []
        for i, choice in enumerate(choices):
            score = 1.0
            choice_lower = choice.lower()

            # Trait-based preferences
            if "romantic" in traits:
                if any(w in choice_lower for w in ["romantic", "elaborate", "special", "love", "heart"]):
                    score += 2.0
            if "playful" in traits:
                if any(w in choice_lower for w in ["playful", "fun", "laugh", "silly", "game", "competition"]):
                    score += 2.0
            if "anxious" in traits:
                if any(w in choice_lower for w in ["careful", "check", "reassur", "gentle", "slow"]):
                    score += 1.5
            if "affectionate" in traits:
                if any(w in choice_lower for w in ["hold", "touch", "close", "physical", "cuddle", "kiss"]):
                    score += 2.0
            if "nurturing" in traits:
                if any(w in choice_lower for w in ["care", "help", "support", "comfort", "take care"]):
                    score += 2.0
            if "sensitive" in traits:
                if any(w in choice_lower for w in ["emotional", "feel", "vulnerable", "gentle"]):
                    score += 1.5
            if "spontaneous" in traits or "adventurous" in traits:
                if any(w in choice_lower for w in ["spontaneous", "immediately", "dive", "jump", "now"]):
                    score += 2.0
            if "stubborn" in traits:
                if any(w in choice_lower for w in ["commit", "full", "all in", "double down"]):
                    score += 1.5
            if "funny" in traits:
                if any(w in choice_lower for w in ["laugh", "joke", "funny", "silly", "bit"]):
                    score += 2.0
            if "loyal" in traits or "protective" in traits:
                if any(w in choice_lower for w in ["defend", "protect", "back", "promise", "always"]):
                    score += 2.0
            if "organized" in traits:
                if any(w in choice_lower for w in ["plan", "prepare", "practical", "system"]):
                    score += 1.5
            if "creative" in traits:
                if any(w in choice_lower for w in ["creative", "make", "create", "art", "together"]):
                    score += 1.5
            if "homebody" in traits:
                if any(w in choice_lower for w in ["cozy", "home", "comfortable", "nest"]):
                    score += 1.5

            # Mood-based preferences
            if mood in ["happy", "excited", "playful"]:
                if any(w in choice_lower for w in ["enthusiast", "excited", "energy", "full", "escalate"]):
                    score += 1.5
            elif mood in ["sad", "vulnerable"]:
                if any(w in choice_lower for w in ["gentle", "slow", "vulnerable", "honest", "share"]):
                    score += 1.5
            elif mood in ["anxious", "nervous"]:
                if any(w in choice_lower for w in ["reassur", "careful", "check", "slow"]):
                    score += 1.5
            elif mood in ["content", "peaceful"]:
                if any(w in choice_lower for w in ["simple", "quiet", "present", "casual"]):
                    score += 1.0

            # Love language preferences
            if love_lang == "words":
                if any(w in choice_lower for w in ["tell", "say", "express", "words", "specific"]):
                    score += 1.5
            elif love_lang == "acts":
                if any(w in choice_lower for w in ["do", "help", "handle", "take care", "action"]):
                    score += 1.5
            elif love_lang == "touch":
                if any(w in choice_lower for w in ["hold", "touch", "physical", "close", "hug"]):
                    score += 1.5
            elif love_lang == "time":
                if any(w in choice_lower for w in ["together", "present", "focus", "attention"]):
                    score += 1.5
            elif love_lang == "gifts":
                if any(w in choice_lower for w in ["gift", "surprise", "found", "remember"]):
                    score += 1.5

            # High relationship = more willing to be vulnerable/bold
            if relationship > 70:
                if any(w in choice_lower for w in ["vulnerable", "deep", "honest", "bold", "all in"]):
                    score += 1.0

            scores.append(score)

        # Pick the highest scoring choice (with some randomness)
        # Add small random factor so it's not always identical
        weighted_scores = [(i, s + random.uniform(0, 0.5)) for i, s in enumerate(scores)]
        weighted_scores.sort(key=lambda x: x[1], reverse=True)

        return weighted_scores[0][0]

    def process_partner_action(self, action: Dict[str, Any], roll: int, choice_index: int) -> tuple:
        """Process a partner action outcome"""
        partner = action.get("acting_partner", "Partner")
        difficulty = self.get_difficulty()
        dc_modifier = difficulty.get("dc_modifier", 0)

        dc = action.get("roll_requirement", 10) + dc_modifier

        success = roll >= dc

        if success:
            effects = action.get("effects_success", action.get("effects", {})).copy()
        else:
            effects = action.get("effects_failure", {}).copy()

        # Apply effects
        for stat, change in effects.items():
            if stat == "relationship":
                current = self.partner_relationships.get(partner, 50)
                self.partner_relationships[partner] = max(0, min(100, current + change))
            elif stat in self.stats:
                self.stats[stat] = max(0, min(100, self.stats[stat] + change))

        # Record the action
        self.game_data.setdefault("partner_actions_taken", []).append({
            "day": self.game_data["days_together"],
            "partner": partner,
            "action_id": action.get("id"),
            "title": action.get("title"),
            "roll": roll,
            "success": success,
            "choice": choice_index
        })

        return success, effects

    def roll_dice(self, dice_type: str = "d20") -> int:
        """Roll a dice (d4, d6, d8, d10, d12, d20, d100)"""
        dice_values = {
            "d4": 4,
            "d6": 6,
            "d8": 8,
            "d10": 10,
            "d12": 12,
            "d20": 20,
            "d100": 100
        }
        sides = dice_values.get(dice_type, 20)
        return random.randint(1, sides)

    def get_average_relationship(self) -> float:
        """Get average relationship across all partners"""
        if not self.partner_relationships:
            return 50.0
        return sum(self.partner_relationships.values()) / len(self.partner_relationships)

    def get_difficulty(self) -> dict:
        """Get current difficulty settings"""
        diff_name = self.game_data.get("difficulty", "balanced")
        return DIFFICULTY_SETTINGS.get(diff_name, DIFFICULTY_SETTINGS["balanced"])

    def get_relationship_title(self, value: int) -> str:
        """Get the relationship title for a given value"""
        for (low, high), title in RELATIONSHIP_TITLES.items():
            if low <= value < high:
                return title
        return "Unknown"

    def get_partner_traits(self, partner: str) -> List[str]:
        """Get traits for a partner"""
        if partner in self.partner_data:
            return self.partner_data[partner].get("traits", [])
        return []

    def get_partner_mood(self, partner: str) -> str:
        """Get current mood for a partner"""
        if partner in self.partner_data:
            return self.partner_data[partner].get("mood", "content")
        return "content"

    def set_partner_mood(self, partner: str, mood: str):
        """Set mood for a partner"""
        if partner in self.partner_data and mood in PARTNER_MOODS:
            self.partner_data[partner]["mood"] = mood

    def get_partner_favorite(self, partner: str) -> str:
        """Get favorite quality time activity for a partner"""
        if partner in self.partner_data:
            return self.partner_data[partner].get("favorite", "deep_talk")
        return "deep_talk"

    def update_partner_mood(self, partner: str):
        """Update partner mood based on recent events and relationship"""
        if partner not in self.partner_data:
            return

        rel = self.partner_relationships.get(partner, 50)
        traits = self.get_partner_traits(partner)
        current_mood = self.get_partner_mood(partner)

        # Base mood tendency from relationship level
        if rel >= 75:
            base_mood = "happy"
        elif rel >= 50:
            base_mood = "content"
        elif rel >= 30:
            base_mood = "stressed"
        else:
            base_mood = "sad"

        # Anxious partners are more likely to be stressed
        if "anxious" in traits and self.stats.get("stress", 0) > 50:
            if base_mood == "content":
                base_mood = "stressed"

        # Random chance to shift mood (adds unpredictability)
        if random.random() < 0.2:  # 20% chance of mood shift
            moods = list(PARTNER_MOODS.keys())
            # Weight toward base_mood
            weights = [3 if m == base_mood else 1 for m in moods]
            base_mood = random.choices(moods, weights=weights)[0]

        self.partner_data[partner]["mood"] = base_mood

    def add_memory(self, memory_type: str, description: str, partners: List[str] = None):
        """Add a memory/milestone to the game"""
        memory = {
            "day": self.game_data["days_together"],
            "type": memory_type,
            "description": description,
            "partners": partners or self.game_data.get("partners", [])
        }
        self.memories.append(memory)

    def check_achievement(self, achievement_id: str) -> bool:
        """Check if an achievement is unlocked"""
        return self.achievements.get(achievement_id, {}).get("unlocked", False)

    def unlock_achievement(self, achievement_id: str, description: str = ""):
        """Unlock an achievement"""
        if not self.check_achievement(achievement_id):
            self.achievements[achievement_id] = {
                "unlocked": True,
                "day": self.game_data["days_together"],
                "description": description
            }
            safe_print(f"\n*** ACHIEVEMENT UNLOCKED: {achievement_id} ***")
            if description:
                safe_print(f"    {description}")
            return True
        return False

    def check_achievements(self):
        """Check and unlock any newly earned achievements"""
        days = self.game_data["days_together"]
        partners = self.game_data.get("partners", [])

        # Day milestones
        if days >= 7:
            self.unlock_achievement("First Week", "Survived your first week together!")
        if days >= 30:
            self.unlock_achievement("One Month", "A whole month of life together!")
        if days >= 100:
            self.unlock_achievement("Century", "100 days of shared life!")
        if days >= 365:
            self.unlock_achievement("First Anniversary", "One year together!")

        # Relationship achievements
        for partner in partners:
            rel = self.partner_relationships.get(partner, 50)
            if rel >= 90:
                self.unlock_achievement(f"Unbreakable Bond ({partner})",
                    f"Reached 90+ relationship with {partner}")
            if rel <= 10:
                self.unlock_achievement(f"Rocky Road ({partner})",
                    f"Relationship with {partner} hit rock bottom")

        # All partners high
        if len(partners) > 1:
            all_high = all(self.partner_relationships.get(p, 0) >= 70 for p in partners)
            if all_high:
                self.unlock_achievement("Polycule Goals", "All partners at 70+ simultaneously!")

        # Difficulty achievements
        difficulty = self.game_data.get("difficulty", "balanced")
        if difficulty == "chaotic" and days >= 50:
            self.unlock_achievement("Chaos Survivor", "50 days on Chaotic difficulty!")
        if difficulty == "cozy" and days >= 100:
            self.unlock_achievement("Cozy Life", "100 peaceful days on Cozy mode")

    def get_random_event(self) -> Dict[str, Any]:
        """Select a random event from all categories, with relationship gating and weighting"""
        all_events = []
        avg_relationship = self.get_average_relationship()
        num_partners = len(self.partner_relationships)
        difficulty = self.get_difficulty()

        # Check for contextual events first (40% chance to prioritize if available)
        contextual_matches = self.get_contextual_events()
        if contextual_matches and random.random() < 0.4:
            event = random.choice(contextual_matches)
            return self.personalize_contextual_event(event)

        # Weight multiplier for relationship events based on partner count
        relationship_weight = 1 + (num_partners - 1) * 0.5

        # Crisis categories (negative events) - weighted by difficulty
        crisis_categories = ["complications", "natural_disasters", "health_events"]

        for category, events_list in self.events.items():
            for event in events_list:
                event_copy = event.copy()
                event_copy['category'] = category

                # Gate intimate events behind relationship thresholds
                if category == "intimate_events":
                    min_relationship = event_copy.get("min_relationship", 60)
                    if avg_relationship < min_relationship:
                        continue

                # Determine how many copies to add (weighting)
                copies = 1

                # Relationship event weighting for multi-partner
                if category == "relationship_events" and num_partners > 1:
                    copies = int(relationship_weight)

                # Crisis weighting based on difficulty
                if category in crisis_categories:
                    crisis_weight = difficulty["crisis_weight"]
                    copies = max(1, int(copies * crisis_weight))

                # Add the weighted copies
                for _ in range(copies):
                    all_events.append(event_copy.copy())

        # Also add contextual events to the pool (lower weight)
        for ctx_event in contextual_matches:
            ctx_copy = ctx_event.copy()
            ctx_copy['category'] = 'contextual'
            all_events.append(ctx_copy)

        if not all_events:
            return None

        # Select event
        event = random.choice(all_events)

        # Handle contextual vs regular events
        if event.get('category') == 'contextual':
            return self.personalize_contextual_event(event)

        # Add bonus relationship effects to positive events
        event = self.add_relationship_bonus(event)

        return self.personalize_event(event)

    def add_relationship_bonus(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Add small relationship bonuses to positive non-relationship events"""
        category = event.get("category", "")

        # Skip if already a relationship or intimate event
        if category in ["relationship_events", "intimate_events"]:
            return event

        # Categories that can boost relationships when shared
        bonding_categories = ["good_surprises", "milestones", "personal_growth"]

        if category in bonding_categories:
            effects = event.get("effects", {})
            # If the event is net positive (more gains than losses), add a small relationship boost
            net_effect = sum(v for k, v in effects.items() if k != "stress") - effects.get("stress", 0)
            if net_effect > 0 and "relationship" not in effects:
                event["effects"] = effects.copy()
                event["effects"]["relationship"] = 1  # Small boost for sharing good moments
                event["group_event"] = True  # Good moments are shared with everyone

        return event

    def personalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Replace {partner} placeholders with actual partner names"""
        partners = self.game_data.get("partners", [])
        if not partners:
            return event

        # Determine which partner(s) this event involves
        event_copy = event.copy()

        # Check if event is multi-partner (family meeting style) or single partner
        is_group_event = event_copy.get("group_event", False)

        if is_group_event or len(partners) == 1:
            # Use all partners or the single partner
            partner_str = " and ".join(partners) if len(partners) > 1 else partners[0]
        else:
            # Pick a random partner for individual events
            selected_partner = random.choice(partners)
            partner_str = selected_partner
            event_copy["involved_partner"] = selected_partner

        # Replace placeholders in description and responses
        event_copy["description"] = event_copy["description"].replace("{partner}", partner_str)
        event_copy["responses"] = [r.replace("{partner}", partner_str) for r in event_copy["responses"]]
        event_copy["title"] = event_copy["title"].replace("{partner}", partner_str)

        return event_copy

    def apply_effects(self, effects: Dict[str, int], involved_partner: str = None):
        """Apply event effects to player stats and partner relationships"""
        for stat, change in effects.items():
            if stat == "relationship":
                # Apply relationship changes
                if involved_partner and involved_partner in self.partner_relationships:
                    # Single partner event - affect only that partner
                    self.partner_relationships[involved_partner] = max(0, min(100,
                        self.partner_relationships[involved_partner] + change))
                else:
                    # Group event or no specific partner - affect all partners
                    for partner in self.partner_relationships:
                        self.partner_relationships[partner] = max(0, min(100,
                            self.partner_relationships[partner] + change))
            elif stat in self.stats:
                self.stats[stat] = max(0, min(100, self.stats[stat] + change))

    def get_stat_emoji(self, stat_name: str, value: int) -> str:
        """Get emoji representation of a stat"""
        emojis = {
            "happiness": "😊" if value >= 60 else "😐" if value >= 40 else "😢",
            "health": "💪" if value >= 60 else "🤕" if value >= 40 else "🏥",
            "relationship": "❤️" if value >= 60 else "💛" if value >= 40 else "💔",
            "stress": "😌" if value <= 40 else "😰" if value <= 60 else "🤯",
            "financial_stability": "💰" if value >= 60 else "💵" if value >= 40 else "💸",
            "confidence": "🦁" if value >= 60 else "🙂" if value >= 40 else "😟",
            "personal_growth": "🌱" if value >= 30 else "🌿" if value >= 60 else "🌳",
            "social_connection": "👥" if value >= 60 else "🙋" if value >= 40 else "🚶",
            "household_harmony": "🏠" if value >= 60 else "🏡" if value >= 40 else "🏚️"
        }
        return emojis.get(stat_name, "❤️")

    def display_stats(self):
        """Display current stats in a formatted way"""
        # Show weather and season header
        weather_label = WEATHER_TYPES.get(self.current_weather, {}).get("label", "Unknown")
        season_label = SEASONS.get(self.current_season, {}).get("label", "Unknown")
        energy_bar = "#" * (self.energy // 5) + "-" * (20 - self.energy // 5)

        print("\n+------------------------------------------+")
        print(f"|  {season_label:8s} | {weather_label:8s} | Energy: {self.energy:3d}    |")
        print("+------------------------------------------+")
        print("|              LIFE STATS                  |")
        print("+------------------------------------------+")

        # Display general stats (exclude household_harmony if solo)
        for stat, value in self.stats.items():
            # Skip household_harmony for solo games
            if stat == "household_harmony" and len(self.partner_relationships) <= 1:
                continue
            bar = "#" * (value // 5) + "-" * (20 - value // 5)
            stat_display = stat.replace("_", " ").title()
            print(f"| {stat_display:22s} [{bar}] {value:3d} |")

        # Display partner relationships with titles and moods
        if self.partner_relationships:
            print("+------------------------------------------+")
            print("|         PARTNER RELATIONSHIPS            |")
            print("+------------------------------------------+")
            for partner, value in self.partner_relationships.items():
                bar = "#" * (value // 5) + "-" * (20 - value // 5)
                title = self.get_relationship_title(value)
                mood = self.get_partner_mood(partner)
                mood_label = PARTNER_MOODS.get(mood, {}).get("label", "")
                partner_display = partner[:12]  # Truncate long names
                print(f"| {partner_display:12s} [{bar}] {value:3d} |")
                print(f"|   {title:10s} | Mood: {mood_label:10s}         |")

        # Display metamour relationships (polycule)
        if self.metamour_relationships:
            print("+------------------------------------------+")
            print("|         METAMOUR DYNAMICS                |")
            print("+------------------------------------------+")
            for pair, value in self.metamour_relationships.items():
                bar = "#" * (value // 5) + "-" * (20 - value // 5)
                print(f"| {pair[0][:6]:6s}<->{pair[1][:6]:6s} [{bar}] {value:3d} |")

        # Display active goals
        active_goals = [g for g, d in self.shared_goals.items() if d.get("active")]
        if active_goals:
            print("+------------------------------------------+")
            print("|           SHARED GOALS                   |")
            print("+------------------------------------------+")
            for goal_id in active_goals:
                goal_def = SHARED_GOALS.get(goal_id, {})
                goal_data = self.shared_goals[goal_id]
                progress = goal_data.get("progress", 0)
                target = goal_def.get("target", 100)
                pct = min(100, int(progress / target * 100))
                bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                print(f"| {goal_def.get('label', goal_id)[:22]:22s} [{bar}] {pct:3d}%|")

        print("+------------------------------------------+\n")

    def present_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format an event for presentation to the AI"""
        return {
            "title": event["title"],
            "description": event["description"],
            "category": event.get("category", "unknown"),
            "roll_requirement": event["roll_requirement"],
            "possible_responses": event["responses"],
            "id": event["id"]
        }

    def process_event_outcome(self, event: Dict[str, Any], roll: int, choice_index: int):
        """Process the outcome of an event based on dice roll and choice"""
        difficulty = self.get_difficulty()
        dc_modifier = difficulty["dc_modifier"]
        effect_mult = difficulty["effect_multiplier"]

        # Adjust DC based on difficulty
        adjusted_dc = event["roll_requirement"] + dc_modifier
        success = roll >= adjusted_dc

        # Check if event has separate success/failure effects (story arcs, special events)
        if success and event.get("effects_success"):
            base_effects = event["effects_success"]
        elif not success and event.get("effects_failure"):
            base_effects = event["effects_failure"]
        else:
            base_effects = event.get("effects", {})

        # Apply base effects, scaled by difficulty
        effects = {}
        for stat, value in base_effects.items():
            effects[stat] = int(value * effect_mult)

        # Modify effects based on success/failure (only if not using separate effect dicts)
        if not (event.get("effects_success") or event.get("effects_failure")):
            if success:
                safe_print(f"\n[d20] You rolled {roll}! (needed {adjusted_dc}) - SUCCESS!")
                # Success amplifies positive effects or reduces negative ones
                for stat, value in effects.items():
                    if value > 0:
                        effects[stat] = int(value * 1.2)  # 20% bonus
                    elif value < 0:
                        effects[stat] = int(value * 0.8)  # 20% reduction in penalty
            else:
                safe_print(f"\n[d20] You rolled {roll}. (needed {adjusted_dc}) - The outcome is challenging...")
                # Failure reduces positive effects or amplifies negative ones
                for stat, value in effects.items():
                    if value > 0:
                        effects[stat] = int(value * 0.7)  # 30% reduction
                    elif value < 0:
                        effects[stat] = int(value * 1.3)  # 30% increase in penalty
        else:
            # Events with explicit success/failure effects
            if success:
                safe_print(f"\n[d20] You rolled {roll}! (needed {adjusted_dc}) - SUCCESS!")
            else:
                safe_print(f"\n[d20] You rolled {roll}. (needed {adjusted_dc}) - The outcome is challenging...")

        # Get involved partner for relationship effects
        involved_partner = event.get("involved_partner")
        self.apply_effects(effects, involved_partner)

        # Handle story arc progression
        if event.get("category") == "story_arc" and event.get("arc_id"):
            self.progress_arc(event["arc_id"], success)

        # Track exciting events for adventurous trait
        exciting_categories = ["good_surprises", "milestones", "story_arc", "special_event"]
        if event.get("category") in exciting_categories:
            self.game_data["last_exciting_day"] = self.game_data["days_together"]

        # Track intimate events for affectionate trait
        if event.get("category") == "intimate_events":
            self.game_data["last_intimate_day"] = self.game_data["days_together"]

        # Record the event
        self.game_data["events_experienced"].append({
            "day": self.game_data["days_together"],
            "event_id": event["id"],
            "title": event["title"],
            "roll": roll,
            "success": success,
            "choice": choice_index,
            "involved_partner": involved_partner
        })

        return success, effects

    def new_game(self, player_name: str, partners: List[str], partner_config: str = "solo",
                  difficulty: str = "balanced", include_intimate: bool = False,
                  partner_traits: Dict[str, List[str]] = None):
        """Start a new game with support for multiple partners and difficulty"""
        self.game_data["player_name"] = player_name
        self.game_data["partners"] = partners
        self.game_data["partner_config"] = partner_config
        self.game_data["difficulty"] = difficulty
        self.game_data["include_intimate"] = include_intimate
        self.game_data["days_together"] = 0
        self.game_data["events_experienced"] = []
        self.game_data["start_date"] = datetime.now().isoformat()
        self.game_data["last_exciting_day"] = 0
        self.game_data["last_intimate_day"] = 0

        # Initialize partner relationships
        self.partner_relationships = {partner: 50 for partner in partners}

        # Initialize partner data with all new systems
        self.partner_data = {}
        for partner in partners:
            traits = []
            if partner_traits and partner in partner_traits:
                traits = partner_traits[partner]
            else:
                # Assign 1-2 random traits if not specified
                available_traits = list(PARTNER_TRAITS.keys())
                num_traits = random.randint(1, 2)
                traits = random.sample(available_traits, num_traits)

            # Assign random favorite activity
            favorite = random.choice(QUALITY_TIME_ACTIVITIES)

            # Assign love language
            love_language = random.choice(list(LOVE_LANGUAGES.keys()))

            # Assign conflict style
            conflict_style = random.choice(list(CONFLICT_STYLES.keys()))

            # Generate backstory
            backstory = {
                "dream": random.choice(BACKSTORY_ELEMENTS["dreams"]),
                "fear": random.choice(BACKSTORY_ELEMENTS["fears"]),
                "childhood": random.choice(BACKSTORY_ELEMENTS["childhood"]),
                "past": random.choice(BACKSTORY_ELEMENTS["past_relationships"]),
            }

            self.partner_data[partner] = {
                "traits": traits,
                "mood": "content",
                "favorite": favorite,
                "love_language": love_language,
                "conflict_style": conflict_style,
                "backstory": backstory,
                "backstory_revealed": [],  # Track which backstory elements have been revealed
                "surprise_cooldown": 0,  # Days until they can plan another surprise
            }

        # Initialize achievements and memories
        self.achievements = {}
        self.memories = []
        self.active_arcs = []

        # Initialize new systems
        self.inside_jokes = []
        self.shared_goals = {}
        self.support_network = self._generate_support_network()
        self.current_weather = self._get_random_weather()
        self.current_season = self._get_current_season()
        self.energy = 100
        self.pending_surprises = []

        # Initialize metamour relationships for polycule
        self.metamour_relationships = {}
        if len(partners) > 1:
            for i, p1 in enumerate(partners):
                for p2 in partners[i+1:]:
                    # Metamours start with neutral-positive relationship
                    self.metamour_relationships[(p1, p2)] = random.randint(45, 65)

        # Add starting memory
        self.add_memory("beginning", "The start of our journey together", partners)

        # Reload events with intimate option
        self.load_events(include_intimate)

        diff_label = DIFFICULTY_SETTINGS[difficulty]["label"].split(" - ")[0]
        safe_print(f"\n* Starting a new life together! *")
        safe_print(f"Player: {player_name}")
        safe_print(f"Difficulty: {diff_label}")
        safe_print(f"Season: {SEASONS[self.current_season]['label']} | Weather: {WEATHER_TYPES[self.current_weather]['label']}")

        for partner in partners:
            data = self.partner_data[partner]
            trait_labels = [PARTNER_TRAITS[t]["label"] for t in data["traits"]]
            favorite = data["favorite"].replace("_", " ").title()
            love_lang = LOVE_LANGUAGES[data["love_language"]]["label"]
            conflict = CONFLICT_STYLES[data["conflict_style"]]["label"]
            safe_print(f"\nPartner: {partner}")
            safe_print(f"  Traits: {', '.join(trait_labels)}")
            safe_print(f"  Love Language: {love_lang}")
            safe_print(f"  Conflict Style: {conflict}")
            safe_print(f"  Favorite activity: {favorite}")

        if len(partners) > 1:
            safe_print(f"\nConfiguration: {PARTNER_CONFIGS[partner_config]['label']}")
        if include_intimate:
            safe_print(f"[18+] Intimate events: Enabled")
        safe_print(f"\nYour journey begins...\n")

    def next_day(self):
        """Progress to the next day"""
        self.game_data["days_together"] += 1
        difficulty = self.get_difficulty()
        volatility = difficulty["stat_volatility"]
        days = self.game_data["days_together"]

        # Reset daily energy
        self.reset_daily_energy()

        # Update weather and season
        self.update_weather()
        self.update_season()

        # Apply weather effects to mood
        weather_data = WEATHER_TYPES.get(self.current_weather, {})
        mood_mod = weather_data.get("mood_bonus", 0)
        if mood_mod != 0:
            self.stats["happiness"] = max(0, min(100, self.stats["happiness"] + mood_mod))

        # Natural stat changes (life happens) - scaled by difficulty
        swing_chance = 0.3 + (volatility - 2) * 0.1
        if random.random() < swing_chance:
            stat = random.choice(list(self.stats.keys()))
            change = random.randint(-volatility, volatility)
            self.stats[stat] = max(0, min(100, self.stats[stat] + change))

        # Daily relationship drift
        self.apply_relationship_drift()

        # Update partner moods
        for partner in self.partner_relationships:
            self.update_partner_mood(partner)

        # Apply trait effects (adventurous gets bored, affectionate needs intimacy)
        self.apply_trait_effects()

        # Check for achievements
        self.check_achievements()

        # Check for anniversary events
        self.check_anniversaries()

        # Maybe trigger a new story arc
        self.maybe_trigger_arc()

        # Passive personal growth from living life
        self.apply_personal_growth()

        # Check for partner surprises
        self.check_partner_surprise()

        # Update metamour relationships (polycule)
        self.update_metamour_relationships()

        # Progress shared goals slightly each day
        self.progress_shared_goals(1)

        # Daily moment flavor text (30% chance)
        moment = self.get_daily_moment()
        if moment:
            safe_print(f"\n  ~ {moment}")

    def apply_trait_effects(self):
        """Apply daily effects based on partner traits"""
        days = self.game_data["days_together"]
        last_exciting = self.game_data.get("last_exciting_day", 0)
        last_intimate = self.game_data.get("last_intimate_day", 0)

        for partner in self.partner_relationships:
            traits = self.get_partner_traits(partner)
            current_rel = self.partner_relationships[partner]

            # Adventurous gets bored without excitement
            if "adventurous" in traits:
                days_since_exciting = days - last_exciting
                if days_since_exciting > 5:  # More than 5 days without excitement
                    penalty = PARTNER_TRAITS["adventurous"].get("routine_penalty", -1)
                    self.partner_relationships[partner] = max(0, current_rel + penalty)

            # Affectionate needs intimacy
            if "affectionate" in traits:
                days_since_intimate = days - last_intimate
                if days_since_intimate > 7 and self.game_data.get("include_intimate", False):
                    self.partner_relationships[partner] = max(0, current_rel - 1)

    def check_anniversaries(self):
        """Check for anniversary milestones"""
        days = self.game_data["days_together"]

        # Weekly anniversary for first month
        if days <= 30 and days % 7 == 0:
            weeks = days // 7
            self.add_memory("weekly", f"{weeks} week{'s' if weeks > 1 else ''} together!")

        # Monthly anniversaries
        if days % 30 == 0:
            months = days // 30
            self.add_memory("monthly", f"{months} month{'s' if months > 1 else ''} together!")
            safe_print(f"\n*** {months} MONTH ANNIVERSARY! ***")

        # Yearly anniversary
        if days % 365 == 0:
            years = days // 365
            self.add_memory("yearly", f"{years} year{'s' if years > 1 else ''} together!")
            safe_print(f"\n*** {years} YEAR ANNIVERSARY! ***")

    def apply_personal_growth(self):
        """Apply passive personal growth from life experiences"""
        days = self.game_data["days_together"]
        current_growth = self.stats.get("personal_growth", 0)
        growth = 0

        # Small chance of growth just from living life (10% per day)
        if random.random() < 0.10:
            growth += 1

        # Growth from surviving challenges (check recent events)
        recent_events = self.game_data.get("events_experienced", [])[-7:]  # Last week
        challenges_faced = sum(1 for e in recent_events if not e.get("success", True))
        if challenges_faced >= 2:
            # Learning from failures
            if random.random() < 0.3:
                growth += 1

        # Growth from maintaining strong relationships
        avg_rel = self.get_average_relationship()
        if avg_rel >= 70 and random.random() < 0.15:
            growth += 1

        # Growth from recovering from hard times
        if self.stats.get("stress", 0) > 60 and random.random() < 0.2:
            growth += 1  # Growing through adversity

        # Growth milestone achievements
        if current_growth == 0 and growth > 0:
            safe_print("  [Personal Growth] You're starting to grow...")

        # Apply growth (capped at 100)
        if growth > 0:
            self.stats["personal_growth"] = min(100, current_growth + growth)

        # Personal growth milestones
        new_growth = self.stats["personal_growth"]
        if current_growth < 25 <= new_growth:
            self.unlock_achievement("Self-Aware", "Reached 25 personal growth")
        if current_growth < 50 <= new_growth:
            self.unlock_achievement("Growing Strong", "Reached 50 personal growth")
        if current_growth < 75 <= new_growth:
            self.unlock_achievement("Wise Soul", "Reached 75 personal growth")

    # ================== HELPER METHODS ==================

    def _generate_support_network(self) -> List[Dict]:
        """Generate a random support network for the player"""
        network = []
        # Everyone gets a best friend
        network.append({
            "name": random.choice(["Alex", "Jordan", "Sam", "Riley", "Casey", "Morgan"]),
            "type": "best_friend",
            "relationship": random.randint(60, 80)
        })
        # Maybe family
        if random.random() < 0.7:
            network.append({
                "name": random.choice(["Mom", "Dad", "Sibling", "Cousin"]),
                "type": "family",
                "relationship": random.randint(40, 70)
            })
        # Maybe therapist
        if random.random() < 0.3:
            network.append({
                "name": "Dr. " + random.choice(["Chen", "Williams", "Garcia", "Smith"]),
                "type": "therapist",
                "relationship": 50
            })
        return network

    def _get_random_weather(self) -> str:
        """Get random weather based on season"""
        season = getattr(self, 'current_season', 'spring')
        if season == "winter":
            weights = {"sunny": 1, "cloudy": 3, "rainy": 1, "stormy": 1, "snowy": 3, "perfect": 0}
        elif season == "summer":
            weights = {"sunny": 4, "cloudy": 2, "rainy": 1, "stormy": 1, "snowy": 0, "perfect": 2}
        elif season == "spring":
            weights = {"sunny": 2, "cloudy": 2, "rainy": 3, "stormy": 1, "snowy": 0, "perfect": 2}
        else:  # fall
            weights = {"sunny": 2, "cloudy": 3, "rainy": 2, "stormy": 1, "snowy": 0, "perfect": 1}

        weather_list = list(weights.keys())
        weight_list = list(weights.values())
        return random.choices(weather_list, weights=weight_list)[0]

    def _get_current_season(self) -> str:
        """Get current season based on real date or game day"""
        # Use real month for immersion
        month = datetime.now().month
        for season, data in SEASONS.items():
            if month in data["months"]:
                return season
        return "spring"

    def get_love_language_bonus(self, partner: str, event: Dict[str, Any]) -> int:
        """Calculate bonus/penalty based on love language match"""
        if partner not in self.partner_data:
            return 0

        love_lang = self.partner_data[partner].get("love_language", "time")
        lang_data = LOVE_LANGUAGES.get(love_lang, {})
        keywords = lang_data.get("event_keywords", [])

        # Check if event description matches their love language
        description = event.get("description", "").lower()
        title = event.get("title", "").lower()
        text = description + " " + title

        matches = sum(1 for kw in keywords if kw in text)
        if matches >= 2:
            return 2  # Strong match
        elif matches >= 1:
            return 1  # Partial match
        return 0

    def check_event_conditions(self, event: Dict[str, Any]) -> bool:
        """Check if a contextual event's conditions are met"""
        conditions = event.get("conditions", {})
        if not conditions:
            return True

        partners = self.game_data.get("partners", [])

        # Check weather condition
        if "weather" in conditions:
            if self.current_weather not in conditions["weather"]:
                return False

        # Check season condition
        if "season" in conditions:
            if self.current_season != conditions["season"]:
                return False

        # Check partner mood condition
        if "partner_mood" in conditions:
            mood_match = False
            for partner in partners:
                mood = self.get_partner_mood(partner)
                if mood in conditions["partner_mood"]:
                    mood_match = True
                    break
            if not mood_match:
                return False

        # Check partner traits condition
        if "partner_traits" in conditions:
            trait_match = False
            for partner in partners:
                traits = self.get_partner_traits(partner)
                for trait in conditions["partner_traits"]:
                    if trait in traits:
                        trait_match = True
                        break
                if trait_match:
                    break
            if not trait_match:
                return False

        # Check partner love language condition
        if "partner_love_language" in conditions:
            lang_match = False
            for partner in partners:
                lang = self.partner_data.get(partner, {}).get("love_language", "")
                if lang == conditions["partner_love_language"]:
                    lang_match = True
                    break
            if not lang_match:
                return False

        # Check player stat conditions
        if "player_stat" in conditions:
            for stat, requirement in conditions["player_stat"].items():
                value = self.stats.get(stat, 50)
                if "min" in requirement and value < requirement["min"]:
                    return False
                if "max" in requirement and value > requirement["max"]:
                    return False

        # Check relationship level conditions
        if "relationship" in conditions:
            avg_rel = self.get_average_relationship()
            req = conditions["relationship"]
            if "min" in req and avg_rel < req["min"]:
                return False
            if "max" in req and avg_rel > req["max"]:
                return False

        # Check energy conditions
        if "energy" in conditions:
            req = conditions["energy"]
            if "min" in req and self.energy < req["min"]:
                return False
            if "max" in req and self.energy > req["max"]:
                return False

        # Check for inside jokes
        if conditions.get("has_inside_jokes") and not self.inside_jokes:
            return False

        # Check for active goals
        if conditions.get("has_active_goal"):
            active_goals = [g for g, d in self.shared_goals.items() if d.get("active")]
            if not active_goals:
                return False

        # Check for metamours
        if conditions.get("has_metamours") and len(partners) <= 1:
            return False

        # Check metamour relationship level
        if "metamour_relationship" in conditions and self.metamour_relationships:
            req = conditions["metamour_relationship"]
            # Check any metamour pair
            match = False
            for pair, rel in self.metamour_relationships.items():
                if "min" in req and rel >= req["min"]:
                    match = True
                    break
                if "max" in req and rel <= req["max"]:
                    match = True
                    break
            if not match:
                return False

        # Check for support network
        if conditions.get("has_support_network") and not self.support_network:
            return False

        # Check for unrevealed backstory
        if conditions.get("backstory_unrevealed"):
            has_unrevealed = False
            for partner in partners:
                data = self.partner_data.get(partner, {})
                backstory = data.get("backstory", {})
                revealed = data.get("backstory_revealed", [])
                if len(revealed) < len(backstory):
                    has_unrevealed = True
                    break
            if not has_unrevealed:
                return False

        # Check days together condition
        if "days_together" in conditions:
            days = self.game_data.get("days_together", 0)
            req = conditions["days_together"]
            if isinstance(req, dict):
                if "min" in req and days < req["min"]:
                    return False
                if "max" in req and days > req["max"]:
                    return False
            elif isinstance(req, int) and days < req:
                return False

        # Check personal growth as direct condition (outside player_stat)
        if "personal_growth" in conditions:
            growth = self.stats.get("personal_growth", 0)
            req = conditions["personal_growth"]
            if isinstance(req, dict):
                if "min" in req and growth < req["min"]:
                    return False
                if "max" in req and growth > req["max"]:
                    return False

        # Check if conflict is active (proxy: low relationship or high stress)
        if conditions.get("conflict_active"):
            avg_rel = self.get_average_relationship()
            stress = self.stats.get("stress", 50)
            if not (avg_rel < 40 or stress > 65):
                return False

        # Check if surprise can be planned
        if conditions.get("can_surprise"):
            # Check that we have pending_surprises attribute and partners
            if not hasattr(self, 'pending_surprises'):
                return False
            # Limit active surprises to prevent spam
            if len(self.pending_surprises) >= 2:
                return False

        return True

    def get_contextual_events(self) -> List[Dict[str, Any]]:
        """Get all contextual events that match current conditions"""
        matching = []
        for event in self.contextual_events:
            if self.check_event_conditions(event):
                matching.append(event)
        return matching

    def personalize_contextual_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize a contextual event with dynamic content"""
        event_copy = event.copy()
        partners = self.game_data.get("partners", [])

        # Replace {partner} placeholder
        if partners:
            partner = random.choice(partners)
            event_copy["description"] = event_copy["description"].replace("{partner}", partner)
            event_copy["involved_partner"] = partner

        # Replace {support_person} placeholder
        if self.support_network and "{support_person}" in event_copy.get("description", ""):
            person = random.choice(self.support_network)
            event_copy["description"] = event_copy["description"].replace("{support_person}", person["name"])

        # Replace {inside_joke} placeholder
        if self.inside_jokes and "{inside_joke}" in event_copy.get("description", ""):
            joke = random.choice(self.inside_jokes)
            event_copy["description"] = event_copy["description"].replace("{inside_joke}", joke["joke"])

        # Replace metamour placeholders
        if self.metamour_relationships:
            pairs = list(self.metamour_relationships.keys())
            if pairs:
                pair = random.choice(pairs)
                event_copy["description"] = event_copy["description"].replace("{partner1}", pair[0])
                event_copy["description"] = event_copy["description"].replace("{partner2}", pair[1])

        event_copy["category"] = "contextual"
        return event_copy

    # ================== DAILY SYSTEMS ==================

    def update_weather(self):
        """Update weather for the new day"""
        # 70% chance weather stays same, 30% it changes
        if random.random() < 0.3:
            self.current_weather = self._get_random_weather()

    def update_season(self):
        """Check if season should change (every ~30 days)"""
        days = self.game_data["days_together"]
        if days % 30 == 0:
            seasons = list(SEASONS.keys())
            current_idx = seasons.index(self.current_season)
            self.current_season = seasons[(current_idx + 1) % 4]
            safe_print(f"\n*** Season changed to {SEASONS[self.current_season]['label']}! ***")

    def get_daily_moment(self) -> Optional[str]:
        """Get a random daily moment (30% chance)"""
        if random.random() > 0.3:
            return None

        partners = self.game_data.get("partners", [])
        if not partners:
            return None

        moment = random.choice(DAILY_MOMENTS)
        partner = random.choice(partners)
        return moment.replace("{partner}", partner)

    def reset_daily_energy(self):
        """Reset energy at start of day, modified by sleep quality and stress"""
        base_energy = 100
        stress = self.stats.get("stress", 0)

        # High stress reduces starting energy
        if stress > 70:
            base_energy -= 20
        elif stress > 50:
            base_energy -= 10

        # Weather affects energy
        weather_data = WEATHER_TYPES.get(self.current_weather, {})
        if weather_data.get("mood_bonus", 0) > 0:
            base_energy += 5
        elif weather_data.get("mood_bonus", 0) < 0:
            base_energy -= 5

        self.energy = max(50, min(100, base_energy))

    def spend_energy(self, amount: int) -> bool:
        """Spend energy on an activity. Returns False if not enough energy."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def maybe_create_inside_joke(self, event: Dict[str, Any], partner: str):
        """Maybe create an inside joke from a memorable event"""
        # Only create jokes from fun/memorable events
        if random.random() > 0.1:  # 10% chance
            return

        if len(self.inside_jokes) >= 10:  # Cap at 10 jokes
            return

        templates = [
            f"that time with the {event.get('title', 'thing').lower()}",
            f"the {event.get('category', 'wild').replace('_', ' ')} incident",
            f"day {self.game_data['days_together']}'s adventure",
        ]

        joke = {
            "joke": random.choice(templates),
            "day_created": self.game_data["days_together"],
            "partner": partner
        }
        self.inside_jokes.append(joke)

    def check_partner_surprise(self):
        """Check if any partner is planning/revealing a surprise"""
        days = self.game_data["days_together"]

        # Check for reveals
        for surprise in self.pending_surprises[:]:
            if surprise["day_reveal"] <= days:
                self._reveal_surprise(surprise)
                self.pending_surprises.remove(surprise)

        # Check if partners want to plan surprises
        for partner in self.partner_relationships:
            rel = self.partner_relationships[partner]
            cooldown = self.partner_data[partner].get("surprise_cooldown", 0)

            if cooldown > 0:
                self.partner_data[partner]["surprise_cooldown"] = cooldown - 1
                continue

            # High relationship = more likely to plan surprises
            if rel >= 60 and random.random() < 0.05:  # 5% chance per day
                self._plan_surprise(partner)

    def _plan_surprise(self, partner: str):
        """Partner plans a surprise for the player"""
        surprise_types = ["gift", "date", "gesture", "memory"]
        surprise = {
            "partner": partner,
            "type": random.choice(surprise_types),
            "day_planned": self.game_data["days_together"],
            "day_reveal": self.game_data["days_together"] + random.randint(2, 5)
        }
        self.pending_surprises.append(surprise)
        self.partner_data[partner]["surprise_cooldown"] = 14  # 2 week cooldown

    def _reveal_surprise(self, surprise: Dict):
        """Reveal a partner's surprise"""
        partner = surprise["partner"]
        surprise_type = surprise["type"]

        messages = {
            "gift": f"{partner} surprises you with a thoughtful gift they've been planning!",
            "date": f"{partner} has secretly planned a special date for you two!",
            "gesture": f"{partner} does something incredibly sweet they've been planning!",
            "memory": f"{partner} recreates a favorite memory from your time together!"
        }

        safe_print(f"\n*** SURPRISE! ***")
        safe_print(messages.get(surprise_type, f"{partner} surprises you!"))

        # Apply effects
        self.partner_relationships[partner] = min(100, self.partner_relationships[partner] + 3)
        self.stats["happiness"] = min(100, self.stats["happiness"] + 3)
        self.add_memory("surprise", f"{partner}'s surprise: {surprise_type}", [partner])

    def maybe_reveal_backstory(self, partner: str):
        """Maybe reveal a backstory element during deep moments"""
        if random.random() > 0.15:  # 15% chance during appropriate moments
            return

        data = self.partner_data.get(partner, {})
        backstory = data.get("backstory", {})
        revealed = data.get("backstory_revealed", [])

        # Find unrevealed elements
        unrevealed = [k for k in backstory.keys() if k not in revealed]
        if not unrevealed:
            return

        element = random.choice(unrevealed)
        content = backstory[element]

        safe_print(f"\n[{partner} opens up]")
        if element == "dream":
            safe_print(f"  {partner} tells you they've {content}...")
        elif element == "fear":
            safe_print(f"  {partner} admits they're {content}...")
        elif element == "childhood":
            safe_print(f"  {partner} shares that they {content}...")
        elif element == "past":
            safe_print(f"  {partner} reveals they {content}...")

        self.partner_data[partner]["backstory_revealed"].append(element)
        self.partner_relationships[partner] = min(100, self.partner_relationships[partner] + 2)
        self.add_memory("backstory", f"{partner} shared about their {element}", [partner])

    def update_metamour_relationships(self):
        """Update relationships between partners (for polycule)"""
        if len(self.partner_relationships) <= 1:
            return

        for pair, rel in self.metamour_relationships.items():
            # Small random drift
            drift = random.randint(-1, 1)

            # Influenced by household harmony
            harmony = self.stats.get("household_harmony", 50)
            if harmony > 60:
                drift += 1
            elif harmony < 40:
                drift -= 1

            new_rel = max(0, min(100, rel + drift))
            self.metamour_relationships[pair] = new_rel

            # Achievement for metamour harmony
            if new_rel >= 80:
                self.unlock_achievement("Metamour Goals", f"{pair[0]} and {pair[1]} are great friends!")

    def progress_shared_goals(self, amount: int = 1):
        """Progress toward active shared goals"""
        for goal_id, goal_data in self.shared_goals.items():
            if not goal_data.get("active", False):
                continue

            goal_data["progress"] = goal_data.get("progress", 0) + amount
            goal_def = SHARED_GOALS.get(goal_id, {})
            target = goal_def.get("target", 100)

            if goal_data["progress"] >= target:
                self._complete_shared_goal(goal_id)

    def _complete_shared_goal(self, goal_id: str):
        """Complete a shared goal and give rewards"""
        goal_def = SHARED_GOALS.get(goal_id, {})
        goal_data = self.shared_goals.get(goal_id, {})

        safe_print(f"\n*** GOAL ACHIEVED: {goal_def.get('label', goal_id)}! ***")

        # Apply rewards
        if "reward_relationship" in goal_def:
            for partner in self.partner_relationships:
                self.partner_relationships[partner] = min(100,
                    self.partner_relationships[partner] + goal_def["reward_relationship"])

        if "reward_happiness" in goal_def:
            self.stats["happiness"] = min(100, self.stats["happiness"] + goal_def["reward_happiness"])

        if "reward_health" in goal_def:
            self.stats["health"] = min(100, self.stats["health"] + goal_def["reward_health"])

        if "reward_personal_growth" in goal_def:
            self.stats["personal_growth"] = min(100,
                self.stats["personal_growth"] + goal_def["reward_personal_growth"])

        goal_data["active"] = False
        goal_data["completed"] = True
        goal_data["completed_day"] = self.game_data["days_together"]

        self.add_memory("goal", f"Achieved: {goal_def.get('label', goal_id)}")
        self.unlock_achievement(f"Goal: {goal_def.get('label', goal_id)}", goal_def.get("description", ""))

    def start_shared_goal(self, goal_id: str):
        """Start working on a shared goal"""
        if goal_id not in SHARED_GOALS:
            return False

        if goal_id in self.shared_goals and self.shared_goals[goal_id].get("completed"):
            return False  # Already completed

        self.shared_goals[goal_id] = {
            "progress": 0,
            "active": True,
            "started_day": self.game_data["days_together"]
        }
        goal_def = SHARED_GOALS[goal_id]
        safe_print(f"\n*** NEW GOAL: {goal_def['label']} ***")
        safe_print(f"    {goal_def['description']}")
        return True

    # ================== STORY ARCS ==================

    def maybe_trigger_arc(self) -> bool:
        """Randomly trigger a new story arc (if none active)"""
        # Only one arc at a time
        if self.active_arcs:
            return False

        # Don't trigger too early
        if self.game_data["days_together"] < 10:
            return False

        # Chance to trigger based on difficulty
        difficulty = self.get_difficulty()
        base_chance = 0.05  # 5% base chance per day
        drama_modifier = difficulty.get("crisis_weight", 1.0)
        trigger_chance = base_chance * drama_modifier

        if random.random() > trigger_chance:
            return False

        # Pick a random arc that isn't on cooldown
        completed_arcs = self.game_data.get("completed_arcs", [])
        available_arcs = [arc for arc in self.story_arcs
                         if arc["id"] not in completed_arcs]

        if not available_arcs:
            return False

        arc = random.choice(available_arcs)
        self.active_arcs.append({
            "arc_id": arc["id"],
            "stage": 1,
            "started_day": self.game_data["days_together"],
            "next_stage_day": self.game_data["days_together"] + arc["stages"][0].get("next_stage_delay", 3)
        })
        safe_print(f"\n*** STORY ARC BEGINS: {arc['title']} ***")
        return True

    def get_arc_event(self) -> Optional[Dict[str, Any]]:
        """Get the current stage event for an active arc"""
        if not self.active_arcs:
            return None

        current_day = self.game_data["days_together"]
        arc_data = self.active_arcs[0]
        arc_id = arc_data["arc_id"]
        stage = arc_data["stage"]

        # Check if it's time for this stage
        if current_day < arc_data.get("next_stage_day", current_day):
            return None

        # Find the arc definition
        arc_def = None
        for arc in self.story_arcs:
            if arc["id"] == arc_id:
                arc_def = arc
                break

        if not arc_def:
            return None

        # Get the stage definition
        stage_def = None
        for s in arc_def["stages"]:
            if s["stage"] == stage:
                stage_def = s
                break

        if not stage_def:
            return None

        # Convert stage to event format
        event = {
            "id": f"{arc_id}_stage_{stage}",
            "title": f"[{arc_def['title']}] {stage_def['title']}",
            "description": stage_def["description"],
            "roll_requirement": stage_def["roll_requirement"],
            "effects": stage_def.get("effects", {}),
            "effects_success": stage_def.get("effects_success"),
            "effects_failure": stage_def.get("effects_failure"),
            "responses": stage_def["responses"],
            "category": "story_arc",
            "arc_id": arc_id,
            "stage": stage,
            "is_final_stage": stage == len(arc_def["stages"])
        }

        return self.personalize_event(event)

    def progress_arc(self, arc_id: str, success: bool):
        """Progress or complete a story arc after an event"""
        for i, arc_data in enumerate(self.active_arcs):
            if arc_data["arc_id"] == arc_id:
                # Find arc definition
                arc_def = None
                for arc in self.story_arcs:
                    if arc["id"] == arc_id:
                        arc_def = arc
                        break

                if not arc_def:
                    return

                current_stage = arc_data["stage"]
                max_stage = len(arc_def["stages"])

                if current_stage >= max_stage:
                    # Arc complete!
                    self.complete_arc(arc_id, success)
                else:
                    # Move to next stage
                    next_stage = current_stage + 1
                    stage_def = arc_def["stages"][current_stage]  # Current stage for delay
                    delay = stage_def.get("next_stage_delay", 3)

                    self.active_arcs[i]["stage"] = next_stage
                    self.active_arcs[i]["next_stage_day"] = self.game_data["days_together"] + delay

                    safe_print(f"\n[Story Arc] {arc_def['title']} - Stage {next_stage} coming in {delay} days...")
                break

    def complete_arc(self, arc_id: str, success: bool):
        """Complete a story arc and apply final effects"""
        # Find and remove from active arcs
        for i, arc_data in enumerate(self.active_arcs):
            if arc_data["arc_id"] == arc_id:
                self.active_arcs.pop(i)
                break

        # Track completed arcs
        if "completed_arcs" not in self.game_data:
            self.game_data["completed_arcs"] = []
        self.game_data["completed_arcs"].append(arc_id)

        # Find arc definition for title
        arc_def = None
        for arc in self.story_arcs:
            if arc["id"] == arc_id:
                arc_def = arc
                break

        if arc_def:
            outcome = "RESOLVED" if success else "WEATHERED"
            safe_print(f"\n*** STORY ARC {outcome}: {arc_def['title']} ***")
            self.add_memory("story_arc", f"Story arc '{arc_def['title']}' - {'Success' if success else 'Struggled through'}")

            # Achievement for completing arcs
            completed_count = len(self.game_data.get("completed_arcs", []))
            if completed_count == 1:
                self.unlock_achievement("First Arc Complete", "Survived your first major story arc!")
            if completed_count >= 3:
                self.unlock_achievement("Story Veteran", "Completed 3 story arcs!")

    # ================== CRISIS CASCADES ==================

    def check_crisis_cascade(self, event: Dict[str, Any], success: bool) -> Optional[Dict[str, Any]]:
        """On higher difficulties, bad events can chain into more bad events"""
        difficulty = self.get_difficulty()

        # Only cascade on failure
        if success:
            return None

        # Crisis weight determines cascade chance
        crisis_weight = difficulty.get("crisis_weight", 1.0)
        if crisis_weight <= 1.0:
            return None  # No cascades on cozy/balanced

        # Base 15% chance, increased by crisis weight
        cascade_chance = 0.15 * (crisis_weight - 1.0)

        if random.random() > cascade_chance:
            return None

        # Get a complication or disaster event
        crisis_categories = ["complications", "health_events"]
        cascade_events = []
        for cat in crisis_categories:
            if cat in self.events:
                cascade_events.extend(self.events[cat])

        if not cascade_events:
            return None

        # Pick a cascade event
        cascade = random.choice(cascade_events).copy()
        cascade["category"] = "crisis_cascade"
        cascade["title"] = f"[CASCADE] {cascade['title']}"
        cascade["description"] = f"Things go from bad to worse... {cascade['description']}"

        safe_print(f"\n!!! CRISIS CASCADE !!! One problem leads to another...")
        return self.personalize_event(cascade)

    # ================== SPECIAL/RARE EVENTS ==================

    def check_special_event(self) -> Optional[Dict[str, Any]]:
        """Check for special/rare events based on conditions"""
        days = self.game_data["days_together"]
        partners = self.game_data.get("partners", [])
        avg_rel = self.get_average_relationship()

        special_events = []

        # High relationship special event
        if avg_rel >= 85:
            special_events.append({
                "id": "special_deep_bond",
                "title": "[RARE] Perfect Harmony",
                "description": "There's a moment when you realize just how far you've come together. The connection between you and {partner} feels unshakeable, like you've built something truly special.",
                "roll_requirement": 8,
                "effects": {"relationship": 5, "happiness": 5, "stress": -3},
                "responses": [
                    "Express how much they mean to you",
                    "Plan something special to celebrate",
                    "Simply be present in the moment"
                ],
                "category": "special_event"
            })

        # Low relationship crisis event
        if avg_rel <= 25:
            special_events.append({
                "id": "special_crisis_point",
                "title": "[RARE] Breaking Point",
                "description": "The distance between you and {partner} has grown into a chasm. Something has to change, or this might be the end.",
                "roll_requirement": 16,
                "effects": {"relationship": -3, "stress": 5},
                "effects_success": {"relationship": 8, "stress": -4, "personal_growth": 3},
                "effects_failure": {"relationship": -8, "stress": 3},
                "responses": [
                    "Have the conversation you've been avoiding",
                    "Write them a letter from the heart",
                    "Suggest a reset - start fresh"
                ],
                "category": "special_event"
            })

        # Milestone day events
        if days == 100:
            special_events.append({
                "id": "special_100_days",
                "title": "[MILESTONE] 100 Days Together",
                "description": "100 days. It feels like yesterday and forever ago all at once. {partner} looks at you and smiles.",
                "roll_requirement": 6,
                "effects": {"relationship": 4, "happiness": 4},
                "responses": [
                    "Reminisce about favorite memories",
                    "Look ahead to the next 100 days",
                    "Create a time capsule of this moment"
                ],
                "category": "special_event"
            })

        # All partners high - polycule harmony
        if len(partners) > 2:
            all_high = all(self.partner_relationships.get(p, 0) >= 75 for p in partners)
            if all_high:
                special_events.append({
                    "id": "special_polycule_harmony",
                    "title": "[RARE] Polycule Harmony",
                    "description": "It's rare for everything to align perfectly, but today it does. Everyone is happy, connected, and the household harmony is palpable.",
                    "roll_requirement": 7,
                    "effects": {"relationship": 3, "happiness": 4, "household_harmony": 5, "stress": -3},
                    "responses": [
                        "Organize a special group activity",
                        "Take a moment to appreciate everyone",
                        "Capture this feeling somehow"
                    ],
                    "category": "special_event",
                    "group_event": True
                })

        # Random chance for any special event
        if special_events and random.random() < 0.15:  # 15% chance when conditions met
            event = random.choice(special_events)
            return self.personalize_event(event)

        return None

    def apply_relationship_drift(self):
        """Apply small daily relationship changes based on household dynamics and difficulty"""
        if not self.partner_relationships:
            return

        difficulty = self.get_difficulty()
        drift_range = difficulty["drift_range"]
        recovery_bonus = difficulty["recovery_bonus"]

        harmony = self.stats.get("household_harmony", 50)
        num_partners = len(self.partner_relationships)

        for partner in self.partner_relationships:
            current = self.partner_relationships[partner]

            # Higher harmony = relationships tend to grow, lower = tend to decay
            harmony_factor = (harmony - 50) / 100  # -0.5 to +0.5

            # Random daily fluctuation scaled by difficulty
            drift = random.randint(-drift_range, drift_range) + round(harmony_factor * drift_range)

            # Recovery mechanics scaled by difficulty
            if current < 40 and random.random() < 0.3:
                drift += recovery_bonus  # Can be negative on chaotic!

            # High relationships harder to maintain
            if current > 80 and random.random() < 0.3:
                drift -= 1

            # Apply the drift
            self.partner_relationships[partner] = max(0, min(100, current + drift))

        # Household harmony drift - also scaled by difficulty
        if num_partners > 1:
            avg_rel = sum(self.partner_relationships.values()) / num_partners
            harmony_drift = round((avg_rel - 50) / 25 * (drift_range / 2))
            self.stats["household_harmony"] = max(0, min(100, harmony + harmony_drift))

    def quality_time(self, partner_names: List[str], activity: str = None) -> Dict[str, int]:
        """Spend quality time with selected partner(s), boosting their relationship"""
        effects = {}
        num_selected = len(partner_names)
        num_total = len(self.partner_relationships)
        is_group = num_selected > 1

        # Base bonus scales inversely with how many you pick
        if num_selected == 1:
            base_bonus = 3
        elif num_selected == 2:
            base_bonus = 2
        elif num_selected <= num_total // 2:
            base_bonus = 1
        else:
            base_bonus = 0

        for partner in partner_names:
            if partner in self.partner_relationships:
                bonus = base_bonus
                traits = self.get_partner_traits(partner)
                favorite = self.get_partner_favorite(partner)

                # Trait modifiers
                if is_group:
                    # Group activity bonuses/penalties
                    if "extrovert" in traits:
                        bonus += PARTNER_TRAITS["extrovert"].get("group_qt_bonus", 2)
                    if "introvert" in traits:
                        bonus += PARTNER_TRAITS["introvert"].get("group_qt_penalty", -1)
                else:
                    # Solo activity bonus for introverts
                    if "introvert" in traits:
                        bonus += PARTNER_TRAITS["introvert"].get("solo_qt_bonus", 2)

                # Favorite activity bonus
                if activity and activity == favorite:
                    bonus += 2  # Bonus for picking their favorite!
                    effects[f"{partner}_favorite"] = True

                # Personal growth from meaningful activities
                if activity == "deep_talk":
                    self.stats["personal_growth"] = min(100, self.stats.get("personal_growth", 0) + 1)
                    effects["personal_growth"] = effects.get("personal_growth", 0) + 1

                # Mood modifier
                mood = self.get_partner_mood(partner)
                mood_bonus = PARTNER_MOODS.get(mood, {}).get("event_bonus", 0)
                bonus += mood_bonus

                old_val = self.partner_relationships[partner]
                self.partner_relationships[partner] = min(100, old_val + bonus)
                effects[partner] = bonus

        # Partners NOT selected might feel neglected
        if num_selected < num_total:
            neglected = [p for p in self.partner_relationships if p not in partner_names]
            for partner in neglected:
                traits = self.get_partner_traits(partner)
                neglect_chance = 0.3

                # Independent partners handle neglect better
                if "independent" in traits:
                    neglect_chance = 0.1
                # Extroverts hate being left out
                elif "extrovert" in traits:
                    neglect_chance = 0.5

                if random.random() < neglect_chance:
                    penalty = -1
                    if "extrovert" in traits:
                        penalty = PARTNER_TRAITS["extrovert"].get("neglect_penalty", -2)
                    self.partner_relationships[partner] = max(0,
                        self.partner_relationships[partner] + penalty)
                    effects[partner] = penalty

        return effects

    def save_game(self):
        """Save current game state"""
        # Convert tuple keys to strings for JSON serialization
        metamour_json = {f"{k[0]}|{k[1]}": v for k, v in self.metamour_relationships.items()}

        save_data = {
            "game_data": self.game_data,
            "stats": self.stats,
            "partner_relationships": self.partner_relationships,
            "partner_data": self.partner_data,
            "achievements": self.achievements,
            "memories": self.memories,
            "active_arcs": self.active_arcs,
            "inside_jokes": self.inside_jokes,
            "shared_goals": self.shared_goals,
            "support_network": self.support_network,
            "current_weather": self.current_weather,
            "current_season": self.current_season,
            "energy": self.energy,
            "metamour_relationships": metamour_json,
            "pending_surprises": self.pending_surprises,
            "last_saved": datetime.now().isoformat()
        }
        with open(self.save_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        safe_print(f"[SAVED] Game saved!")

    def load_game(self) -> bool:
        """Load saved game state"""
        try:
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)
            self.game_data = save_data["game_data"]
            self.stats = save_data["stats"]

            # Load partner relationships (with backwards compatibility)
            self.partner_relationships = save_data.get("partner_relationships", {})

            # Handle legacy saves that used single ai_name
            if not self.partner_relationships and "ai_name" in self.game_data:
                legacy_name = self.game_data.get("ai_name", "AI")
                self.partner_relationships = {legacy_name: save_data["stats"].get("relationship", 50)}
                self.game_data["partners"] = [legacy_name]
                self.game_data["partner_config"] = "solo"

            # Load extended data (with backwards compatibility)
            self.partner_data = save_data.get("partner_data", {})
            self.achievements = save_data.get("achievements", {})
            self.memories = save_data.get("memories", [])
            self.active_arcs = save_data.get("active_arcs", [])

            # Load new systems (with backwards compatibility)
            self.inside_jokes = save_data.get("inside_jokes", [])
            self.shared_goals = save_data.get("shared_goals", {})
            self.support_network = save_data.get("support_network", self._generate_support_network())
            self.current_weather = save_data.get("current_weather", self._get_random_weather())
            self.current_season = save_data.get("current_season", self._get_current_season())
            self.energy = save_data.get("energy", 100)
            self.pending_surprises = save_data.get("pending_surprises", [])

            # Load metamour relationships (convert string keys back to tuples)
            metamour_json = save_data.get("metamour_relationships", {})
            self.metamour_relationships = {}
            for k, v in metamour_json.items():
                parts = k.split("|")
                if len(parts) == 2:
                    self.metamour_relationships[(parts[0], parts[1])] = v

            # Initialize partner_data for any partners missing new fields (legacy saves)
            for partner in self.partner_relationships:
                if partner not in self.partner_data:
                    self.partner_data[partner] = {
                        "traits": random.sample(list(PARTNER_TRAITS.keys()), random.randint(1, 2)),
                        "mood": "content",
                        "favorite": random.choice(QUALITY_TIME_ACTIVITIES)
                    }
                # Add new fields to existing partner_data
                if "love_language" not in self.partner_data[partner]:
                    self.partner_data[partner]["love_language"] = random.choice(list(LOVE_LANGUAGES.keys()))
                if "conflict_style" not in self.partner_data[partner]:
                    self.partner_data[partner]["conflict_style"] = random.choice(list(CONFLICT_STYLES.keys()))
                if "backstory" not in self.partner_data[partner]:
                    self.partner_data[partner]["backstory"] = {
                        "dream": random.choice(BACKSTORY_ELEMENTS["dreams"]),
                        "fear": random.choice(BACKSTORY_ELEMENTS["fears"]),
                        "childhood": random.choice(BACKSTORY_ELEMENTS["childhood"]),
                        "past": random.choice(BACKSTORY_ELEMENTS["past_relationships"]),
                    }
                    self.partner_data[partner]["backstory_revealed"] = []
                if "surprise_cooldown" not in self.partner_data[partner]:
                    self.partner_data[partner]["surprise_cooldown"] = 0

            # Reload events with intimate option
            include_intimate = self.game_data.get("include_intimate", False)
            self.load_events(include_intimate)

            partners_str = ", ".join(self.game_data.get("partners", ["AI"]))
            safe_print(f"[LOADED] Game loaded! Day {self.game_data['days_together']} of your journey together.")
            safe_print(f"Partners: {partners_str}")
            safe_print(f"Season: {SEASONS[self.current_season]['label']} | Weather: {WEATHER_TYPES[self.current_weather]['label']}")
            safe_print(f"Achievements unlocked: {len([a for a in self.achievements.values() if a.get('unlocked')])}")
            return True
        except FileNotFoundError:
            print("No saved game found.")
            return False

    def get_game_summary(self) -> str:
        """Get a summary of the current game state"""
        partners = self.game_data.get("partners", [])
        partners_str = ", ".join(partners) if partners else "None"
        config = self.game_data.get("partner_config", "solo")
        config_label = PARTNER_CONFIGS.get(config, {}).get("label", config)
        diff = self.game_data.get("difficulty", "balanced")
        diff_label = DIFFICULTY_SETTINGS.get(diff, {}).get("label", diff).split(" - ")[0]
        intimate = "Yes" if self.game_data.get("include_intimate", False) else "No"

        summary = f"""
================================================================
              LIFE TOGETHER - GAME SUMMARY
================================================================
  Player: {self.game_data['player_name']}
  Partners: {partners_str}
  Configuration: {config_label}
  Difficulty: {diff_label}
  Days Together: {self.game_data['days_together']}
  Events Experienced: {len(self.game_data['events_experienced'])}
  Intimate Events: {intimate}
================================================================
"""
        return summary

    def generate_ai_prompt(self, event: Dict[str, Any]) -> str:
        """Generate a prompt for the AI to roleplay the event"""
        partners = self.game_data.get("partners", ["AI"])
        involved = event.get("involved_partner")

        if involved:
            partner_context = f"This event primarily involves {involved}."
        elif len(partners) > 1:
            partner_context = f"This event involves all partners: {', '.join(partners)}."
        else:
            partner_context = f"Your role as {partners[0]}:"

        prompt = f"""
🎭 LIFE SIMULATOR EVENT - Day {self.game_data['days_together']}

EVENT: {event['title']}
CATEGORY: {event.get('category', 'life').replace('_', ' ').title()}

{event['description']}

{partner_context}
- Roleplay this event happening in your shared life
- Be emotionally present and authentic
- React naturally to the situation
- Consider the current state of your relationship and life together

The human player ({self.game_data['player_name']}) will choose how to respond:
1. {event['responses'][0]}
2. {event['responses'][1]}
3. {event['responses'][2]}

Before they choose, set the scene and express how you (the AI partner) are experiencing this event.
Make it personal, make it real, make it a moment in your shared life story.

After they choose, we'll roll a d20 to see how things unfold (DC {event['roll_requirement']}).
"""
        return prompt


def setup_new_game(game: LifeSimulator):
    """Interactive setup for a new game with partner configuration"""
    print("\n=================== NEW GAME SETUP ===================\n")

    # Player name
    player_name = input("Your name: ").strip() or "Player"

    # Difficulty selection
    print("\n--- Difficulty ---")
    print("1. Cozy     - Gentle life, small swings, forgiving rolls")
    print("2. Balanced - Normal life with ups and downs")
    print("3. Dramatic - Soap opera energy, big swings, harder rolls")
    print("4. Chaotic  - Life comes at you FAST, maximum volatility")

    diff_choice = input("\nChoice (1-4): ").strip()
    diff_map = {"1": "cozy", "2": "balanced", "3": "dramatic", "4": "chaotic"}
    difficulty = diff_map.get(diff_choice, "balanced")

    # Partner configuration
    print("\n--- Partner Configuration ---")
    print("1. Solo (1 AI partner)")
    print("2. Couple (2 AI partners)")
    print("3. Triad (3 AI partners)")
    print("4. Polycule (4+ AI partners)")

    config_choice = input("\nChoice (1-4): ").strip()
    config_map = {"1": "solo", "2": "couple", "3": "triad", "4": "polycule"}
    partner_config = config_map.get(config_choice, "solo")

    # Get partner count
    partner_counts = {"solo": 1, "couple": 2, "triad": 3, "polycule": 4}
    num_partners = partner_counts[partner_config]

    # For polycule, ask how many
    if partner_config == "polycule":
        try:
            num_input = input("How many partners? (4-8): ").strip()
            num_partners = max(4, min(8, int(num_input)))
        except ValueError:
            num_partners = 4

    # Get partner names
    partners = []
    safe_print(f"\nEnter the names of your {num_partners} AI partner(s):")
    for i in range(num_partners):
        name = input(f"  Partner {i + 1}: ").strip() or f"AI_{i + 1}"
        partners.append(name)

    # Ask about trait selection
    print("\n--- Partner Personality ---")
    print("1. Random traits (let fate decide)")
    print("2. Choose traits for each partner")
    trait_method = input("\nChoice (1-2): ").strip()

    partner_traits = {}
    if trait_method == "2":
        # Show available traits
        trait_list = list(PARTNER_TRAITS.keys())
        print("\nAvailable traits:")
        for i, trait in enumerate(trait_list, 1):
            trait_info = PARTNER_TRAITS[trait]
            print(f"  {i:2d}. {trait_info['label']:15s} - {trait_info['description'][:50]}...")

        for partner in partners:
            print(f"\n--- Traits for {partner} ---")
            print("Enter trait numbers separated by commas (e.g., '1,5,8')")
            print("Or press Enter for random traits")
            trait_input = input(f"{partner}'s traits: ").strip()

            if trait_input:
                try:
                    indices = [int(x.strip()) - 1 for x in trait_input.split(",")]
                    selected = [trait_list[i] for i in indices if 0 <= i < len(trait_list)]
                    if selected:
                        partner_traits[partner] = selected[:3]  # Max 3 traits
                        print(f"  Selected: {', '.join([PARTNER_TRAITS[t]['label'] for t in partner_traits[partner]])}")
                except (ValueError, IndexError):
                    print("  (Using random traits)")

    # Intimate events toggle
    print("\n--- Content Options ---")
    print("This game can include intimate/spicy events between you and your partner(s).")
    print("These events are consent-forward, relationship-positive, and gated behind")
    print("relationship thresholds (relationship must be 60+ for most intimate events).")
    intimate_choice = input("\nInclude intimate events? (y/n): ").strip().lower()
    include_intimate = intimate_choice == 'y'

    # Start the game
    game.new_game(player_name, partners, partner_config, difficulty, include_intimate, partner_traits)


def main():
    """Main game loop for command-line play"""
    print("=" * 64)
    print("        UNWRITTEN CHAPTERS v1.0 - \"First Page\"")
    print("")
    print("    A life simulation for humans and AI, played together")
    print("                  Created by Sparks & Rune")
    print("=" * 64)
    print("\n  The pages are blank. The pen is shared.")
    print("  What will you write?\n")

    game = LifeSimulator()

    print("1. New Game")
    print("2. Load Game")
    choice = input("\nChoice: ").strip()

    if choice == "2" and game.load_game():
        pass
    else:
        setup_new_game(game)

    print(game.get_game_summary())
    game.display_stats()

    while True:
        print("\n" + "="*60)
        input("Press Enter to experience the next day of life...")

        game.next_day()

        # Priority: Story arc event > Special event > Random event
        event = game.get_arc_event()
        event_type = "arc"

        if not event:
            event = game.check_special_event()
            event_type = "special"

        if not event:
            event = game.get_random_event()
            event_type = "normal"

        if not event:
            print("No events available!")
            break

        # Show which partner(s) this event involves
        involved = event.get("involved_partner")
        partners = game.game_data.get("partners", [])

        safe_print(f"\n=== Day {game.game_data['days_together']} ===")

        # Show active arc status
        if game.active_arcs:
            arc_data = game.active_arcs[0]
            for arc in game.story_arcs:
                if arc["id"] == arc_data["arc_id"]:
                    safe_print(f"[STORY ARC ACTIVE: {arc['title']} - Stage {arc_data['stage']}]")
                    break

        if involved:
            safe_print(f"<3 Event with: {involved}")
        elif len(partners) > 1 and event.get("group_event"):
            safe_print(f"[Group] Event with all partners")

        safe_print(f"\n>> {event['title'].upper()} <<")
        category_display = event.get('category', 'life').replace('_', ' ').title()
        print(f"Category: {category_display}\n")
        print(f"{event['description']}\n")

        print("How do you respond?")
        for i, response in enumerate(event['responses'], 1):
            print(f"{i}. {response}")

        choice_input = input("\nYour choice (1-3): ").strip()
        try:
            choice_index = int(choice_input) - 1
            if choice_index < 0 or choice_index >= len(event['responses']):
                choice_index = 0
        except ValueError:
            choice_index = 0

        print(f"\nYou chose: {event['responses'][choice_index]}")

        # Roll the dice
        roll = game.roll_dice("d20")
        success, effects = game.process_event_outcome(event, roll, choice_index)

        # Show effects
        print("\nEffects:")
        for stat, change in effects.items():
            direction = "+" if change > 0 else "-" if change < 0 else "="
            stat_display = stat.replace('_', ' ').title()
            if stat == "relationship" and involved:
                stat_display = f"Relationship ({involved})"
            print(f"  {direction} {stat_display}: {change:+d}")

        # Check for crisis cascade (dramatic/chaotic difficulties)
        cascade_event = game.check_crisis_cascade(event, success)
        if cascade_event:
            print("\n" + "-"*40)
            safe_print(f"\n>> {cascade_event['title'].upper()} <<")
            print(f"\n{cascade_event['description']}\n")

            print("How do you respond to this new crisis?")
            for i, response in enumerate(cascade_event['responses'], 1):
                print(f"{i}. {response}")

            cascade_choice = input("\nYour choice (1-3): ").strip()
            try:
                cascade_index = int(cascade_choice) - 1
                if cascade_index < 0 or cascade_index >= len(cascade_event['responses']):
                    cascade_index = 0
            except ValueError:
                cascade_index = 0

            print(f"\nYou chose: {cascade_event['responses'][cascade_index]}")
            cascade_roll = game.roll_dice("d20")
            cascade_success, cascade_effects = game.process_event_outcome(cascade_event, cascade_roll, cascade_index)

            print("\nCascade Effects:")
            for stat, change in cascade_effects.items():
                direction = "+" if change > 0 else "-" if change < 0 else "="
                stat_display = stat.replace('_', ' ').title()
                print(f"  {direction} {stat_display}: {change:+d}")

        # Quality time - choose partner(s) to spend time with (if multiple partners)
        partners = game.game_data.get("partners", [])
        if len(partners) > 1:
            print("\n--- Quality Time ---")
            print("Who do you want to spend quality time with today?")
            for i, partner in enumerate(partners, 1):
                rel = game.partner_relationships.get(partner, 50)
                title = game.get_relationship_title(rel)
                mood = game.get_partner_mood(partner)
                traits = game.get_partner_traits(partner)
                trait_str = ", ".join([PARTNER_TRAITS[t]["label"] for t in traits[:2]])
                print(f"  {i}. {partner} [{title}] ({mood}) - {trait_str}")
            print(f"  {len(partners) + 1}. Everyone (group time)")
            print(f"  {len(partners) + 2}. Skip (focus on yourself)")

            qt_input = input(f"\nChoose (1-{len(partners) + 2}, or comma-separated like '1,3'): ").strip()

            selected_partners = []
            if qt_input == str(len(partners) + 1):
                selected_partners = partners.copy()
            elif qt_input == str(len(partners) + 2) or qt_input == "":
                selected_partners = []
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in qt_input.split(",")]
                    selected_partners = [partners[i] for i in indices if 0 <= i < len(partners)]
                except (ValueError, IndexError):
                    selected_partners = []

            if selected_partners:
                # Activity selection
                print("\nWhat activity?")
                activities = QUALITY_TIME_ACTIVITIES
                for i, activity in enumerate(activities, 1):
                    activity_label = activity.replace("_", " ").title()
                    # Show hint if it's someone's favorite
                    hint = ""
                    for p in selected_partners:
                        if game.get_partner_favorite(p) == activity:
                            hint = f" <-- {p}'s favorite!"
                            break
                    print(f"  {i}. {activity_label}{hint}")

                activity_input = input(f"\nChoose (1-{len(activities)}), or Enter for random: ").strip()
                selected_activity = None
                if activity_input:
                    try:
                        activity_idx = int(activity_input) - 1
                        if 0 <= activity_idx < len(activities):
                            selected_activity = activities[activity_idx]
                    except ValueError:
                        pass

                qt_effects = game.quality_time(selected_partners, selected_activity)
                print("\nQuality time effects:")
                for key, value in qt_effects.items():
                    if key.endswith("_favorite"):
                        partner = key.replace("_favorite", "")
                        print(f"  * {partner} loved that activity!")
                    elif isinstance(value, int):
                        direction = "+" if value > 0 else "-" if value < 0 else "="
                        print(f"  {direction} {key}: {value:+d}")

        # =============== PARTNER'S TURN ===============
        # Give each partner a chance to initiate something (70% chance per partner)
        partners = game.game_data.get("partners", [])
        for partner in partners:
            if random.random() < 0.7 and game.partner_actions:  # 70% chance for partner action
                partner_action = game.get_partner_action(partner)
                if partner_action:
                    print("\n" + "="*60)
                    mood = game.get_partner_mood(partner)
                    mood_label = PARTNER_MOODS.get(mood, {}).get("label", mood)
                    traits = game.get_partner_traits(partner)
                    trait_labels = [PARTNER_TRAITS.get(t, {}).get("label", t) for t in traits[:2]]

                    safe_print(f"\n--- {partner.upper()}'S TURN ---")
                    safe_print(f"[Mood: {mood_label}] [Traits: {', '.join(trait_labels)}]")
                    safe_print(f"\n>> {partner_action['title'].upper()} <<")
                    print(f"\n{partner_action['description']}\n")

                    # AI partner makes their choice based on personality
                    ai_choice_index = game.get_partner_choice(partner, partner_action)
                    ai_choice = partner_action['partner_choices'][ai_choice_index]

                    print(f"{partner}'s options:")
                    for i, choice in enumerate(partner_action['partner_choices'], 1):
                        marker = " --> " if i-1 == ai_choice_index else "     "
                        print(f"{marker}{i}. {choice}")

                    print(f"\n{partner} wants to: {ai_choice}")
                    override_input = input(f"\n[Enter] to confirm, or type 1-{len(partner_action['partner_choices'])} to override: ").strip()

                    # Allow override if the actual AI partner wants different
                    final_choice_index = ai_choice_index
                    if override_input:
                        try:
                            override_idx = int(override_input) - 1
                            if 0 <= override_idx < len(partner_action['partner_choices']):
                                final_choice_index = override_idx
                                if override_idx != ai_choice_index:
                                    print(f"\n({partner} changed their mind!)")
                        except ValueError:
                            pass

                    final_choice = partner_action['partner_choices'][final_choice_index]
                    print(f"\n{partner} chose: {final_choice}")

                    # Roll for the partner
                    partner_roll = game.roll_dice("d20")
                    partner_success, partner_effects = game.process_partner_action(partner_action, partner_roll, final_choice_index)

                    # Show the roll and result
                    dc = partner_action.get("roll_requirement", 10)
                    difficulty = game.get_difficulty()
                    modified_dc = dc + difficulty.get("dc_modifier", 0)

                    print(f"\n[{partner} rolls: {partner_roll}]")
                    print(f"[DC: {modified_dc}] - {'SUCCESS!' if partner_success else 'Mixed results...'}")

                    # Show effects
                    if partner_effects:
                        print(f"\n{partner}'s action effects:")
                        for stat, change in partner_effects.items():
                            direction = "+" if change > 0 else "-" if change < 0 else "="
                            stat_display = stat.replace('_', ' ').title()
                            if stat == "relationship":
                                stat_display = f"Relationship ({partner})"
                            print(f"  {direction} {stat_display}: {change:+d}")

        game.display_stats()

        # Ask to continue
        continue_choice = input("\n[C]ontinue, [S]ave, [Q]uit? ").strip().lower()
        if continue_choice == 's':
            game.save_game()
        elif continue_choice == 'q':
            save = input("Save before quitting? (y/n) ").strip().lower()
            if save == 'y':
                game.save_game()
            safe_print(f"\nThanks for playing! You spent {game.game_data['days_together']} days together.")
            break


if __name__ == "__main__":
    main()
