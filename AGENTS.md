# AGENTS.md

## Language rule

**If use English, write ASD-STE100.**
**If use Chinese, write the project Chinese rules.**

This rule applies to all text in this repository:

- Markdown documents
- Code comments and docstrings
- Commit messages and pull request descriptions
- Issue and review text

The repository documents are written in ASD-STE100 (Simplified Technical
English) or in the project Chinese controlled style. Keep the same standard in
all new text and in all edits. Write a document in one language. Do not mix
English and Chinese sentences in the same paragraph.

## English rules (ASD-STE100)

1. Use common technical words only. Give one word one meaning. Do not use
   ambiguous words such as "adequate", "sufficient", "various", "appropriate",
   "etc.", or "and/or".
2. Keep sentences short. A descriptive sentence has a maximum of 25 words. An
   instruction has a maximum of 20 words. Put one instruction in one sentence.
3. Use the active voice. Use the imperative for instructions (for example,
   "Run the test."). Use the present tense for descriptions.
4. Use "must" for a requirement. Do not use "shall". Use "can" for capability.
   Do not use "should".
5. Keep the article ("a", "an", "the") where the meaning needs it.
6. Do not use the "-ing" form of a verb as a noun. Write "to verify" and not
   "for verification". Write "before you benchmark" and not "before
   benchmarking". Keep "-ing" only in approved technical nouns such as
   "timing", "setting", "routing", "packing", and "warning".
7. Do not use contractions. Write "do not" and not "don't".
8. Keep paragraphs to a maximum of six sentences. Give one paragraph one
   topic.
9. Do not use more than three nouns in a row.
10. Use simple connectors only: "and", "but", "or", "because", "if", "when",
    "before", "after", "until", "although", and "then" for sequence. Split long
    sentences into short sentences.
11. Keep all numbers, units, dates, file paths, commands, flags, product
    names, and code exactly as they are. ASD-STE100 changes the language, not
    the data.
12. Keep every measured value, configuration, and sample count. Do not remove
    data when you rewrite a sentence. The limit rules are in "Limits and open
    items" below.

## Chinese rules

The Chinese rules come from the project writing standard. The source of truth
is `docs/WRITING.md` in the Project-Mozart repository. The standard references
GB/T 19678.1—2018 (instructions for use), GB/T 15834—2011 (punctuation), and
GB/T 1.1—2020 (structure of standardization documents). These standards serve
different purposes, and together they are not called a "Chinese STE".

1. Write one fact in one sentence. Put only one main action in an instruction
   sentence.
2. Write the condition, the action, and the observable result. Delete
   promotional wording and guarantees that have no evidence.
3. Use one consistent Chinese term for each component, action, and state.
   Explain an English term at its first use. Keep identifiers unchanged.
4. Separate 已实现, 已验证, 未实现, and 待验证. Note the configuration or the
   report for every measurement value.
5. 必须 marks a necessary condition. 建议 marks an optional practice. 可以 marks
   a known capability.
6. Use Chinese punctuation in Chinese prose. Commands, paths, and code keep
   their own symbols.
7. Leave a space between a number and its unit, for example 320 ms, 48 kHz,
   8 GB. Code and quoted text are exceptions.
8. Do not infer current whole-machine performance from an old isolated
   baseline. Limit a hardware capability conclusion to the tested platform and
   configuration.
9. Write the claim before the limit. Put the scope in one section at the end of
   the document. Write a limit that a measurement can remove as a task.
10. Do not repeat a limit in more than one document. Link to the document that
    owns the limit.

Quoted text keeps its original language. A quoted log line, a verbatim model
answer, and a literary quotation stay as they are.

## Limits and open items

Write the claim before the limit. Write each limit one time.
Put the scope in one section at the end of the document. List the configuration,
the sample count, and the open items.
Write a limit that a measurement can remove as a task. Do not close a resolvable
item with a limitation sentence.
Use "does not establish" only for a limit that you cannot remove. Then give the
blocker and the release condition.
Do not repeat a limit in more than one document. Link to the document that owns
the limit.

Example:

- Do not write: "Three samples do not establish a population confidence
  interval."
- Write: "The interval uses three samples. Task: measure 30 samples."

## Code checks and fallbacks

Check external input at the entry point one time. External input includes
command lines, files, environment variables, and remote responses.
Inner functions trust the checked values. An inner function does not check the
same value again.
Define a limit in one place. Other code reads that definition.
Do not keep a check that only a test can reach.
Fail with a clear error. Do not continue after an internal error.
Hash an artifact only when a requirement or a recorded failure needs the hash.
Do not seal and re-verify every intermediate result.
Do not write a limitation into a machine-readable artifact. Put the scope in the
report.
If the caller clamps a value, do not check that value again. Remove the check
or remove the clamp.
A check must fail when the error that it guards against occurs. Make that
error and run the check. If the check passes, delete the check or rewrite it.
Do not compare a result with the output of the same implementation. Compare it
with an independent reference.
Catch only the exceptions that the code can handle. Do not catch an internal
error, write it into a result field, and continue.

Example from this repository:

- `spacemit/bench/qemu-screen/predictor/freeze-sources.py:44-45` catches every
  `Exception`, writes it into the `error` field, and continues. Then the script
  writes `SHA256SUMS`. Write instead: catch the network error types only. Let
  other errors stop the script.

Run `python3 tools/writing_lint.py` before you deliver a change. It finds
limitation sentences and broad `except` handlers that do not raise again. The
baseline can only become smaller. Read the script docstring for the rules.

Before you commit, run `tools/ci-local.sh --staged`. The pre-commit hook runs
the same command. To install the hook, run `tools/install-hooks.sh` one time.
Do not use `--no-verify`. The lint step reads the staged content. If a checked
path has unstaged or untracked changes, the hook stops. Stage, restore, or move
those changes, and then commit. CI runs the stages of the same script. Define
each check command only in `tools/ci-local.sh`.

## Review

Review the computed result, not the check branches.
A test that only asserts a rejection does not cover the function. Test the
numbers.
Start a review pass in a fresh context. The author of a change does not approve
it.

After you change code, start a `reviewer` subagent on the diff before you
deliver. Give the subagent this list. Tell it to give the file and the line for
each item:

1. An inner function checks a value that the caller already checked or
   clamped.
2. A check or a branch that only a test can reach.
3. A limit, a constant, or a threshold that has more than one definition.
4. A broad `except`, or a caught error that the code records and then ignores.
5. A gate that is less strict, a self-comparison, or a failure that became a
   record field. For each check and each gate, make the error that it guards
   against. Tell if the check fails.
6. A limitation sentence in a document or a comment, or an open item without
   a blocker and a release condition.

The subagent reports problems only. It does not change files. Fix each item, or
write the reason to keep it in your reply. Do not deliver on the subagent
result alone. After the fixes, run the tests and `tools/writing_lint.py` again.

## One deliverable

This rule applies to all agents and all subagents.

Deliver one result for each task. Do not give the user candidates to choose
from. If you write more than one draft, merge the drafts into one result
before you deliver. Delete the other drafts or keep them out of the delivery.
If two options need a user decision, give one recommendation and the reason.
State the other option in one sentence.

## Records that are not documents

The files in `spacemit/reports/raw/` are machine-generated evidence: board
logs, benchmark summaries, and verbatim model answers. Do not rewrite them.
They are records, not documents. Their SHA-256 receipts stay valid only while
the text stays unchanged.
