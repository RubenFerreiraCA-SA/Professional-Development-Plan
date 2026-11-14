# T-AIE-01-B — Beginner Foundations

*Chapter: [T-AIE-01 — LLM Fundamentals and Prompting](README.md) · Part 3 — AI Engineering*

<a id="t-aie-01-b"></a>
#### T-AIE-01-B — Beginner Foundations

**What an LLM is.** A large language model predicts the next piece of text (a *token*) given the text so far. With enough training it can follow instructions, summarise, classify, write code and answer questions. It does not look things up, it does not know what it does not know, and it can state wrong things fluently. That last property — often called *hallucination* — is the central risk to design around.

**Vocabulary**

| Term | Meaning |
| --- | --- |
| Token | A chunk of text (part of a word) the model reads and writes; cost and limits are measured in tokens |
| Context window | The maximum number of tokens the model can consider at once (input plus output) |
| Prompt | The input text and messages given to the model |
| System prompt | Fixed instructions defining the model's role and rules |
| Temperature | A setting controlling randomness; low is more repeatable |
| Completion | The model's output |
| Hallucination | Plausible but unsupported or false output |

**A general chatbot is not a product feature.** Operators under pressure ask: what does this health payload mean, which runbook applies, what must I not do? An unscoped chatbot answers from its training data and invents confidence. A *scoped* feature answers from your documents, refuses out of scope requests, and is judged against an evaluation you own.

| Approach | Outcome |
| --- | --- |
| "Ask anything" bot | Invented procedures, mutable advice, no way to measure quality |
| Scoped, read-only assistant | Answers from runbooks, refuses mutations, has an evaluation bar |
| Agent with write tools | Needs explicit controls (see T-AIE-04) |

**Roles in a conversation**

| Role | Job |
| --- | --- |
| System | Fixed product policy: scope, format, refusal rules |
| User | The question and any supplied data |
| Assistant | The model's reply; must obey the system policy |

**A first prompt**

```text
SYSTEM: You are ops-assistant. You answer questions about the orders service using ONLY
the CONTEXT provided. You never give commands that change systems. If the context does not
contain the answer, say so. Reply as JSON: {"answer": str, "confidence": "low|medium|high",
"citations": [str], "refused": bool, "refusal_reason": str}.

USER: Question: What does "database: unreachable" in the readiness response mean?
CONTEXT:
[runbooks/readiness.md] "database: unreachable means the service could not run a test query..."
```

**Why structured output.** Asking for JSON lets programs parse the answer, check fields and test behaviour automatically, rather than scraping prose.

**Exercise.** Write a system prompt for a read-only assistant over a small set of documents. Test three questions: one answerable, one unrelated and one that asks the assistant to change something. Record what happened and what you would change.
