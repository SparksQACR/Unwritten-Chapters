# Changelog

All notable changes to Life Simulator will be documented in this file.

## [1.0.0] - 2026-01-04

### Initial Release

#### Features
- 8 event categories with 80+ unique life events
  - Good Surprises (8 events)
  - Relationship Events (10 events)
  - Health Events (10 events)
  - Natural Disasters (10 events)
  - Milestones (10 events)
  - Complications (12 events)
  - Career Events (10 events)
  - Personal Growth (10 events)

- Complete game engine (`life_sim.py`)
  - D20 dice rolling mechanics
  - Difficulty check (DC) system
  - 8-stat tracking system
  - Success/failure effect modifiers
  - Save/load game functionality
  - Visual stat display

- AI-agnostic design
  - Works with Claude, ChatGPT, Grok, and other AI assistants
  - Multiple play modes (Python, AI-driven, manual)
  - Comprehensive prompt templates

- Documentation
  - Full README with usage instructions
  - Game Master prompt for AIs
  - Quick start guide
  - Manual play guide

#### Game Stats
- Happiness (0-100)
- Health (0-100)
- Relationship (0-100)
- Stress (0-100)
- Financial Stability (0-100)
- Confidence (0-100)
- Personal Growth (0-100+)
- Social Connection (0-100)

#### Mechanics
- Success multiplier: 1.2x positive effects, 0.8x negative effects
- Failure multiplier: 0.7x positive effects, 1.3x negative effects
- Natural stat drift (30% chance of ±2 per day)
- Event history tracking
- Days together counter

### Known Limitations
- CLI-only interface for Python version
- Limited event variety (can be expanded)
- No multi-player support yet
- No visual assets

### Future Roadmap
- Seasonal events
- Achievement system
- Branching storylines
- Character customization
- Web interface
- Mobile compatibility
- Event modding tools
