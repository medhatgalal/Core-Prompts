# Design-first route

A supplied design is an input whose product assumptions need examination. It is
not automatic proof of accepted requirements or permission to implement.

1. Identify the supplied design and exact revision; inspect complete relevant
   content. Record inaccessible portions. Keep verified byte hashes separate from
   references whose contents could not be retrieved.
2. Extract behaviors and user expectations implied by the design. Mark each
   unsupported assertion as an assumption with an ID, source and affected scope.
3. Compare those assertions with the user's outcome, existing requirements and
   compatibility promises. Produce explicit conflicts and missing acceptance
   conditions, including migration and failure behavior when relevant.
4. Reconcile acceptance and material assumptions with the real decision authority
   before task approval. A technically detailed design cannot overrule intent.
   Deferred assumptions hold dependent scope unless an attributable exclusion
   removes the dependency. Do not mark an assumption confirmed from silence.
5. Send material choices or revisions back to architecture. Keep the original
   design reference and record which changed requirements require its reassessment.
6. Return the reconciled requirement revision, design references, decisions and
   remaining holds to the authorized next owner. Do not create executable tasks.

Example: a queue design implies that results arrive later, while the request says
immediate download. Specify both claims and the affected acceptance condition.
Leave async behavior unaccepted until the conflict is resolved; a valid hash or
connected requirement/design IDs cannot resolve it.

Load the `contract` route only if machine interchange is required. The schema
permits drafts with open assumptions; schema success cannot authorize task approval.
