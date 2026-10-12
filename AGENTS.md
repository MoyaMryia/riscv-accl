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
12. Keep every warning, limit, and measured claim. Do not remove a caveat when
    you rewrite a sentence.

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

Quoted text keeps its original language. A quoted log line, a verbatim model
answer, and a literary quotation stay as they are.

## Records that are not documents

The files in `spacemit/reports/raw/` are machine-generated evidence: board
logs, benchmark summaries, and verbatim model answers. Do not rewrite them.
They are records, not documents. Their SHA-256 receipts stay valid only while
the text stays unchanged.
