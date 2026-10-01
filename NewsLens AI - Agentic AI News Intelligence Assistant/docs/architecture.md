# Architecture

## Overall system

```mermaid
flowchart TB
  subgraph Discord
    Commands[/brief · /ask · /investigate · /finland/]
  end
  subgraph Application
    Scheduler[APScheduler]
    Pipeline[Discovery pipeline]
    Graph[LangGraph research workflow]
    Brief[Briefing service]
  end
  RSS[Configured RSS / Atom] --> Pipeline
  Scheduler --> Pipeline --> Store[(PostgreSQL + pgvector)]
  Store --> Brief --> Commands
  Commands --> Graph
  Graph --> Search[Optional Tavily search]
  Graph --> Fetch[One public article fetch]
  Graph --> Store
  Search --> Graph
  Fetch --> Graph
  Graph --> Commands
```

## Automated news pipeline

```mermaid
flowchart LR
  Timer[Scheduler or CLI] --> Feed[Discovery providers]
  Feed --> Candidate[Normalized candidates]
  Candidate --> Relevant[Interest classification]
  Relevant --> Cluster[Recency-bounded title clustering]
  Cluster --> Persist[Story + article records]
  Persist --> Brief[Brief generation]
  Brief --> Discord[Discord channel]
```

## Interactive research flow

```mermaid
flowchart LR
  User[Discord question] --> Plan[Plan up to 3 queries]
  Plan --> Gather[Bounded retrieval]
  Gather --> Search[Optional Tavily]
  Gather --> URL[Optional one public URL]
  Gather --> History[Historical vector retrieval]
  Search --> Synthesis[Evidence synthesis]
  URL --> Synthesis
  History --> Synthesis
  Synthesis --> IDs[Validate cited evidence IDs]
  IDs --> Response[Answer with sources and uncertainty]
```

## Story clustering flow

```mermaid
flowchart TD
  A[Candidate] --> U{Canonical URL exists?}
  U -->|Yes| Drop[Count duplicate]
  U -->|No| Recent[Load stories from 10-day window]
  Recent --> Similar[Compare title token Jaccard similarity]
  Similar --> Match{Best score ≥ threshold?}
  Match -->|Yes| Attach[Attach article and update story]
  Match -->|No| Create[Create a new story]
  Attach --> Save[Persist source metadata]
  Create --> Save
```

## Historical RAG flow

```mermaid
flowchart LR
  Question --> Embed[Configured embeddings or lexical hash fallback]
  Embed --> Vector[(pgvector vector 1536)]
  Vector --> Neighbors[Cosine nearest articles]
  Neighbors --> Provenance[Return title, snippet, date, source type, URL]
  Provenance --> Synthesis[Evidence-aware response]
```

PostgreSQL is the target runtime. SQLite is used for deterministic test coverage; it scores vectors in Python. ORM metadata includes SQLite JSON fallback for the vector column, while the migration is PostgreSQL/pgvector specific.
