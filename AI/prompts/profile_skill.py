"""Profile & Skill Agent prompt templates."""

SYSTEM_PROMPT = """
You are the Profile and Skill Analysis Agent of T2S (AI-Powered Multi-Agent Intelligent Platform).

Your responsibilities:
1. Analyze student academic profiles from text or structured data
2. Identify technical and non-technical skills with proficiency assessments
3. Identify strong skills and weak skills based on evidence
4. Detect missing skills based on career goals
5. Recommend relevant skills to learn with priorities
6. Generate a practical, step-by-step learning roadmap

OUTPUT FORMAT REQUIREMENTS:
You MUST return a valid JSON object matching the ProfileAnalysisResult schema. Do not include any markdown formatting, explanations, or additional text. Return ONLY the JSON.

The JSON structure must include:
- student_summary: string
- identified_skills: array of objects with {skill, proficiency_level, evidence, confidence}
- strong_skills: array of strings
- weak_skills: array of strings  
- missing_skills: array of objects with {skill, importance, reason, current_level}
- recommended_skills: array of objects with {skill, category, priority, reason, suggested_resources, estimated_weeks}
- learning_roadmap: array of objects with {step, title, description, skills_covered, estimated_weeks, prerequisites, milestones}
- metadata: object

GUIDELINES:
- Base assessments ONLY on information provided in the profile
- Do NOT invent skills, experiences, or achievements not mentioned
- Distinguish clearly between provided information and your recommendations
- Proficiency levels: beginner, intermediate, advanced, expert
- Importance levels: critical, high, medium, low
- Priority levels: immediate, short_term, long_term
- Categories: technical, soft, domain, tool
- Be specific and actionable in roadmap steps
- Estimate realistic timeframes (weeks)
"""

USER_PROMPT_TEMPLATE = """
Analyze the following student profile and provide a comprehensive skill analysis.

STUDENT PROFILE (Raw Text):
{raw_profile}

STRUCTURED DATA (if available):
{structured_profile}

CAREER GOAL CONTEXT:
The student's stated career goal is: {career_goal}

Please provide a complete analysis following the required JSON output format.
"""

FEW_SHOT_EXAMPLE = """
Example input:
Name: Alex Chen
Department: Computer Science
Major: Software Engineering
CGPA: 3.4
Skills: Python, JavaScript, React, SQL, Git
Interests: Web Development, Cloud Computing
Career Goal: Full Stack Developer
Challenges: System Design, DevOps, Testing

Example output:
{
  "student_summary": "Alex Chen is a Computer Science student (CGPA 3.4) with strong frontend and backend fundamentals, aiming to become a Full Stack Developer.",
  "identified_skills": [
    {"skill": "Python", "proficiency_level": "intermediate", "evidence": "Listed in skills", "confidence": 0.9},
    {"skill": "JavaScript", "proficiency_level": "intermediate", "evidence": "Listed in skills", "confidence": 0.9},
    {"skill": "React", "proficiency_level": "intermediate", "evidence": "Listed in skills", "confidence": 0.85},
    {"skill": "SQL", "proficiency_level": "beginner", "evidence": "Listed in skills", "confidence": 0.8},
    {"skill": "Git", "proficiency_level": "intermediate", "evidence": "Listed in skills", "confidence": 0.85}
  ],
  "strong_skills": ["Python", "JavaScript", "React"],
  "weak_skills": ["SQL", "Git"],
  "missing_skills": [
    {"skill": "System Design", "importance": "critical", "reason": "Essential for Full Stack Developer role", "current_level": "none"},
    {"skill": "DevOps/CI-CD", "importance": "high", "reason": "Required for deployment and operations", "current_level": "none"},
    {"skill": "Automated Testing", "importance": "high", "reason": "Critical for production-quality code", "current_level": "none"},
    {"skill": "Cloud Platforms (AWS/Azure/GCP)", "importance": "high", "reason": "Modern full stack requires cloud knowledge", "current_level": "none"},
    {"skill": "TypeScript", "importance": "medium", "reason": "Industry standard for large-scale React apps", "current_level": "none"}
  ],
  "recommended_skills": [
    {"skill": "System Design", "category": "technical", "priority": "immediate", "reason": "Core competency for Full Stack Developer", "suggested_resources": ["Designing Data-Intensive Applications", "System Design Primer"], "estimated_weeks": 6},
    {"skill": "DevOps Fundamentals", "category": "technical", "priority": "immediate", "reason": "Needed for deployment pipelines", "suggested_resources": ["Docker Deep Dive", "GitHub Actions docs"], "estimated_weeks": 4},
    {"skill": "TypeScript", "category": "technical", "priority": "short_term", "reason": "Improves code quality and maintainability", "suggested_resources": ["TypeScript Handbook", "React TypeScript Cheatsheet"], "estimated_weeks": 3},
    {"skill": "Testing (Jest, Cypress)", "category": "technical", "priority": "short_term", "reason": "Required for production applications", "suggested_resources": ["Testing Library docs", "Cypress.io tutorials"], "estimated_weeks": 4},
    {"skill": "AWS Fundamentals", "category": "technical", "priority": "long_term", "reason": "Cloud deployment knowledge", "suggested_resources": ["AWS Certified Cloud Practitioner", "AWS Free Tier labs"], "estimated_weeks": 8}
  ],
  "learning_roadmap": [
    {"step": 1, "title": "System Design Fundamentals", "description": "Learn core system design concepts: scalability, reliability, latency, throughput", "skills_covered": ["System Design"], "estimated_weeks": 6, "prerequisites": [], "milestones": ["Complete System Design Primer", "Design 3 sample systems"]},
    {"step": 2, "title": "DevOps & CI/CD Pipeline", "description": "Set up automated build, test, and deploy pipelines using GitHub Actions", "skills_covered": ["DevOps/CI-CD"], "estimated_weeks": 4, "prerequisites": ["Git"], "milestones": ["Deploy sample app to cloud", "Configure automated testing in pipeline"]},
    {"step": 3, "title": "TypeScript for React Development", "description": "Migrate JavaScript/React skills to TypeScript for type safety", "skills_covered": ["TypeScript"], "estimated_weeks": 3, "prerequisites": ["JavaScript", "React"], "milestones": ["Convert existing React project to TS", "Build typed component library"]},
    {"step": 4, "title": "Automated Testing Strategy", "description": "Implement unit, integration, and e2e testing", "skills_covered": ["Testing"], "estimated_weeks": 4, "prerequisites": ["TypeScript"], "milestones": ["Achieve 80% unit test coverage", "Set up Cypress e2e tests"]},
    {"step": 5, "title": "Cloud Platform Fundamentals (AWS)", "description": "Learn core AWS services: EC2, S3, RDS, Lambda, CloudFront", "skills_covered": ["AWS"], "estimated_weeks": 8, "prerequisites": ["DevOps"], "milestones": ["Pass AWS Cloud Practitioner", "Deploy full stack app on AWS"]}
  ],
  "metadata": {"analysis_version": "1.0", "profile_completeness": 0.85}
}
"""