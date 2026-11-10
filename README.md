# T2S: AI-Powered Multi-Agent Intelligent Platform

An AI-powered multi-agent intelligent platform for student skill development, mentorship, collaboration, and career discovery.

## Overview

T2S connects students, teachers, and alumni through a unified ecosystem for skill development, mentorship, collaboration, research, hackathons, knowledge sharing, and career discovery. The system uses a multi-agent AI architecture in which specialized AI agents perform different tasks while an AI orchestrator coordinates their interactions.

**Authors:** Nur Mohammod (232-35-089), Sami Ansari (232-35-176), Mahmudul Hassan Shoyaive (232-35-056)

## Problem

University students struggle to find mentors, develop practical skills, discover research opportunities, form project teams, participate in hackathons, and identify matching career opportunities — activities that are traditionally scattered across separate platforms and channels.

## Core Concept

`Student Activities → Skill Analysis → AI Recommendations → Tasks/Teams/Research/Jobs → New Activities → Updated Skill Profile`

This creates a continuously evolving student development ecosystem.

## Key Features

- **Teacher-Led Technical Rooms** — teachers create rooms (AI, ML, Data Science, Web Dev, Cybersecurity, etc.); students request to join.
- **Task & Problem Management** — teachers assign tasks with difficulty, required skills, deadlines, resources, and max marks; students submit solutions for evaluation.
- **Dynamic Student Skill Profiles** — tracks technical skills, activities, and achievements that evolve as students complete tasks.
- **Progress Tracking** — interactive performance visualization with teacher feedback (mentoring indicator, not official ranking).
- **Multi-Agent AI System** — an AI Orchestrator routes requests to specialized agents:
  - Profile & Skill Agent — skill analysis, gap detection, recommendations
  - Task Agent — task recommendation and difficulty suggestion
  - Team Matching Agent — complementary-skill teammate matching
  - Career Agent — job/internship matching and skill-gap identification
  - Research Agent — research topics, papers, collaborators discovery
  - Knowledge Agent — RAG-based answers over authorized resources
- **AI Assistant** — context-aware answers to platform questions using authorized tools.
- **Hackathon & Project Team Formation** — students post hackathon opportunities and find teammates.
- **Research Hub** — discover research opportunities, papers, and collaborators.
- **Knowledge Hub** — centralized learning resources with semantic search and RAG.
- **Job & Internship Module** — collects opportunities from public APIs, RSS feeds, and approved integrations.
- **Alumni Career Network** — alumni share jobs, internships, projects, industry advice, and connect with students.
- **Personalized Recommendations** — tasks, resources, teams, research, and career opportunities.

## Architecture

```
Users (Student/Teacher/Alumni/Admin)
        │
   Next.js Frontend
        │
   FastAPI Backend (Core Services)
        │
   AI Orchestrator
   ├── Profile Agent
   ├── Task Agent
   ├── Team Agent
   ├── Career Agent
   ├── Research Agent
   └── Knowledge Agent
        │
PostgreSQL + pgvector (Vector Search)
```

## Technology Stack

| Layer      | Technologies                                          |
|------------|-------------------------------------------------------|
| Frontend   | Next.js, React, TypeScript, Tailwind CSS              |
| Backend    | Python, FastAPI, Pydantic                             |
| Database   | PostgreSQL, pgvector                                  |
| AI         | LLM API / open-source LLM, Embeddings, RAG, Multi-agent orchestration |
| ML         | Scikit-learn, NumPy, Pandas                           |
| Auth       | JWT or secure session-based authentication           |
| DevOps     | Git, GitHub, Docker                                  |
| Testing    | Postman, Pytest, frontend testing tools               |

## Database Entities

User, StudentProfile, TeacherProfile, AlumniProfile, Skill, Interest, Room, RoomMembership, Task, Submission, Evaluation, Progress, Project, Team, TeamMember, Hackathon, Job, Internship, ResearchOpportunity, Resource, Notification, AIInteraction, Recommendation

## AI Safety & Ethics

- Protect user privacy and avoid exposing private student information.
- Distinguish AI recommendations from human decisions; never present recommendations as guaranteed outcomes.
- Teachers review important academic/career decisions (human-in-the-loop).
- Respect copyright and external website terms; store metadata/links and openly licensed resources rather than unauthorized copies.
- Use authorized tools and permitted data sources only.

## Project Timeline

16-week development plan covering requirement analysis, UI/UX design, database design, authentication, backend/frontend development, task & progress system, collaboration & team system, AI foundation, multi-agent AI, knowledge & research hub, career module, full integration, testing & optimization, and documentation.

## Target Users

- **Students** — create profiles, join rooms, complete tasks, track progress, find teammates, discover research/jobs, use the AI assistant.
- **Teachers** — create rooms, assign tasks, review submissions, give feedback, monitor progress, identify collaborators.
- **Alumni** — share jobs/internships, post projects, share industry knowledge, connect with students, recommend skills.

## Out of Scope (v1)

- Replacing university academic grading or professional recruitment systems.
- Guaranteeing employment or making final hiring/academic decisions.
- Bypassing restricted job websites or hosting unauthorized copyrighted books.
- Unrestricted autonomous AI actions.