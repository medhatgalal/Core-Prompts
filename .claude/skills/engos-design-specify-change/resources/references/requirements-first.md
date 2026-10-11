# Requirements-first route

Start from the requested outcome and existing contracts. Preserve the project's
format and read the shared requirements checklist before drafting.

1. Identify actor, current context, desired outcome and what is explicitly out.
2. Separate source facts, stakeholder requests and inferred assumptions. Keep a
   missing fact open; do not promote a source's suggested mechanism to a requirement.
3. Write stable requirements as condition, observable behavior and acceptance.
   For each, identify compatibility/unchanged behavior and attributable priority.
4. Include supported boundary, error and denial scenarios. If “fast” lacks a target,
   identify who can set it and the relevant usage context; never invent a number.
5. Reconcile conflicts and material assumptions with actual decision authority.
   Keep acceptance pending for the affected scope until the source conflict is
   resolved. Preserve existing acceptance when it covers the exact current draft.
6. Hand material design questions to architecture with this bounded requirements
   draft. Task planning follows accepted requirements and necessary design; this
   route does not produce executable tasks or approve them.

Example: “Export my filtered results” may establish filter preservation, but it
does not establish record limits, retention, delivery mechanism or new access
rights. Record those as questions if they affect acceptance. Do not add unrelated
features because they commonly appear beside exports.

For machine interchange, load the `contract` route and map the authoritative
specification to the schema. A schema pass is a structural observation only.
