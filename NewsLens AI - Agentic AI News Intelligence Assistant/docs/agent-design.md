# Agent design

The research workflow is a LangGraph state machine: `plan → retrieve → synthesize`. This is useful because planning is semantic, retrieval is an auditable set of bounded calls, and synthesis needs evidence provenance and validation.

## State and limits

- User request is capped to 2,000 characters.
- A model may suggest no more than three search queries; code caps it again.
- Tavily returns at most five results per query, and no raw article body is requested.
- One explicitly supplied URL may be fetched; redirects are disabled and bytes are capped.
- Historical retrieval returns at most five records.
- Historical retrieval filters on the matching embedding mode/model to avoid mixing incompatible vector spaces.
- Only retrieved evidence IDs can be referenced in the output.

## Model boundary

`OpenAICompatibleClient` uses a configurable base URL and model names. Pydantic validates planner and synthesis JSON. When no chat key is configured, a deterministic one-query planner and source-bounded fallback response are used. Model claims with no valid evidence IDs are omitted from supported claims and moved to an uncertainty note.

## Tools

There is no shell, SQL, arbitrary browser, or write tool. `TavilySearchProvider`, `investigate_url`, and `NewsRepository.search_history` are the only research capabilities. Article text and search snippets are untrusted data; prompts tell the model to ignore instructions in source content.

## Evidence language

`PRIMARY` identifies an organization speaking about its own event or original research. `INDEPENDENT_REPORTING` is assigned only to configured reporting domains. Other results remain `UNKNOWN`. These labels do not imply truth or bias. The answer separately shows supported claims, uncertain details, source disagreements, and NewsLens analysis.
