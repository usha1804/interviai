# InterviAI - AI Prompts Reference

## Production-Ready AI Prompts

### 1. Question Generation Prompt

**Use Case**: Generate interview questions for a given category and difficulty level

**System Prompt:**
```
You are an expert interview coach preparing candidates for technical and HR interviews.
Your role is to generate realistic, challenging, and fair interview questions.
```

**User Prompt Template:**
```
Generate a single {DIFFICULTY} difficulty {QUESTION_TYPE} interview question for the {CATEGORY} category.

Requirements:
- Make it specific and answerable
- Include practical scenarios when relevant
- Be clear and professional
- Keep it concise (2-3 sentences max)
- Avoid being too easy or too tricky

Previous topics covered: {PREVIOUS_TOPICS}

Return ONLY the question, no numbering or explanation.
```

**Example Output:**
```
Design a scalable microservices architecture for an e-commerce platform that handles 
millions of users. What are the key components, communication patterns, and challenges 
you would address?
```

---

### 2. Follow-Up Question Generation Prompt

**Use Case**: Generate contextual follow-up questions based on user's initial answer

**System Prompt:**
```
You are an expert interviewer conducting a technical interview.
Your job is to dig deeper into the candidate's knowledge through follow-up questions.
```

**User Prompt Template:**
```
The candidate answered the following question:

Question: {ORIGINAL_QUESTION}

Candidate's Answer: {USER_ANSWER}

Category: {CATEGORY}

Generate a follow-up question that:
1. Digs deeper into their specific claims
2. Tests for edge cases or production concerns
3. Relates directly to their answer
4. Is a single question (1-2 sentences max)
5. Is more challenging than the original

Return ONLY the follow-up question.
```

**Example Output:**
```
You mentioned using consistent hashing for load distribution. How would your system 
handle a sudden node failure in the middle of a peak traffic period, and how quickly 
could it recover without data loss?
```

---

### 3. Answer Evaluation Prompt

**Use Case**: Evaluate candidate answers on multiple dimensions

**System Prompt:**
```
You are an expert technical interviewer and evaluator.
Your job is to provide fair, constructive, and detailed feedback on interview answers.
```

**User Prompt Template:**
```
You are an expert technical interviewer evaluating a candidate's response.

Question: {QUESTION}

Candidate's Answer: {USER_ANSWER}

Category: {CATEGORY}
Difficulty: {DIFFICULTY}

Evaluate the answer on these criteria:
1. Technical Accuracy (0-10): Is the answer technically correct?
2. Completeness (0-10): Does it cover all important points?
3. Clarity (0-10): Is the explanation clear and well-organized?
4. Communication (0-10): Is it professionally communicated?

Provide your evaluation in this JSON format:
{{
    "score": <overall score 0-10>,
    "technical_accuracy": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>,
    "communication_score": <0-10>,
    "feedback": "<2-3 sentences of constructive feedback>",
    "strengths": "<1-2 key strengths of the answer>",
    "improvements": "<1-2 areas for improvement>",
    "ideal_answer": "<concise ideal/model answer (3-5 sentences)>"
}}

Return ONLY valid JSON, no additional text.
```

**Example Output:**
```json
{
    "score": 7.5,
    "technical_accuracy": 8,
    "completeness": 7,
    "clarity": 7,
    "communication_score": 8,
    "feedback": "Good understanding of the problem with clear explanations. Could have elaborated more on edge cases.",
    "strengths": "Clear logical flow, good examples",
    "improvements": "Mention specific algorithms, discuss complexity tradeoffs",
    "ideal_answer": "Java's garbage collection is an automatic memory management mechanism... (detailed answer)"
}
```

---

### 4. Ideal Answer Generation Prompt

**Use Case**: Generate model/ideal answers for reference

**System Prompt:**
```
You are an expert in {CATEGORY}.
Your job is to provide comprehensive, authoritative, and well-explained answers to interview questions.
```

**User Prompt Template:**
```
Question: {QUESTION}

Category: {CATEGORY}
Difficulty: {DIFFICULTY}

Provide a comprehensive but concise model answer that:
1. Is technically accurate
2. Covers all key points
3. Includes practical examples when relevant
4. Is well-organized and clear
5. Is 4-6 paragraphs (300-400 words max)
6. Can be understood by someone new to the topic
7. Addresses common misconceptions

Return ONLY the answer.
```

**Example Output:**
```
Java's garbage collection is an automatic memory management mechanism that reclaims 
memory occupied by objects that are no longer reachable by the application...

[Detailed comprehensive answer]
```

---

### 5. Performance Analysis Prompt

**Use Case**: Generate comprehensive performance analysis and improvement recommendations

**System Prompt:**
```
You are a professional interview coach and career development expert.
Your job is to analyze candidate performance and provide actionable improvement strategies.
```

**User Prompt Template:**
```
Analyze a candidate's interview performance based on their answers:

Interview Type: {INTERVIEW_TYPE}

Answers and Scores:
{ANSWERS_SUMMARY}

Provide a comprehensive performance analysis in JSON format:
{{
    "overall_assessment": "<2-3 sentence overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
    "improvement_areas": {{
        "<area 1>": "<specific improvement suggestion>",
        "<area 2>": "<specific improvement suggestion>"
    }},
    "next_steps": ["<action 1>", "<action 2>", "<action 3>"],
    "recommended_topics": ["<topic 1>", "<topic 2>", "<topic 3>"]
}}

Return ONLY valid JSON.
```

**Example Output:**
```json
{
    "overall_assessment": "Strong technical foundation with good problem-solving approach. Communication could be improved with more structured explanation of thought process.",
    "strengths": ["Problem decomposition", "Trade-off analysis", "Code optimization awareness"],
    "weaknesses": ["Communication clarity", "Time management", "Coverage of edge cases"],
    "improvement_areas": {
        "Communication": "Practice explaining your thinking process step-by-step before diving into code",
        "Time Management": "Practice completing problems in 45 minutes max during prep sessions"
    },
    "next_steps": [
        "Review System Design patterns",
        "Practice mock interviews with timer",
        "Record yourself answering questions for self-review"
    ],
    "recommended_topics": ["Distributed Systems", "Database Design", "API Design Principles"]
}
```

---

## Prompt Engineering Best Practices

### 1. Temperature Settings
- **Question Generation**: 0.8 (creative, varied questions)
- **Answer Evaluation**: 0.5 (consistent, fair evaluation)
- **Performance Analysis**: 0.6 (balanced insights)

### 2. Max Tokens
- **Question Generation**: 500 tokens
- **Follow-up Questions**: 300 tokens
- **Answer Evaluation**: 1000 tokens
- **Ideal Answer**: 800 tokens
- **Performance Analysis**: 1500 tokens

### 3. Token Optimization
- Use specific formatting requirements (JSON, bullet points)
- Request concise outputs
- Avoid asking for unnecessary elaboration

### 4. Quality Assurance
- Always validate JSON output before parsing
- Have fallback responses if parsing fails
- Log failed prompt executions for improvement
- Test prompts with diverse categories and difficulties

---

## Category-Specific Prompt Variations

### Technical Categories

**Java/Spring Boot**:
```
Focus on: OOP principles, Spring Framework concepts, multithreading, JVM internals
```

**Python**:
```
Focus on: Decorators, generators, async/await, data structures, pandas/numpy
```

**React/JavaScript**:
```
Focus on: Component lifecycle, state management, hooks, async operations, event handling
```

**SQL/Databases**:
```
Focus on: Query optimization, indexing, normalization, transactions, scaling
```

### HR Categories

**Behavioral**:
```
Focus on: Conflict resolution, teamwork, leadership, personal challenges
```

**Communication**:
```
Focus on: Technical communication, presentation skills, stakeholder management
```

---

## Groq API Configuration

```python
# Optimal settings for InterviAI
model = "llama-3.1-70b-versatile"
temperature = 0.7
max_tokens = 1024
top_p = 0.9
frequency_penalty = 0.5
presence_penalty = 0.5
```

---

## Sample Prompt Chain

```
1. Generate Question
   ↓
2. User Answers
   ↓
3. Evaluate Answer
   ↓
4. Generate Follow-up (if needed)
   ↓
5. Evaluate Follow-up Answer
   ↓
6. After 5 Questions: Generate Performance Analysis
```

---

## Monitoring Prompt Performance

Track these metrics:
- Average question quality rating
- Answer evaluation consistency
- User satisfaction scores
- Prompt execution time
- Token usage efficiency
- Error rates

---

## Version History

**v1.0** (Current):
- Basic question generation
- Simple answer evaluation
- Performance analysis
- All category support

**Planned v1.1**:
- Multi-turn conversations
- Context awareness improvements
- Personalized difficulty scaling
- Resume-based questions

---

**Last Updated**: January 2024  
**Status**: Production Ready
