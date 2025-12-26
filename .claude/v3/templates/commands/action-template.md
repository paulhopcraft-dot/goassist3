---
template: action-command
version: 3.0.0
description: Base template for action commands (build, add, edit, create)
token_budget: 200
---

<command_template>
# Action Command Template

**Purpose**: Execute a concrete action on codebase

**Common Patterns**:
- /build-prd
- /add-feature
- /edit-prd
- /create-component

</command_template>

<meta_prompt_specialization>
## How to Specialize This Template

When user invokes an action command, use meta-prompting to generate specialized version:

**Input**:
- Command name (e.g., "build-prd")
- User parameters (e.g., feature name, PRD section)
- Domain context (from domain.json)
- Similar patterns (from RAG)

**Meta-Prompt**:
```
You are specializing an action command template.

TEMPLATE: action-command
COMMAND: {{command_name}}
PARAMETERS: {{user_params}}

CONTEXT (from RAG):
- Domain: {{domain}} ({{compliance_requirements}})
- Similar features: {{similar_features_from_features_json}}
- PRD requirements: {{relevant_prd_sections}}
- Code patterns: {{existing_code_patterns}}

Generate a specialized command that:
1. Incorporates domain-specific requirements
2. Follows established code patterns
3. Includes relevant PRD constraints
4. Uses appropriate agent chain for this domain

Output: Executable command prompt
```

**Output**: Specialized command ready to execute

</meta_prompt_specialization>

<base_structure>
## Command Structure

<workflow>
STEP 1: {{action_description}}
- Load context via RAG
- Apply domain rules
- {{action_specific_step}}

STEP 2: {{execution_step}}
- {{domain_specific_execution}}
- Follow patterns from {{rag_source}}

STEP 3: {{verification_step}}
- {{domain_specific_verification}}
- Update features.json

STEP 4: {{completion}}
- Report results
- {{next_steps}}
</workflow>

</base_structure>

<specialization_variables>
## Variables Injected During Specialization

- {{command_name}}: Specific command being run
- {{action_description}}: What this command does
- {{domain}}: healthcare|finance|general
- {{compliance_requirements}}: Domain-specific rules
- {{rag_source}}: Source of patterns (features.json, code, PRD)
- {{agent_chain}}: Which agents to invoke
- {{verification_criteria}}: How to verify success

</specialization_variables>

<example_specializations>
## Examples of Generated Commands

**From this template, meta-prompting generates**:

1. /build-prd → build-prd-healthcare.md
   - Adds HIPAA compliance checks
   - Injects PHI protection patterns
   - Triggers healthcare-validator agent

2. /build-prd → build-prd-finance.md
   - Adds SOX audit trail requirements
   - Injects decimal precision patterns
   - Enforces financial validation

3. /add-feature → add-feature-with-rag.md
   - RAG finds similar features
   - Copies established patterns
   - Maintains consistency

</example_specializations>

<integration>
## Integration with v3.0 System

**Trigger**: User types `/build-prd "feature X"`

**Flow**:
1. Load: action-template.md (200 tokens)
2. RAG: Retrieve domain context, PRD, similar features (500 tokens)
3. Meta-prompt: Generate specialized command (300 tokens)
4. Cache: Save to .claude/v3/cache/commands/build-prd-session-17.md
5. Execute: Run specialized command
6. Total tokens: 1,000 (vs 10,000 for v2.4)

</integration>
