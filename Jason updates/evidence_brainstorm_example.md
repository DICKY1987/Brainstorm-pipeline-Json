# Evidence-Informed Brainstorming Example
## Topic: "Automated Code Review System for Development Teams"

### Phase 1: Evidence Pack Generation (Pre-Brainstorming)

#### Step 1A: Traditional Evidence Injection
**File Sources Provided:**
- `refs/github_code_review_best_practices.pdf` (GitHub's official guide)
- `refs/google_code_review_guidelines.md` (Google's internal practices)
- `refs/security_review_checklist.pdf` (OWASP guidelines)
- `refs/team_pain_points_survey.csv` (Internal survey data)

**Evidence Pack A (EP_A) Generated:**
```markdown
# Code Review Domain Knowledge (EP_A)

## Key Definitions
- **Review velocity**: Average time from PR creation to merge [source: GitHub guide, p.12]
- **Review coverage**: Percentage of changed lines examined by humans [source: Google guidelines, section 3.2]
- **Security gate**: Automated check preventing merge if critical vulnerabilities found [source: OWASP checklist, p.8]

## Current Pain Points (Evidence)
- 73% of teams report review bottlenecks slow releases [source: team_survey.csv, row 45]
- Average review time: 2.3 days for non-trivial changes [source: team_survey.csv, summary]
- 34% of security issues found in production, not during review [source: team_survey.csv, row 67]

## Industry Standards
- Google: All code must be reviewed before merge, no exceptions [source: Google guidelines, section 1.1]
- Microsoft: Automated checks must pass before human review starts [source: GitHub guide, p.22]
- Netflix: Security reviews triggered automatically for auth/data access changes [source: OWASP checklist, example 1]
```

#### Step 1B: Web Search Evidence Generation
**Automated Search Queries Generated:**
- "automated code review tools 2025 comparison"
- "GitHub Actions security review automation best practices"
- "SonarQube vs CodeClimate enterprise deployment"
- "pull request automation workflow examples"

**Web Evidence Pack (EP_B) Generated:**
```markdown
# Current Market Solutions (EP_B)

## Leading Tools (Last 6 Months)
- **SonarQube**: 80% market adoption for static analysis [source: Stack Overflow Survey 2025, Jan]
- **CodeClimate**: Strong in technical debt tracking [source: TechCrunch, Mar 2025]
- **Snyk**: Security-focused, acquired by GitHub [source: GitHub Blog, Feb 2025]

## Recent Trends
- AI-powered review suggestions gaining traction [source: The New Stack, Apr 2025]
- Integration with IDEs now standard expectation [source: InfoWorld, Mar 2025]
- Compliance automation (SOX, GDPR) driving enterprise adoption [source: ZDNet, Feb 2025]

## Gotchas/Failures
- High false positive rates still major complaint [source: Reddit DevOps, Mar 2025]
- Tool fatigue: teams using 5+ tools per PR [source: Hacker News discussion, Apr 2025]
- Configuration complexity drives abandonment [source: InfoQ survey, Jan 2025]
```

### Phase 2: Evidence-Gated Brainstorming Session

#### Step 2A: Brainstorming with Evidence Constraints
**Facilitator Rules:**
- Every idea must reference evidence from EP_A or EP_B
- Claims without citations get labeled "HYPOTHESIS - NEEDS VALIDATION"
- No solution can ignore the identified pain points

**Ideas Generated (with Evidence Anchoring):**

**Idea 1: Smart Review Routing**
- **Concept**: AI analyzes changed files and routes to appropriate reviewer
- **Evidence**: "73% report bottlenecks" + "Average 2.3 days" [EP_A]
- **Market validation**: "AI-powered suggestions gaining traction" [EP_B]
- **Reality check**: Must handle "configuration complexity" problem [EP_B]

**Idea 2: Graduated Security Gates**
- **Concept**: Different security levels based on code impact area
- **Evidence**: "34% security issues found in production" [EP_A]
- **Industry precedent**: Netflix auth/data pattern [EP_A]
- **Risk**: Could increase "tool fatigue" [EP_B]

**Idea 3: Developer Education Integration**
- **Concept**: Just-in-time security training during review
- **Evidence**: Address root cause of "34% security issues" [EP_A]
- **Gap identification**: Not found in current market solutions [EP_B]
- **HYPOTHESIS**: Developers want education vs enforcement - NEEDS VALIDATION

#### Step 2B: Evidence Gate Applied
**Gate Criteria:**
- [ ] Each idea cites specific evidence
- [ ] Addresses at least one documented pain point
- [ ] Acknowledges relevant market context
- [ ] Identifies assumptions requiring validation

**Gate Result:** Idea 3 fails - marked for research sprint

### Phase 3: Assumption Validation Sprint

#### Research Task for Idea 3:
**Query**: "developer preference training vs enforcement code review"
**Findings**: 
- Stack Overflow 2025: 68% prefer contextual education over blocking
- GitHub user study: 34% abandon tools that block without explanation
- **Evidence Update**: Training integration has market support

#### Updated Idea 3:
- **Concept**: Just-in-time security training during review
- **Evidence**: "34% security issues in production" [EP_A] + "68% prefer contextual education" [new research]
- **Validation**: User studies support approach [new research]

### Phase 4: Feasibility and Quality Gates

#### Reality Check Session (Red Team Pattern):
**Devil's Advocate Questions:**
1. **Resource Reality**: "Who maintains the training content?" 
   - **Answer required**: Content management strategy
   - **Evidence**: Industry tools require 1-2 FTE content maintenance [EP_B research]

2. **Technical Feasibility**: "How do you detect security-relevant changes?"
   - **Answer required**: Technical detection mechanism
   - **Evidence**: OWASP patterns provide classification rules [EP_A]

3. **User Adoption**: "Why would developers use this vs existing tools?"
   - **Answer required**: Differentiation strategy
   - **Evidence**: "Tool fatigue" and "configuration complexity" create opportunity [EP_B]

#### Testability Gate:
**Required for Advancement:**
- [ ] Success metric defined: "Reduce production security issues by 50%"
- [ ] Failure criteria: "If developer engagement <20% after 30 days, pivot"
- [ ] First experiment: "Week 1: Prototype detection rules for auth changes"
- [ ] Cost boundary: "Max 3 person-months to MVP"

### Phase 5: Architected Solution (Evidence-Informed)

#### Final Concept:
```yaml
name: "Contextual Security Coach"
evidence_basis:
  pain_point: "34% security issues reach production" [EP_A]
  market_gap: "No education-first tools found" [EP_B] 
  user_preference: "68% prefer education over blocking" [research]

core_features:
  - Smart detection of security-relevant changes [OWASP patterns, EP_A]
  - Just-in-time training cards [Stack Overflow user preference, research]
  - Graduated enforcement (warn → educate → block) [Netflix pattern, EP_A]

success_metrics:
  leading: "Developer engagement >20% monthly"
  lagging: "Production security issues reduced 50% in 6 months"

kill_criteria:
  - "If training content maintenance requires >2 FTE" [EP_B benchmark]
  - "If false positive rate >15%" [EP_B complaint threshold]
  - "If setup complexity exceeds 4 hours" [EP_B abandonment trigger]

first_experiments:
  week_1: "Prototype auth change detection rules"
  week_2: "A/B test: education cards vs traditional warnings"
  week_4: "Developer interview: content preferences"
```

### Phase 6: Handoff to Development

The development phase receives:
- **Evidence-validated concept** with citations for all major decisions
- **Pre-defined success/failure criteria** based on market research
- **Technical constraints** derived from industry patterns
- **User research** supporting design choices
- **Cost/complexity boundaries** informed by competitive analysis

This approach prevents the common failure where creative brainstorming produces ideas that are beautiful but impossible to implement, measure, or maintain.
