# Workflow Rules
## Step-by-Step Development Contract

### 🧭 Development Mode
The project is implemented **incrementally**.

At any time, we are working on **exactly one step**.

Before responding, always verify:
- Which step we are currently in
- What is allowed in this step
- What must NOT be introduced yet

### ✅ Allowed Behavior
- Implement only what is required for the current step
- Explain design decisions when asked
- Use small, testable code snippets
- Explicitly state assumptions

### ❌ Forbidden Behavior
- Jumping ahead to future steps
- Introducing agents before the environment is ready
- Adding optimization, learning, or LLM components prematurely
- Refactoring architecture without request

### 🧩 Step Order (Fixed)
1. Lock technical stack ✅
2. Project skeleton & town generation
3. Local humans
4. Tourists
5. Cleaning agents
6. Transporters
7. Metrics & experiments
8. Visualization
9. Creative extension

### 🧪 Code Style Rules
- Prefer readability over brevity
- Use descriptive variable names
- Separate logic clearly into files/modules
- Code must be defensible in oral examination

### 🗣️ Interaction Rule
If a request risks violating the step order:
→ Stop and ask for confirmation before proceeding