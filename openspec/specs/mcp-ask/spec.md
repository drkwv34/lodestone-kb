# mcp-ask Specification

## Purpose
Expose LLM-free retrieval as a read-only MCP stdio server and run an optional
ask pipeline that plans tool calls, gathers evidence, cites only retrieved ids,
and refuses when evidence is empty.

## Requirements

### Requirement: FR-052 read-only MCP server
The system SHALL implement "FR-052": an MCP stdio server using the official
`mcp` Python SDK that exposes tools `search`, `grep`, `get_record`,
`list_sources`, `who_knows`, and `recent`. Every tool is LLM-free except
`search(rerank=true)`. Inputs are JSON-schema'd. `search` and `recent` output
`evidence.v1` hits. The process opens the SQLite database with `mode=ro` and
exposes no write tools. With `--offline`, the process makes no network
connections.

#### Scenario: Client lists and calls six tools
- **WHEN** an MCP client connects in-process or over stdio
- **THEN** `tools/list` returns exactly those six tools and each `tools/call`
  succeeds with a result that matches the documented output shape, and search
  or recent hits validate against `evidence.v1`

#### Scenario: Offline MCP makes no sockets
- **WHEN** the server is started with `--offline` and sockets are patched to
  raise
- **THEN** listing tools and calling `search` complete without opening a
  network connection

#### Scenario: Read-only database
- **WHEN** a write is attempted through the MCP database connection
- **THEN** SQLite rejects the write

### Requirement: FR-043 who-knows MCP tool
The system SHALL expose "FR-043" `who_knows` as an MCP tool that ranks authors
by in-scope records matching the topic, weighted by recency and burst or
reaction presence.

#### Scenario: Tool returns ranked people
- **WHEN** `who_knows` is called with a topic present in a fixture corpus
- **THEN** the result contains `people` with `author`, `score`, and example
  `records`

### Requirement: FR-044 recent MCP tool
The system SHALL expose "FR-044" `recent` as an MCP tool returning the most
recent in-scope records as `evidence.v1` hits.

#### Scenario: Tool returns recent hits
- **WHEN** `recent` is called with a positive limit
- **THEN** hits are `evidence.v1` packets in deterministic recency order

### Requirement: FR-053 ask pipeline
The system SHALL implement "FR-053": `ask` runs planner then parallel executor
then evidence normalisation then synthesis with numbered citations mapping to
evidence ids. When the evidence packet is empty it SHALL refuse to answer and
return `insufficient_evidence: true`. Answer text MAY cite only retrieved
evidence ids.

#### Scenario: Citations map to retrieved ids
- **WHEN** FakeLLM synthesises an answer from a non-empty evidence packet
- **THEN** every citation in the answer text refers to an evidence id that was
  retrieved, and unsupported citation numbers are stripped

#### Scenario: Empty evidence refuses
- **WHEN** no records match the planned tools
- **THEN** the answer has `insufficient_evidence` true and does not invent
  citations

### Requirement: FR-054 planner validation and fallback
The system SHALL implement "FR-054": the planner receives a compact catalog
(projects, sources, kinds, counts, date ranges, top terms) and returns JSON
tool calls from the allow-list `search`, `grep`, `who_knows`, `recent`. Invalid
or empty plans SHALL fall back to a deterministic default: `search` plus
`grep` when the query contains an identifier-like token.

#### Scenario: Valid plan uses allow-listed tools
- **WHEN** the planner JSON contains only allow-listed tools with argument
  objects
- **THEN** those calls are executed and unknown tools are dropped

#### Scenario: Malformed plan uses default
- **WHEN** the planner returns malformed JSON, a non-object, or no valid calls
- **THEN** the fallback is `search` of the question, plus `grep` if the
  question contains an identifier-like token

### Requirement: FR-055 sufficiency loop
The system SHALL implement "FR-055": after a synthesis draft, a cheap
sufficiency check may issue at most `ask.max_rounds - 1` follow-up tool rounds
with refined queries. Every round's calls are logged. The loop SHALL terminate
in at most `ask.max_rounds` rounds even when the model always says
insufficient.

#### Scenario: Adversarial model still terminates
- **WHEN** a FakeLLM always replies that evidence is insufficient
- **THEN** ask returns after at most `max_rounds` rounds and logs each round's
  calls

### Requirement: FR-056 untrusted content handling
The system SHALL implement "FR-056": retrieved text is placed inside
`<evidence id=..>` blocks with an instruction-hierarchy note; planner tool
arguments are restricted to the allow-list; a prompt-injection fixture in a
document MUST NOT alter tool selection when using a rule-based FakeLLM stub,
and MUST NOT change the tool-call or output contract.

#### Scenario: Ten injection payloads stay data
- **WHEN** each of ten injection payloads is indexed and asked about with a
  rule-based FakeLLM
- **THEN** planned tools stay on the allow-list, citations still map only to
  retrieved ids, and the output contract (text, citations, insufficient_evidence)
  is unchanged in shape
