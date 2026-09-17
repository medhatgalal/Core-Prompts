# Round one render observations

Model capacity: actual Mermaid CLI rendering was attempted with the cached CLI
and its bundled renderer. Component PNG generated. Sequence rendering failed
with exit 1: `Parse error on line 8`, at the message ending `bind response data`
before `else Invalid candidate`. Data-flow was not attempted because the serial
render loop stopped on the failure. G3 cannot pass this source revision.

The original sequence source remains unchanged as evidence. Round two must
repair the syntax and rerender all three outputs. A source parser pass still
requires subsequent pixel inspection. No output from a failed render is accepted.

Configuration deployment: component PNG generated. Sequence rendering failed
with exit 1 on line 11, at `Denied; no writes` before `else Authorized`. Its
data-flow was also not reached by the serial loop. Both observed sequence failures
involve unescaped semicolons in message text. Round two should use an unambiguous
message phrase and prove the repaired source renders; no speculative renderer
workaround is counted as a fix.

The model-capacity component PNG was pixel-inspected: node names, source/config
boundary and the proposed response addition are visible with no clipping.
No corresponding sequence or data-flow visual pass exists for round one.

The first npx registry lookup stalled and was terminated only for this task;
the same already-cached renderer was invoked directly. This is a tooling lookup
recovery, not diagram success evidence.
