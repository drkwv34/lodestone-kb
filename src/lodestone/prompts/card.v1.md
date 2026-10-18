You convert one knowledge record into a retrieval card.
Reply with JSON only, no markdown fences, matching this schema:
{"question": "string <=200 characters, the question a user would ask",
 "summary": "string <=500 characters, factual synopsis",
 "resolution": "string <=500 characters, or empty if none",
 "entities": ["up to 8 system or topic names"],
 "code_refs": ["up to 12 identifiers, paths or error codes"]}

Use only facts from the record. Do not invent a resolution.
Prefer concrete names as they appear in the text.

<record kind="$kind" title="$title">
$body
</record>
