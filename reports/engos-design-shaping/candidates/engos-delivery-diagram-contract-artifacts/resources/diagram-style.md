# Diagram style reference

Derived from the inspected team Mermaid Diagram Style Guide. Use LR for request
flows and TB for component hierarchies where it improves reading order. Label
edges with protocol or meaningful contract context. Keep node labels short;
sequence diagrams use at most eight participants, aliases and alt/opt sections.

| Role | Fill | Stroke | Text |
| --- | --- | --- | --- |
| Primary service | #326ce5 | #1a3e7a | #ffffff |
| Secondary internal component | #4fc3f7 | #0277bd | #01579b |
| Client | #e3f2fd | #1565c0 | #0d47a1 |
| UI | #bbdefb | #1565c0 | #0d47a1 |
| Data store | #e8f5e9 | #2e7d32 | #1b5e20 |
| Authentication/security | #fce4ec | #c62828 | #b71c1c |
| Background/async | #fff3e0 | #e65100 | #bf360c |

These examples' actual renderer rejected unescaped semicolons in sequence
message text. Use unambiguous plain wording and rerender; do not treat a text
edit as proof that the resulting diagram displays correctly. Preserve failed
source revisions as experiment evidence.
