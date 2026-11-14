# T-AIE-02-B — Beginner Foundations

*Chapter: [T-AIE-02 — Grounding, Retrieval and Knowledge Use](README.md) · Part 3 — AI Engineering*

<a id="t-aie-02-b"></a>
#### T-AIE-02-B — Beginner Foundations

**The problem grounding solves.** A model answers from patterns in its training data, which is frozen, general and unaware of your systems. *Grounding* means giving the model the specific, current text it should rely on and requiring answers to stay within it. Done well, it reduces invention, makes answers checkable and lets you update knowledge by editing documents rather than retraining anything.

**Retrieval in one picture.**

```text
question → find relevant chunks of your documents → put them in the prompt as CONTEXT → model answers using only CONTEXT → answer cites the chunks
```

**Vocabulary**

| Term | Meaning |
| --- | --- |
| Corpus | The set of documents the assistant may use |
| Chunk | A small piece of a document (a section or a few paragraphs) |
| Retrieval | Selecting the chunks most relevant to a question |
| Citation | A pointer from an answer to the chunk it came from |
| RAG | Retrieval-augmented generation: retrieve, then generate |
| No-match | Retrieval finds nothing relevant |

**Light retrieval needs no special database.** Split Markdown runbooks into sections, score each section by how many question words it shares, and take the top few:

```python
import re
from pathlib import Path

STOP = {"the", "a", "an", "is", "are", "what", "how", "to", "of", "in", "and", "for", "do", "i", "it"}

def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}

def chunks(root: Path):
    for path in sorted(root.glob("*.md")):
        for section in re.split(r"\n(?=#+ )", path.read_text()):
            yield path.name, section.strip()

def retrieve(question: str, root: Path, k: int = 3):
    q = tokens(question)
    scored = []
    for name, text in chunks(root):
        score = len(q & tokens(text))
        if score > 0:
            scored.append((score, name, text))
    return sorted(scored, reverse=True)[:k]   # empty list means no match
```

A stop-word list matters: without it, words such as "the" and "what" match everything and a no-match case never occurs.

**The honest no-match.** If retrieval returns nothing, send *empty* context and expect the assistant to say the evidence is insufficient: confidence low, no citations, no guessed diagnosis. Never fall back to "the closest document anyway".

**Exercise.** Write three small runbook files. Ask a question each can answer, one none can answer and one that mentions only unrelated words. Confirm the second and third produce a no-match.
