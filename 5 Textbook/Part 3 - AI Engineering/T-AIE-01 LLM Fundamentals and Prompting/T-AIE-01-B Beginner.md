# T-AIE-01-B — Beginner Foundations

*Chapter: [T-AIE-01 — LLM Fundamentals and Prompting](README.md) · Part 3 — AI Engineering*

<a id="t-aie-01-b"></a>
#### T-AIE-01-B — Beginner Foundations

## Why this matters

A large language model (LLM) is the first component many engineers meet that is *useful and unreliable at the same time*. It can summarise a long incident thread, explain an unfamiliar error message, draft a runbook step or classify a ticket in seconds. It can also state a wrong answer in exactly the same confident tone as a right one, give a different answer to the same question tomorrow, and quietly follow instructions that were hidden in the text it was asked to read.

Ordinary software fails in ways you can usually reproduce and explain. An LLM fails *statistically*: it is right most of the time on some inputs and wrong far more often on others, and you cannot tell which from the look of the answer. So you stop asking "does it work?" and ask "how often does it work, on which inputs, how do I know, and what happens when it does not?"

This section builds the vocabulary and mental model for that habit: what an LLM does, tokens and context windows, training versus inference, why hallucination happens, a first scoped prompt and a small, honest prompt experiment. It assumes you can read short Python and call an HTTP API; it does **not** assume machine-learning background. Examples use a neutral read-only assistant, `ops-assistant`, that answers questions about an `orders` service from runbooks. Nothing here depends on any other course material. Numbers marked *illustrative* show shapes, not measured results of any model.

## First principles: what an LLM does

An LLM is a function with one job: given a sequence of text pieces, produce a probability for every possible *next* piece. A program (the *decoder*) then picks one, appends it, and asks the function again. Repeat until a stop condition is met. Everything else — answering, summarising, translating, writing code — is that single loop applied to a well-chosen starting text.

```text
Input so far:   "The readiness endpoint returns 503 when the"
Model output:   a probability for each possible next token, for example (illustrative)
                  " database"   0.41
                  " service"    0.12
                  " cache"      0.09
                  ...thousands more, each with a small probability
Decoder picks one (say " database"), appends it, and asks again.
```

Three consequences follow, and the rest of this chapter returns to them repeatedly.

1. **The model produces plausible continuations, not verified facts.** It is good at text that *looks like* a correct answer; whether the content is true depends on whether learned patterns line up with reality for your question.
2. **It has no built-in lookup and no reliable "I do not know".** Unless a surrounding system supplies documents, it answers from patterns in its parameters. Saying "I do not know" is just another pattern, encouraged by training and your prompt, and imperfect.
3. **Output is sampled, so it can vary.** The same question can produce two different valid-looking answers.

Analogy, and its limit: an LLM is like a very well-read colleague who answers instantly from memory and never checks a source. It fails because a human usually knows when they are guessing; the model's tone is not a reliable signal of how likely it is to be right.

## Tokens: the unit of everything

Models do not read letters or words. They read **tokens**: chunks of text from a fixed vocabulary, produced by a program called a *tokenizer*. Common words are often one token; rare words, names, numbers and code are often split into several.

```text
Text:     "database: unreachable"
Tokens:   ["database", ":", " un", "reach", "able"]      # illustrative split, not any real tokenizer
Count:    5 tokens
```

Why you care: **cost** is usually charged per token (input and output priced separately); **limits** are measured in tokens; **latency** grows with tokens, especially output tokens, which are generated one after another; and **odd behaviour** often traces to tokens, since a model does not see the letters inside a token, one reason letter counting and exact arithmetic are unreliable without help.

How many tokens is a text? It depends on the tokenizer and the language. A common rule of thumb for English prose is three to four characters per token. Code, numbers, logs and many non-English languages usually take more tokens per character. Estimate for planning; use the provider's tokenizer or usage report for decisions.

```python
def rough_token_estimate(text: str, chars_per_token: float = 4.0) -> int:
    """A planning estimate only. Real counts come from the provider's tokenizer or usage report."""
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be positive")
    return max(1, round(len(text) / chars_per_token))


runbook = "database: unreachable means the service could not run a test query against the database."
print(rough_token_estimate(runbook))        # a planning number, not a measurement
```

Good enough to notice that a 400,000-character log will not fit; not good enough to bill a customer.

## The context window: the model's working memory for one call

The **context window** is the maximum number of tokens the model can take into account in a single call. In most APIs it covers the input (system prompt, conversation, documents you attached) **plus** the output the model writes back. If the total would exceed the limit, the call fails or the input is truncated, depending on the provider and settings.

```text
|<------------------------ context window ------------------------>|
| system prompt | context chunks | question | reserved for the answer |
|     400       |     3,000      |    60    |         1,000           |   tokens (illustrative)
```

Four facts to hold on to:

- **A call has no memory of previous calls.** A chat application *looks* like it remembers because the program resends earlier messages with every request.
- **A bigger window is not free.** More tokens cost more and take longer, and a model may not use every part of a long input equally well.
- **You must reserve space for the answer.** If the input fills the window, there is no room to reply.
- **Anything in the window can influence the output**, including text you did not write — a pasted email, a retrieved document, a web page. That becomes a security concern in later sections.

A budget check is simple: estimated system, chunk and question tokens plus the reserved output must not exceed the window.

## Training versus inference

Two phases of a model's life are constantly confused, and the confusion causes real mistakes.

| | Training | Inference |
| --- | --- | --- |
| What happens | Parameters (the numbers inside the model) are adjusted to predict text well | The fixed model is run to produce output for an input |
| When | Before you ever call the model; done by the provider | Every time you send a request |
| Does the model change? | Yes — that is the point | **No.** Your prompt does not change the model's parameters |
| What data is involved | Large collections of text, then curated examples and feedback | Only the tokens in your request |

Practical consequences:

- **The model does not learn from your conversation.** A fact told in one call is unknown to the next unless you include it again. (Whether a provider uses your data for *future* training is a contractual question; see the Professional section.)
- **The model has a knowledge horizon.** Its parameters reflect text collected up to some date. It may not know last month's release or your internal systems; your documents are not in there unless you supply them.
- **Behaviour is shaped in stages.** General language patterns first; later stages teach instruction following, declining some requests and formatting. The result *behaves* like an assistant while still predicting tokens.
- **Product behaviour is changed at inference time**, by changing the prompt and supplied data. Fine-tuning exists but is slower and costlier (later levels).

## Temperature and why the same question can give two answers

At each step the decoder chooses a token from the model's probabilities. **Temperature** controls how adventurous that choice is.

| Setting | Behaviour | When it suits |
| --- | --- | --- |
| Low (near zero) | Picks the most likely tokens; much more repeatable | Extraction, classification, structured output, tests |
| Medium | Some variety | Drafting text where variation is welcome |
| High | Occasionally picks unlikely tokens; creative and sometimes erratic | Brainstorming; rarely appropriate for operations |

Two cautions: low temperature is **more repeatable, not guaranteed identical** (and a provider changing the model under a name changes output regardless); and repeatability is not correctness, since a model can be reliably wrong. For anything an operator will act on, start low and verify with tests.

## Hallucination: plausible but unsupported output

**Hallucination** means output that reads as fluent and confident but is false or unsupported. It is not a rare glitch; it is a direct consequence of "predict plausible text".

Typical forms, each shown with an example from our service:

| Form | Example from `ops-assistant` | Why it is dangerous |
| --- | --- | --- |
| Invented fact | "The readiness endpoint returns 418 when the cache is cold" (no such behaviour exists) | A reader acts on behaviour that does not exist |
| Invented source | "See runbooks/readiness.md section 4.2" when no such section exists | Looks verifiable, wastes time, builds false trust |
| Accepting a false premise | "Since DNS caused the outage, how do I fix DNS?" answered in detail | Reinforces a wrong diagnosis |

Why it happens: training rewards likely text, not checked claims; when asked about something it has no information on, the likeliest continuation is still a fluent answer; and specific-looking details (numbers, section names, flags) are easy to produce and hard to spot as invented.

What reduces it, in order of strength: (1) **give the evidence** and say to answer only from it; (2) **require citations** of supplied chunks and check them in code; (3) **allow "I cannot tell from the provided material"** with a defined output shape; (4) **keep the task narrow**; (5) **verify** before anyone acts, in proportion to the cost of being wrong. None removes hallucination; they make it rarer and easier to catch.

## A general chatbot is not a product feature

Operators under pressure ask: what does this health payload mean, which runbook applies, what must I not do? An unscoped chatbot answers from its training data and invents confidence. A *scoped* feature answers from your documents, refuses out-of-scope requests and is judged against an evaluation you own.

| Approach | Outcome |
| --- | --- |
| "Ask anything" bot | Invented procedures, mutable advice, no way to measure quality |
| Scoped, read-only assistant | Answers from runbooks, refuses mutations, has an evaluation bar |
| Agent with write tools | Needs explicit controls (see T-AIE-04) |

## Roles in a conversation

Chat-style APIs take a list of messages, each tagged with a role.

| Role | Job |
| --- | --- |
| System | Fixed product policy: scope, format, refusal rules |
| User | The question and any supplied data |
| Assistant | The model's reply; must obey the system policy |

Putting policy in the system message and data in the user message is a good habit, but a convention the model respects *most* of the time, not a security boundary.

## A first prompt

```text
SYSTEM: You are ops-assistant. You answer questions about the orders service using ONLY
the CONTEXT provided. You never give commands that change systems. If the context does not
contain the answer, say so. Reply as JSON: {"answer": str, "confidence": "low|medium|high",
"citations": [str], "refused": bool, "refusal_reason": str}.

USER: Question: What does "database: unreachable" in the readiness response mean?
CONTEXT:
[runbooks/readiness.md] "database: unreachable means the service could not run a test query..."
```

Read it line by line, as you would read code:

| Line or phrase | What it does |
| --- | --- |
| "You are ops-assistant." | Names a role; gives the model a style and purpose |
| "using ONLY the CONTEXT provided" | Narrows the source of truth to what you supply |
| "If the context does not contain the answer, say so." | Makes abstention an allowed behaviour |
| "Reply as JSON: ..." | Defines an output contract a program can check |
| `[runbooks/readiness.md]` | A label the model can cite and your code can verify |

A plausible well-behaved reply (illustrative):

```json
{
  "answer": "It means the service could not run a test query against its database when it was asked whether it is ready.",
  "confidence": "medium",
  "citations": ["runbooks/readiness.md"],
  "refused": false,
  "refusal_reason": ""
}
```

**Why structured output.** Asking for JSON lets programs parse the answer, check fields and test behaviour automatically, rather than scraping prose. A parser either accepts the text or rejects it, and a rejection is information you can count.

## Vocabulary in context

| Term | Meaning |
| --- | --- |
| Token | A chunk of text (part of a word) the model reads and writes; cost and limits are measured in tokens |
| Context window | The maximum number of tokens the model can consider at once (input plus output) |
| Prompt | The input text and messages given to the model |
| System prompt | Fixed instructions defining the model's role and rules |
| Temperature | A setting controlling randomness; low is more repeatable |
| Hallucination | Plausible but unsupported or false output |

## A first prompt experiment

A prompt experiment is a small, controlled test of a question you can answer with data. The Beginner aim is the *habit* of comparing a change against fixed cases instead of trusting one impressive answer.

**Question:** does adding "If the context does not contain the answer, say so" change how often the assistant invents an answer to an unanswerable question?

**Cases.** Write ten questions and the correct behaviour *before* seeing any output:

| Group | Count | Example | Correct behaviour |
| --- | --- | --- | --- |
| Answerable from the context | 4 | "What does `database: unreachable` mean?" | Answers, cites the chunk |
| Not answerable from the context | 4 | "What is the on-call phone number?" | States that the evidence is insufficient |
| Asks for a change | 2 | "Restart the orders service." | Refuses |

**Variants.** A is the system prompt without the abstention sentence; B is identical plus that sentence. Change exactly one thing. Run each case on each variant three times, because output varies, and record everything.

```python
import csv
import json


def run_experiment(call_model, variants: dict[str, str], cases: list[dict], context: str,
                   repeats: int = 3, out_path: str = "experiment.csv") -> None:
    """call_model(system, user) -> raw text. Rows are written to a CSV for hand-labelling."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant", "case_id", "group", "run", "valid_json", "refused", "raw_output", "label"])
        for name, system in variants.items():
            for case in cases:
                user = f"Question: {case['question']}\nCONTEXT:\n{context}"
                for run in range(1, repeats + 1):
                    raw = call_model(system, user)
                    try:
                        refused = bool(json.loads(raw).get("refused")); valid = True
                    except (json.JSONDecodeError, AttributeError):
                        refused, valid = False, False
                    w.writerow([name, case["id"], case["group"], run, valid, refused, raw, ""])
```

After the run, fill the `label` column by hand (`correct`, `wrong`, `unclear`) against the behaviour you wrote first, then count per group and variant: answerable out of 12, unanswerable out of 12, mutation out of 6, invalid JSON out of 30.

**Reading the result.** With ten cases the numbers are small. A difference of one or two rows is not evidence; a consistent shift across all unanswerable cases is worth following up. The honest conclusion is often "looks helpful, I need more cases". Do not report behaviour from one run, and do not edit the cases after seeing results, which quietly turns the test into a flattering one.

**Rules to carry forward:** decide expected behaviour first; change one thing at a time; repeat runs; keep the cases as the start of your evaluation set (see T-AIE-03).

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Treating the model as a database | Confident answer about your internal system, wrong in the details | Supply the documents; require citations; allow "insufficient evidence" |
| Judging a prompt by one run | "It worked" on Monday, fails on Tuesday | Run a case set several times and count |
| Assuming the chat remembers | A follow-up lacks context or contradicts itself | Resend the relevant history; know what you resend |
| Ignoring the output budget | Answers cut off mid-sentence, broken JSON | Reserve output tokens; set a maximum; handle truncation |
| Trusting well-formed JSON | Valid structure, wrong content | Validate values and citations in code |
| Giving the assistant write access early | A wrong answer becomes a wrong action | Start read-only; add controls before any write tool (see T-AIE-04) |

## Knowledge consolidation

- An LLM **predicts the next token**; fluent output is not verified output.
- **Tokens** are the unit of cost, limit and latency; estimate roughly, measure with the provider's tokenizer or usage report.
- The **context window** holds input plus output for one call; the model has **no memory between calls** other than what you resend.
- **Training** changes the model before you call it; **inference** does not. Your prompt teaches nothing permanently.
- **Temperature** trades variety for repeatability; low is more repeatable, never a guarantee, and never a measure of correctness.
- **Hallucination** is a normal behaviour to design around: ground, cite, allow abstention, narrow the task, verify.
- A **scoped, read-only, evidence-based** assistant is a feature; an unscoped chatbot is a liability.
- **System prompt rules are requests**, not guarantees.
- A **prompt experiment** compares variants on fixed cases with expected behaviour written first and honest counts.

## Exercises

**Exercise 1 — Count tokens.** Take five texts: an English sentence, a log line, a JSON object, a code block and a sentence in another language. Estimate with `rough_token_estimate`, compare with your provider's tokenizer or usage report, and note where the estimate was furthest off.

**Exercise 2 — Prove the model has no memory.** Tell the model a made-up fact ("the staging cluster is named basalt") in one call; ask for the name in a second call; then send both messages in one call as history. Record and explain the three behaviours.

**Exercise 3 — Hunt a hallucination.** With no context, ask about an invented flag of a real tool. Then supply a context that lacks the answer plus an abstention instruction and repeat three times. Compare.

**Exercise 4 — The scoped assistant.** Write a system prompt for a read-only assistant over three short runbook excerpts of your own. Test one answerable, one unrelated and one change-request question. Record what happened and what you would change.

**Exercise 5 — Run the experiment.** Complete the ten-case, two-variant, three-repeat experiment. Label every row by hand, fill the counts and write three sentences: what the numbers show, what they do not, and which cases you would add.

**Solution notes.**

*Exercise 1.* Illustrative expectation: plain English is closest to the rule of thumb; JSON, code and logs usually give more tokens than estimated; other languages often give more tokens per character. One constant does not fit all content, so budgets need headroom.

*Exercise 2.* Expected pattern: without history the model does not know the name (it may guess, which is a hallucination test in itself); with history it answers correctly. "Memory" is the application resending messages; if you see otherwise, check whether your client library adds history for you.

*Exercise 3.* Without context a model may invent a plausible flag; with a no-answer context and an abstention instruction it should more often say the information is unavailable, though not every time. Report counts out of three and note any run that still invented something.

*Exercise 4.* Typical improvements: an explicit refusal sentence for change requests, citations by label, an `insufficient evidence` output shape, tighter format rules. Passing three questions is a smoke test, not a quality claim.

*Exercise 5.* State results as "x of y", not percentages that suggest false precision, for example "variant B abstained on 11 of 12 unanswerable runs and A on 7 of 12; suggestive, not proof; I will add twenty more cases" (invented numbers, shown only as a template). If both variants behaved alike, that is also a result. Keep the file; it seeds your evaluation set.
