import os
import datetime

FEATURES = [
    ("001-saas-foundation", "SaaS Foundation and tenant isolation", "SaaS Foundation"),
    ("002-knowledge-engine", "Knowledge & Evidence Engine", "Knowledge Engine"),
    ("003-customer-case", "Customer Case Intelligence", "Customer Case"),
    ("004-market-intelligence", "Market Intelligence", "Market Intel"),
    ("005-idea-intelligence", "Idea Intelligence", "Idea Intel"),
    ("006-safe-workflow", "Safe Workflow Automation", "Safe Workflow"),
    ("007-frontend-experience", "Frontend and Product Experience", "Frontend"),
    ("008-eval-security", "Evaluation, Security, and Release", "Eval & Security")
]

DATE_STR = datetime.datetime.now().strftime("%Y-%m-%d")

# Load templates
TEMPLATE_DIR = r"D:\VERITAS_AI\.specify\templates"
with open(os.path.join(TEMPLATE_DIR, "spec-template.md"), "r", encoding="utf-8") as f:
    spec_template = f.read()

with open(os.path.join(TEMPLATE_DIR, "plan-template.md"), "r", encoding="utf-8") as f:
    plan_template = f.read()

with open(os.path.join(TEMPLATE_DIR, "tasks-template.md"), "r", encoding="utf-8") as f:
    tasks_template = f.read()

def generate_spec(feature_dir, feature_name, short_name):
    content = spec_template
    content = content.replace("[FEATURE NAME]", feature_name)
    content = content.replace("[###-feature-name]", feature_dir)
    content = content.replace("[DATE]", DATE_STR)
    content = content.replace("$ARGUMENTS", f"Build the {feature_name} capability for VERITAS AI.")
    
    # Fill in some user stories
    story1 = f"### User Story 1 - Core {short_name} (Priority: P1)\n\nAs a user, I want to use the {short_name} so that I can achieve my goal securely.\n\n**Why this priority**: It is the foundation of the feature.\n\n**Independent Test**: Can be tested via API.\n\n**Acceptance Scenarios**:\n1. **Given** a valid request, **When** I trigger the action, **Then** it completes successfully."
    
    # simple text replacement for placeholders
    import re
    content = re.sub(r"### User Story 1.*?---", story1 + "\n\n---", content, flags=re.DOTALL)
    
    content = content.replace("FR-001**: System MUST [behavior]", f"FR-001**: System MUST implement {feature_name} core logic.")
    content = content.replace("FR-002**: System MUST [behavior]", f"FR-002**: System MUST integrate with the VERITAS AI stack.")
    
    return content

def generate_plan(feature_dir, feature_name, short_name):
    content = plan_template
    content = content.replace("[FEATURE]", feature_name)
    content = content.replace("[###-feature-name]", feature_dir)
    content = content.replace("[DATE]", DATE_STR)
    content = content.replace("[link]", f"../{feature_dir}/spec.md")
    
    content = content.replace("[e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]", "Python 3.13 and Node.js 24")
    content = content.replace("[e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]", "FastAPI, Next.js, LangGraph")
    content = content.replace("[if applicable, e.g., PostgreSQL, CoreData, files or N/A]", "PostgreSQL with pgvector")
    content = content.replace("[e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]", "pytest, npm run test")
    content = content.replace("[e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]", "Docker/Linux Server")
    content = content.replace("[e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]", "web-service")
    
    return content

def generate_tasks(feature_dir, feature_name, short_name):
    content = tasks_template
    content = content.replace("[FEATURE NAME]", feature_name)
    content = content.replace("[###-feature-name]", feature_dir)
    
    # We can just leave the task template as mostly is, but ensure checklists are valid
    # Replace the sample tasks with real ones
    real_tasks = f"""## Phase 1: Setup
- [ ] T001 Initialize database schemas for {short_name} in `backend/app/db/`
- [ ] T002 [P] Create initial API routes in `backend/app/api/routes/`

## Phase 2: Foundational
- [ ] T003 Implement data access layer for {short_name}
- [ ] T004 Build LangGraph nodes (if applicable) in `backend/app/agent/`

## Phase 3: User Story 1
- [ ] T005 [US1] Develop core service logic
- [ ] T006 [US1] Write integration tests in `backend/tests/`
"""
    # Replace Phase 1-3 in template
    import re
    content = re.sub(r"## Phase 1: Setup.*?---", real_tasks + "\n---", content, flags=re.DOTALL)
    
    return content

base_dir = r"D:\VERITAS_AI\specs"
os.makedirs(base_dir, exist_ok=True)

for feat_dir, feat_name, short_name in FEATURES:
    dir_path = os.path.join(base_dir, feat_dir)
    os.makedirs(dir_path, exist_ok=True)
    
    # Spec
    with open(os.path.join(dir_path, "spec.md"), "w", encoding="utf-8") as f:
        f.write(generate_spec(feat_dir, feat_name, short_name))
        
    # Plan
    with open(os.path.join(dir_path, "plan.md"), "w", encoding="utf-8") as f:
        f.write(generate_plan(feat_dir, feat_name, short_name))
        
    # Tasks
    with open(os.path.join(dir_path, "tasks.md"), "w", encoding="utf-8") as f:
        f.write(generate_tasks(feat_dir, feat_name, short_name))

print("Successfully generated all specs, plans, and tasks.")
