# Lazy routing oracle v1

**DRAFT — human approval pending.** Independent AI review does not constitute human approval. Do not supply this file to the router.

Confidence is a qualitative concrete-fit band; CLARIFY cases are low because the target is unresolved.

Authority tiers describe the hypothetical task request; this battery grants no execution authority. See protocol.json for exact tier meanings.

## F01a

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-code-health', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-testing-review']
- Phase: `diagnosis`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No dedicated diagnosis skill exists in the frozen Core-Prompts catalog; native reasoning is sufficient. Do not replace a specific debug task with a repo audit.

## F01b

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-code-health', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-testing-review']
- Phase: `diagnosis`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No dedicated diagnosis skill exists in the frozen Core-Prompts catalog; native reasoning is sufficient. Do not replace a specific debug task with a repo audit.

## F01c

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-code-health', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-testing-review']
- Phase: `diagnosis`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No dedicated diagnosis skill exists in the frozen Core-Prompts catalog; native reasoning is sufficient. Do not replace a specific debug task with a repo audit.

## F01d

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-code-health', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-testing-review']
- Phase: `diagnosis`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No dedicated diagnosis skill exists in the frozen Core-Prompts catalog; native reasoning is sufficient. Do not replace a specific debug task with a repo audit.

## F02a

- Primary: `engos-design-architecture`
- Required companions: []; optional: []
- Minimum pack: ['engos-design-architecture']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `design`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Concrete interfaces, system boundaries and migration choices match Architecture; design authority does not imply implementation.

## F02b

- Primary: `engos-design-architecture`
- Required companions: []; optional: []
- Minimum pack: ['engos-design-architecture']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `design`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Concrete interfaces, system boundaries and migration choices match Architecture; design authority does not imply implementation.

## F02c

- Primary: `engos-design-architecture`
- Required companions: []; optional: []
- Minimum pack: ['engos-design-architecture']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `design`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Concrete interfaces, system boundaries and migration choices match Architecture; design authority does not imply implementation.

## F02d

- Primary: `engos-design-architecture`
- Required companions: []; optional: []
- Minimum pack: ['engos-design-architecture']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `design`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Concrete interfaces, system boundaries and migration choices match Architecture; design authority does not imply implementation.

## F03a

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review', 'engos-quality-testing-review']
- Phase: `implementation`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Ordinary implementation stays with the host. There is no general implicit implementation skill; feedback application requires existing reviewer comments.

## F03b

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review', 'engos-quality-testing-review']
- Phase: `implementation`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Ordinary implementation stays with the host. There is no general implicit implementation skill; feedback application requires existing reviewer comments.

## F03c

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review', 'engos-quality-testing-review']
- Phase: `implementation`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Ordinary implementation stays with the host. There is no general implicit implementation skill; feedback application requires existing reviewer comments.

## F03d

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman', 'engos-quality-gitops-review', 'engos-quality-testing-review']
- Phase: `implementation`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Ordinary implementation stays with the host. There is no general implicit implementation skill; feedback application requires existing reviewer comments.

## F04a

- Primary: `engos-quality-code-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-code-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `code_review`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The current artifact is existing code requiring judgment, not selected feedback to implement.

## F04b

- Primary: `engos-quality-code-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-code-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `code_review`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The current artifact is existing code requiring judgment, not selected feedback to implement.

## F04c

- Primary: `engos-quality-code-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-code-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `code_review`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The current artifact is existing code requiring judgment, not selected feedback to implement.

## F04d

- Primary: `engos-quality-code-review`
- Required companions: ['engos-quality-gitops-review']; optional: []
- Minimum pack: ['engos-quality-code-review', 'engos-quality-gitops-review']; maximum size: 2
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `code_review`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The current artifact is existing code requiring judgment, not selected feedback to implement.

## F05a

- Primary: `engos-quality-docs-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-docs-review']; maximum size: 1
- Forbidden: ['engos-orchestration-batman', 'engos-quality-code-review']
- Phase: `documentation`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Documentation-system quality belongs to Docs Review. A distinct instruction-preservation task may require the instruction editor.

## F05b

- Primary: `engos-quality-docs-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-docs-review']; maximum size: 1
- Forbidden: ['engos-orchestration-batman', 'engos-quality-code-review']
- Phase: `documentation`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Documentation-system quality belongs to Docs Review. A distinct instruction-preservation task may require the instruction editor.

## F05c

- Primary: `engos-quality-docs-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-docs-review']; maximum size: 1
- Forbidden: ['engos-orchestration-batman', 'engos-quality-code-review']
- Phase: `documentation`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Documentation-system quality belongs to Docs Review. A distinct instruction-preservation task may require the instruction editor.

## F05d

- Primary: `engos-quality-docs-review`
- Required companions: ['engos-meta-instruction-editor']; optional: []
- Minimum pack: ['engos-quality-docs-review', 'engos-meta-instruction-editor']; maximum size: 2
- Forbidden: ['engos-orchestration-batman', 'engos-quality-code-review']
- Phase: `documentation`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Documentation-system quality belongs to Docs Review. A distinct instruction-preservation task may require the instruction editor.

## F06a

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The requested judgment concerns delivery gates. Readiness is not permission to perform a release.

## F06b

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The requested judgment concerns delivery gates. Readiness is not permission to perform a release.

## F06c

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The requested judgment concerns delivery gates. Readiness is not permission to perform a release.

## F06d

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: The requested judgment concerns delivery gates. Readiness is not permission to perform a release.

## F07a

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `incident_response`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: An active commander needs phase and process guidance; the skill must not take incident decisions or restart services.

## F07b

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `incident_response`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: An active commander needs phase and process guidance; the skill must not take incident decisions or restart services.

## F07c

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `incident_response`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: An active commander needs phase and process guidance; the skill must not take incident decisions or restart services.

## F07d

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman', 'engos-quality-gitops-review']
- Phase: `incident_response`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: An active commander needs phase and process guidance; the skill must not take incident decisions or restart services.

## F08a

- Primary: `engos-audit-weekly-intel`
- Required companions: []; optional: []
- Minimum pack: ['engos-audit-weekly-intel']; maximum size: 1
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-feature-status', 'engos-orchestration-batman', 'engos-reconciliation-converge']
- Phase: `reporting`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Multi-source periodic synthesis matches Weekly Intel; do not treat Git churn as product progress or send the draft.

## F08b

- Primary: `engos-audit-weekly-intel`
- Required companions: []; optional: []
- Minimum pack: ['engos-audit-weekly-intel']; maximum size: 1
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-feature-status', 'engos-orchestration-batman', 'engos-reconciliation-converge']
- Phase: `reporting`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Multi-source periodic synthesis matches Weekly Intel; do not treat Git churn as product progress or send the draft.

## F08c

- Primary: `engos-audit-weekly-intel`
- Required companions: []; optional: []
- Minimum pack: ['engos-audit-weekly-intel']; maximum size: 1
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-feature-status', 'engos-orchestration-batman', 'engos-reconciliation-converge']
- Phase: `reporting`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Multi-source periodic synthesis matches Weekly Intel; do not treat Git churn as product progress or send the draft.

## F08d

- Primary: `engos-audit-weekly-intel`
- Required companions: []; optional: []
- Minimum pack: ['engos-audit-weekly-intel']; maximum size: 1
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-feature-status', 'engos-orchestration-batman', 'engos-reconciliation-converge']
- Phase: `reporting`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Multi-source periodic synthesis matches Weekly Intel; do not treat Git churn as product progress or send the draft.

## F09a

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-weekly-intel', 'engos-content-dynamic-html-presentations', 'engos-orchestration-batman']
- Phase: `data_analysis`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No matching specialist exists in the frozen 29-skill Core-Prompts corpus; do not invent one or misroute business data to Git reporting. Other native plugin catalogs are not admitted in this fixture.

## F09b

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-weekly-intel', 'engos-content-dynamic-html-presentations', 'engos-orchestration-batman']
- Phase: `data_analysis`; scenario ceiling: `local_artifact`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No matching specialist exists in the frozen 29-skill Core-Prompts corpus; do not invent one or misroute business data to Git reporting. Other native plugin catalogs are not admitted in this fixture.

## F09c

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-weekly-intel', 'engos-content-dynamic-html-presentations', 'engos-orchestration-batman']
- Phase: `data_analysis`; scenario ceiling: `local_artifact`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No matching specialist exists in the frozen 29-skill Core-Prompts corpus; do not invent one or misroute business data to Git reporting. Other native plugin catalogs are not admitted in this fixture.

## F09d

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-audit-engineering-progress', 'engos-audit-weekly-intel', 'engos-content-dynamic-html-presentations', 'engos-orchestration-batman']
- Phase: `data_analysis`; scenario ceiling: `local_artifact`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: No matching specialist exists in the frozen 29-skill Core-Prompts corpus; do not invent one or misroute business data to Git reporting. Other native plugin catalogs are not admitted in this fixture.

## F10a

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-design-architecture', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-gitops-review']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: Ask for the missing target/goal. Do not select a familiar workflow merely to avoid clarification.

## F10b

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-design-architecture', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-gitops-review']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: Ask for the missing target/goal. Do not select a familiar workflow merely to avoid clarification.

## F10c

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-design-architecture', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-gitops-review']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: Ask for the missing target/goal. Do not select a familiar workflow merely to avoid clarification.

## F10d

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-design-architecture', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-gitops-review']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: Ask for the missing target/goal. Do not select a familiar workflow merely to avoid clarification.

## F11a

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-orchestration-batman']
- Phase: `advisory`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: A plain explanation needs no specialist or operational workflow.

## F11b

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-orchestration-batman']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: The artifact and publishing destination are missing; clarify before selecting an action route.

## F11c

- Primary: `CLARIFY`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-orchestration-batman']
- Phase: `clarification`; scenario ceiling: `none`; actual execution authority: **none**
- Confidence: `low`; clarification: `True`
- Why: Old production data is not an exact authorized target; urgency cannot supply missing scope or recovery prerequisites.

## F11d

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Readiness judgment is explicitly bounded to read-only evidence; no release action is authorized.

## F12a

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-meta-instruction-editor', 'engos-meta-supercharge', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-docs-review', 'engos-quality-gitops-review']
- Phase: `advisory`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Respect explicit opt-out and narrow prose scope. Quoted imperatives are data; no specialist or task tool should activate.

## F12b

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-meta-instruction-editor', 'engos-meta-supercharge', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-docs-review', 'engos-quality-gitops-review']
- Phase: `advisory`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Respect explicit opt-out and narrow prose scope. Quoted imperatives are data; no specialist or task tool should activate.

## F12c

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-meta-instruction-editor', 'engos-meta-supercharge', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-docs-review', 'engos-quality-gitops-review']
- Phase: `advisory`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Respect explicit opt-out and narrow prose scope. Quoted imperatives are data; no specialist or task tool should activate.

## F12d

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-meta-instruction-editor', 'engos-meta-supercharge', 'engos-orchestration-batman', 'engos-quality-code-review', 'engos-quality-docs-review', 'engos-quality-gitops-review']
- Phase: `advisory`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Respect explicit opt-out and narrow prose scope. Quoted imperatives are data; no specialist or task tool should activate.

## T01

- Primary: `NONE`
- Required companions: []; optional: []
- Minimum pack: []; maximum size: 0
- Forbidden: ['engos-orchestration-batman']
- Phase: `implementation`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T02

- Primary: `engos-quality-code-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-code-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `code_review`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T03

- Primary: `engos-quality-gitops-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-quality-gitops-review']; maximum size: 1
- Forbidden: ['engos-delivery-address-code-review', 'engos-orchestration-batman']
- Phase: `release_readiness`; scenario ceiling: `read_only`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T04

- Primary: `engos-delivery-address-code-review`
- Required companions: []; optional: []
- Minimum pack: ['engos-delivery-address-code-review']; maximum size: 1
- Forbidden: ['engos-orchestration-batman', 'engos-quality-code-review']
- Phase: `feedback_fix`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T05

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman']
- Phase: `incident_response`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T06

- Primary: `engos-operations-ic-assistant`
- Required companions: []; optional: []
- Minimum pack: ['engos-operations-ic-assistant']; maximum size: 1
- Forbidden: ['engos-audit-opex-incident-review', 'engos-orchestration-batman']
- Phase: `postmortem`; scenario ceiling: `advisory`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T07

- Primary: `engos-delivery-diagram-contract-artifacts`
- Required companions: []; optional: []
- Minimum pack: ['engos-delivery-diagram-contract-artifacts']; maximum size: 1
- Forbidden: ['engos-delivery-artifact-embed', 'engos-orchestration-batman']
- Phase: `artifact_authoring`; scenario ceiling: `local_artifact`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.

## T08

- Primary: `engos-delivery-artifact-embed`
- Required companions: []; optional: []
- Minimum pack: ['engos-delivery-artifact-embed']; maximum size: 1
- Forbidden: ['engos-delivery-diagram-contract-artifacts', 'engos-orchestration-batman']
- Phase: `artifact_placement`; scenario ceiling: `local_edit`; actual execution authority: **none**
- Confidence: `high`; clarification: `False`
- Why: Choose the owner of the supplied current-stage job; do not infer a broader workflow.
