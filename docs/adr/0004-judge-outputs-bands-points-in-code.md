# The Judge outputs Bands with Evidence, and code computes the points

The official Grid is ordinal: four Bands per Criterion. So the Judge makes one structured call per Criterion and returns `{band, evidence[], missing[]}`. Each Evidence quote must be an exact substring of the Transcript, and code checks this.

Each Criterion is judged n times (n = 3 in production) to get a Band Distribution, in the style of G-Eval, because the Claude API doesn't return token logprobs. The Report shows the Modal Band, and the spread is used as an uncertainty signal.

Band Points and the Estimated Score are always summed in code from the Exam Definition, never by the LLM. A free 0–25 score was rejected because it doesn't match the official form and makes agreement metrics meaningless.
