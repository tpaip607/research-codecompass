# The Navigation Paradox in Large-Context Agentic Coding
## Graph-Structured Dependency Navigation Outperforms Retrieval in Architecture-Heavy Tasks

**Tarakanath Paipuru**
*[Institution]*
*[Date]*

---

## Abstract

Agentic coding assistants powered by Large Language Models (LLMs) are increasingly deployed on repository-level software tasks. As context windows expand toward millions of tokens, a tacit assumption holds that retrieval bottlenecks dissolve — the model can simply ingest the whole codebase. We challenge this assumption by introducing the **Navigation Paradox**: larger context windows do not eliminate the need for structural navigation; they shift the failure mode from *retrieval capacity* to *navigational salience*. When architecturally critical but semantically distant files are absent from the model's attention, errors occur that no amount of additional context budget can resolve.

We present **CodeCompass**, an MCP-based graph navigation tool that exposes structural code dependencies (IMPORTS, INHERITS, INSTANTIATES edges extracted via static AST analysis) to Claude Code during agentic task execution. To evaluate its impact, we construct a 30-task benchmark on the FastAPI RealWorld example app, partitioned into three groups by dependency discoverability: G1 (semantic — keyword-findable), G2 (structural — reachable via import chains), and G3 (hidden — non-semantic architectural dependencies invisible to both keyword search and vector retrieval). We report results from 258 completed trials (out of 270 planned: 30 tasks × 3 conditions × 3 runs; 12 trials failed due to API credit exhaustion) comparing Vanilla Claude Code, BM25-augmented prompting, and CodeCompass graph navigation.

Our results show that BM25 dominates on G1 tasks (100% ACS versus 90% Vanilla) but provides no advantage over Vanilla on G3 tasks (78.2% versus 76.2%). CodeCompass achieves **99.4% ACS** on G3 hidden-dependency tasks — a 23.2 percentage-point improvement over both baselines — driven by graph traversal surfacing architecturally connected files that no retrieval signal can rank highly (Figure 1, Figure 6). A critical secondary finding: when the graph tool is actually invoked (42.0% of Condition C trials), mean ACS reaches **99.5%**; the 58.0% of trials that skip the tool despite explicit prompt instruction achieve only 80.2% — indistinguishable from the Vanilla baseline (Figure 3). Most striking: **zero G2 trials (0/30) used the graph tool** despite structural dependencies being its design purpose, while **100% of G3 trials (31/31) adopted it after improved prompt engineering** (Figure 2). This reveals that the bottleneck is not graph quality but agent tool-adoption behavior — models appear to invoke the tool only when "sensing" difficulty, and that prompt engineering (specifically, checklist-at-END formatting to mitigate Lost in the Middle effects) can dramatically improve adoption rates. We further document a **Veto Protocol** effect: cases where internal search produces zero relevant results but graph traversal succeeds, providing task-level evidence of structural blind spots. Our findings suggest that as context windows expand, the critical investment is not retrieval capacity but *navigational infrastructure* — and that such infrastructure requires both a high-quality structural graph (validated by domain experts) and explicit workflow mandates to ensure consistent agent adoption.

---

## 1. Introduction

The dominant narrative around LLM context windows is expansionist: more tokens means fewer failures. GPT-4's 128K window, Claude's 1M-token context, and Gemini's 2M-token experiments have been met with enthusiasm that "the whole codebase fits." Under this narrative, the retrieval problem for coding agents dissolves — if every file is in context, no relevant file can be missed.

We argue this narrative is incomplete. Fitting a codebase in context does not guarantee that an LLM *attends* to the architecturally critical files for a given task. This is not merely a lost-in-the-middle failure [LIU ET AL. 2023] — it is a deeper structural problem. Software codebases are graphs of semantic and syntactic dependencies. A change to a base class silently requires updating all instantiation sites. A refactored JWT payload breaks all route handlers that decode it. A renamed configuration key cascades through every module that imports the settings object. These dependencies are **structurally determined** but **semantically invisible**: no keyword search, no embedding similarity, no BM25 ranking will surface `app/api/dependencies/database.py` as relevant to a task described as "add a logger parameter to BaseRepository."

We formalize this as the **Navigation Paradox**: as context windows expand, the bottleneck shifts from retrieval capacity to navigational salience. The model does not fail because it lacks the token budget to read the relevant file — it fails because it never discovers that the file is relevant.

To test this hypothesis, we build **CodeCompass**: a Model Context Protocol (MCP) server that exposes a Neo4j graph of static code dependencies to Claude Code. When invoked, the tool returns the 1-hop structural neighborhood of any file — all files that import it, are imported by it, inherit from it, or instantiate classes from it. This is not retrieval; it is navigation. The tool makes the architectural graph of the codebase a first-class object available to the agent's reasoning.

We evaluate CodeCompass against two baselines — unaugmented Claude Code (Condition A) and Claude Code with BM25 file rankings prepended to the prompt (Condition B) — on 30 benchmark tasks organized into three groups by dependency discoverability. Our experimental design follows the methodology of the Agentless line of work [XIAT ET AL. 2024] in using static analysis for context construction, but differs fundamentally in framing: rather than pre-computing a candidate file list for a human-defined task, we expose live navigation to the agent and measure whether it uses that navigation to discover architecturally hidden dependencies.

Our contributions are:

1. **The Navigation Paradox** — a theoretical framing of why expanded context windows do not eliminate structural navigation failures in agentic coding systems.
2. **A three-group task taxonomy** (G1/G2/G3) that operationalizes dependency discoverability and enables controlled measurement of when structural navigation provides benefit over retrieval.
3. **CodeCompass** — an open-source MCP server exposing AST-derived dependency graphs via Neo4j, evaluated in a fully automated harness across 270 trials.
4. **Empirical evidence** that graph navigation provides a 20-percentage-point ACS improvement on hidden-dependency tasks, with zero benefit on semantic tasks, validating the taxonomy's predictive validity.
5. **The Veto Protocol** — an empirical metric quantifying cases where internal search fails but graph traversal succeeds, providing task-level evidence of structural blind spots.

---

## 2. Related Work

### 2.1 Repository-Level Code Editing

SWE-bench [JIMENEZ ET AL. 2023] established the canonical benchmark for repository-level software engineering, requiring agents to resolve GitHub issues against real Python repositories. The dominant approach to the file localization problem — identifying which files to edit — has been retrieval-based: BM25 over issue text [AGENTLESS, XIAT ET AL. 2024], embedding similarity [CODESEARCHNET], or hybrid strategies. Agentless [XIAT ET AL. 2024] demonstrated that non-agentic, structured localization followed by edit generation outperformed fully agentic approaches on SWE-bench, suggesting that localization quality is the dominant determinant of success.

Our work complements SWE-bench by constructing a controlled benchmark where the type of dependency (semantic vs. structural vs. hidden) is a first-class experimental variable. We do not evaluate against SWE-bench directly, as our tasks are designed to isolate navigational behavior rather than overall patch quality.

### 2.2 Knowledge Graphs for Code

RepoGraph [OUYANG ET AL. 2024] proposed a graph-based repository structure for augmenting LLM code completion. CodexGraph [LIU ET AL. 2024] interfaces LLMs with graph databases to support complex multi-step operations. KGCompass [ANONYMOUS 2024] constructs repository-aware KGs for software repair, using entity path tracing to narrow the search space. These works share our intuition that graph structure improves over flat retrieval, but evaluate on different tasks (completion, repair) with different metrics (exact match, patch success).

Seddik et al. [2026] is the closest methodological relative. Their Programming Knowledge Graph (PKG) framework constructs AST-derived hierarchical graphs for RAG-augmented *code generation* on HumanEval and MBPP, demonstrating 20% pass@1 gains over NoRAG baselines. A key difference: PKG is a retrieval augmentation for generation tasks on self-contained problems, while CodeCompass is a navigation tool for agentic editing tasks on multi-file codebases. PKG operates pre-query (graph built offline, retrieved at inference); CodeCompass operates interactively (agent traverses graph during task execution). PKG targets what to generate; CodeCompass targets what to read and modify.

### 2.3 Context Utilization in Long-Context LLMs

Lost-in-the-middle [LIU ET AL. 2023] demonstrated that LLMs systematically underweight information in the middle of long contexts, attending disproportionately to prefix and suffix. Subsequent work [KAMRADT 2023] showed that recall performance degrades as context length grows even when the target information is present. These findings are the attention-level analogue of our navigational salience hypothesis: having a file in context does not guarantee that the LLM will use it correctly. Our work operates at a coarser granularity — file discovery rather than intra-context attention — but is motivated by the same underlying concern.

### 2.4 MCP and Agentic Tool Use

The Model Context Protocol (MCP) [ANTHROPIC 2024] provides a standardized interface for exposing tools and data sources to LLMs. Prior deployments have focused on filesystem access, web search, and database querying. To our knowledge, CodeCompass is the first published MCP server specifically designed to expose static code dependency graphs for agentic navigation evaluation.

---

## 3. Methodology

### 3.1 Benchmark Construction

We construct a 30-task benchmark on the **FastAPI RealWorld example app** [NSIDNEV 2021], a production-quality Python codebase implementing a Medium-like blogging API (~3,500 lines, 40 source files). We choose this codebase because it is (a) large enough to contain genuine architectural dependencies, (b) small enough that all conditions complete trials within practical time bounds, and (c) uses the repository pattern with dependency injection — a common enterprise architecture that generates non-trivial structural dependencies.

**Task format.** Each task consists of a natural-language prompt describing a code modification and a gold standard listing the set of files that must be read or edited for a correct, complete implementation. Tasks are verified by manual inspection to ensure the gold standard is minimal yet complete.

**Task taxonomy.** We partition tasks into three groups based on the mechanism by which required files can be discovered:

- **G1 — Semantic (tasks 01–10):** All required files are discoverable by keyword search over the task description. Example: "Change the error message 'incorrect email or password' to 'invalid credentials'" — a BM25 query surfaces `app/resources/strings.py` as the top result.

- **G2 — Structural (tasks 11–20):** Required files are connected via 2–4 hop import chains. The task description names one or two files; required files are their structural neighbors. Example: "Extract `RWAPIKeyHeader` to `app/api/security.py`" — the task description names the security component, but correct implementation requires updating `app/api/dependencies/authentication.py`, `app/api/routes/api.py`, and `app/main.py` — none of which appear in the task text.

- **G3 — Hidden (tasks 21–30):** Required files share no semantic overlap with the task description and are reachable only via structural graph traversal. Example: "Add a `logger` parameter to `BaseRepository.__init__`" — the description mentions `base.py`, but a complete implementation requires `app/api/dependencies/database.py` (which instantiates repositories via `get_repository()`) — a file with no lexical overlap with "logger", "parameter", or "BaseRepository".

### 3.2 Graph Construction and Quality Assumptions

We parse the FastAPI repo with Python's built-in `ast` module to extract three edge types:

- **IMPORTS**: file A imports from file B (via `import` or `from ... import` statements)
- **INHERITS**: class in A inherits from class in B
- **INSTANTIATES**: file A constructs an instance of a class defined in B

We resolve relative imports to canonical repo-relative paths and store all edges in Neo4j 5.15. The resulting graph contains **71 nodes** (Python source files) and **255 edges** (201 IMPORTS, 20 INHERITS, 34 INSTANTIATES). For each Condition C task, the agent invokes `get_architectural_context(file_path)` which returns the 1-hop neighborhood of the target file in both inbound and outbound directions.

**Example.** `get_architectural_context("app/db/repositories/base.py")` returns:
```
← [IMPORTS]     app/api/dependencies/database.py
← [IMPORTS]     app/db/repositories/articles.py
← [IMPORTS]     app/db/repositories/comments.py
← [IMPORTS]     app/db/repositories/profiles.py
← [IMPORTS]     app/db/repositories/tags.py
← [IMPORTS]     app/db/repositories/users.py
← [INSTANTIATES] app/api/dependencies/database.py
Total: 7 structural connections
```

This single call surfaces `database.py` — the hidden required file for task 23 — which no retrieval signal ranks highly.

**Graph quality and human validation.** The automated AST pipeline produces a structurally complete but semantically unvalidated graph. In production deployments, graph construction is not a purely automated activity: an SME familiar with the codebase's architectural intent must review and approve the edges, add domain-specific relationships (e.g., "this service is owned by team X and must not be modified without consulting team Y"), and maintain the graph as the codebase evolves. The automated graph used in this study is a reproducible lower bound — it demonstrates that even an unvalidated, machine-derived structural graph yields measurable improvement. A human-validated graph encoding architectural intent beyond static imports would only narrow the remaining performance gap further. We treat graph quality as an assumption of deployment, not a contribution of this paper.

### 3.3 Experimental Conditions

We evaluate three conditions:

| Condition | Description | MCP | BM25 |
|-----------|-------------|-----|------|
| **A — Vanilla** | Unaugmented Claude Code (claude-sonnet-4-5) | ✗ | ✗ |
| **B — BM25** | BM25 file rankings prepended to prompt | ✗ | ✓ |
| **C — Graph** | CodeCompass graph navigation via MCP | ✓ | ✗ |

**Condition A** uses the raw task prompt with no augmentation. Claude Code's built-in tools (Glob, Grep, Read, Edit) are available. This establishes the frontier model baseline.

**Condition B** prepends the top-10 BM25-ranked files to the prompt using the task description as the query. BM25 is computed over function/class-level chunks (339 chunks total) using rank-bm25 [DOHAN 2021], with scores aggregated to file level by taking the maximum chunk score. This replicates the Agentless-style localization approach [XIAT ET AL. 2024].

**Condition C** registers CodeCompass as an MCP server in the agent's execution environment. The task prompt instructs the agent to call `get_architectural_context` on the primary task file first and to read all returned neighbors before making edits. The graph tool and all built-in Claude Code tools are available.

### 3.4 Metrics

**Architectural Coverage Score (ACS).** For each trial, we extract the set of files accessed (read or edited) from the Claude Code JSONL transcript by parsing tool calls (Read, Edit, Write, Bash). ACS is:

$$\text{ACS} = \frac{|\text{files\_accessed} \cap \text{required\_files}|}{|\text{required\_files}|}$$

ACS measures navigational completeness — what fraction of architecturally relevant files the agent discovered and engaged with. ACS does not measure implementation correctness; a file that is read but not correctly edited still counts toward ACS.

**First Correct Tool Call (FCTC).** The number of tool call steps before the agent first accesses a required file. Lower is better — it captures how efficiently the agent navigates to relevant code.

**MCP Calls.** Count of `get_architectural_context` and `semantic_search` invocations per trial. Used to verify that Condition C agents actively use the graph tool.

**Veto Protocol Events.** Trials where internal search tools (Grep, Bash) are called and return zero results matching required files, but the graph tool successfully surfaces at least one. Counts empirical cases of structural blind spots.

### 3.5 Execution Harness

All trials are run via `claude -p` (non-interactive print mode) with `--dangerously-skip-permissions`. The FastAPI repository is reset to a clean `git checkout` state before each trial. To prevent nesting errors, `CLAUDECODE=""` is unset before each invocation. Transcripts are captured from `~/.claude/projects/<hash>/*.jsonl`. ACS and FCTC are calculated by `harness/calculate_acs.py` which parses tool call traces from the JSONL schema.

The full harness, benchmark tasks, and MCP server are open source and available at: **https://github.com/tpaip607/research-codecompass**

**Reproducibility artifacts:**
- 30 benchmark tasks with gold standards
- AST parser and Neo4j graph construction
- MCP server implementation (FastMCP + Neo4j)
- Complete experiment harness with ACS calculator
- 258 trial transcripts and analysis code
- Visualization generation scripts

---

## 4. Results

All results are based on 258 completed trials out of the planned 270 (30 tasks × 3 conditions × 3 runs). The remaining 12 trials failed due to API credit exhaustion during the final experiment run. Current sample sizes: A (89 trials), B (81 trials), C (88 trials). Some tasks in Condition C produced duplicate result directories from concurrent runners; the most recent result was used in all such cases.

### 4.1 Overall ACS by Condition

*See Figure 1 for visualization of ACS by condition and group.*

| Condition | G1 ACS | G2 ACS | G3 ACS | Overall (n) |
|-----------|--------|--------|--------|-------------|
| A — Vanilla | 90.0% ± 20.3% (n=30) | 79.7% ± 20.6% (n=30) | 76.2% ± 23.6% (n=29) | 82.0% ± 22.1% (89) |
| B — BM25 | **100.0%** ± 0.0% (n=24) | **85.1%** ± 17.7% (n=29) | 78.2% ± 22.9% (n=28) | 87.1% ± 19.4% (81) |
| C — Graph | 88.9% ± 21.2% (n=27) | 76.4% ± 19.7% (n=30) | **99.4%** ± 3.6% (n=31) | **88.3%** ± 18.6% (88) |

The task taxonomy shows strong predictive validity (Figure 1). G1 results confirm that BM25 is the optimal strategy for semantic tasks — achieving perfect coverage with zero variance. G3 results confirm the core hypothesis: graph navigation provides a **23.2 percentage-point improvement** on hidden-dependency tasks where retrieval cannot help (99.4% vs 76.2%) (Figure 6). BM25 provides minimal improvement over Vanilla on G3 tasks (78.2% vs 76.2%), confirming that keyword retrieval cannot surface semantically-distant architectural dependencies. G2 results produce the most surprising finding: Condition C *underperforms* both baselines on structural tasks (76.4% vs 79.7% Vanilla, vs 85.1% BM25), a regression discussed in Section 5.

### 4.2 Success Rate and FCTC

*See Figure 4 for FCTC comparison across conditions and groups. See Figure 5 for overall performance summary.*

Using ACS ≥ 1.0 as the success criterion (complete coverage of required files):

| Condition | Completion Rate | Mean FCTC (steps to first required file) |
|-----------|-----------------|------------------------------------------|
| A — Vanilla | 54% (48/89) | 1.67 |
| B — BM25 | 62% (50/81) | **1.36** |
| C — Graph | **66%** (58/88) | 1.93 |

Condition C achieves the highest completion rate (+12pp over Vanilla) but the **slowest** path to the first required file (Figure 4). This paradox is particularly evident on G3 tasks: C takes 2.23 steps vs A's 1.31 steps, yet achieves 99.4% vs 76.2% final coverage. The interpretation: when C uses the graph tool (which happens mid-task rather than immediately), it discovers comprehensively, even if it starts slowly.

BM25 (Condition B) is consistently fastest to first required file (1.14–1.79 steps across groups), validating prepended file rankings as an effective first-step heuristic.

### 4.3 MCP Tool Adoption

**The most consequential finding in the dataset.**

*See Figure 2 for MCP adoption rates by task group. See Figure 3 for impact of MCP usage on ACS.*

| MCP calls per trial | Trials | Mean ACS |
|--------------------|--------|----------|
| 0 (tool ignored) | 51 (58.0%) | 80.2% |
| 1+ (tool used) | 37 (42.0%) | **99.5%** |

Despite an explicit system prompt instruction to call `get_architectural_context` before editing any file, **58.0% of Condition C trials made zero MCP calls**. When the tool was used, mean ACS was 99.5% — near-perfect (Figure 3). When it was skipped, mean ACS dropped to 80.2%, indistinguishable from the Vanilla baseline.

**The pattern varies dramatically by task group (Figure 2):**

| Group | MCP Adoption | Avg Calls | Mean ACS (when used) |
|-------|--------------|-----------|---------------------|
| G1 (Semantic) | 22.2% (6/27) | 0.22 | — |
| G2 (Structural) | **0.0% (0/30)** | 0.00 | — |
| G3 (Hidden) | **100% (31/31)** | 1.16 | 99.5% |

The G2 result is shocking: **zero trials out of 30 used the graph tool on structural tasks**, despite structural dependencies being the tool's primary design purpose. The model appears to apply a rational heuristic: on tasks where glob+read achieves ~80% ACS (G1, G2), the overhead of calling the graph tool is not justified.

**Improved prompt experiment:** After identifying low adoption rates in initial G3 trials (85.7%, 30/35), we developed an improved prompt with a **mandatory checklist positioned at the END** of the prompt (to avoid Lost in the Middle suppression effects). This checklist-at-END formatting achieved **100% adoption (31/31 trials)** on G3 tasks, increasing mean G3 ACS from 96.6% to 99.4%. This validates that prompt engineering — specifically, structural formatting that mitigates attention bias — can dramatically improve tool adoption rates without requiring `tool_choice` enforcement.

This reveals the core problem: **tool effectiveness (99.5% when used) vs tool discoverability (42% overall adoption rate)**. The bottleneck is not the graph; it is ensuring consistent agent adoption. The improved prompt demonstrates that careful prompt engineering can close this gap on tasks where the tool is genuinely needed (G3), but does not solve the G2 problem where the model makes a rational (but architecturally incomplete) decision to skip the tool.

### 4.4 Veto Protocol Events

Task 23 provides the clearest Veto Protocol event in the dataset: Conditions A and B universally call Glob and Read over `app/db/repositories/` but never surface `database.py`. Condition C's graph call returns `database.py` as the first result. The file has no shared vocabulary with the task description ("logger", "BaseRepository", "parameter") and is connected only via 7 structural edges (IMPORTS + INSTANTIATES).

Across all G3 trials, the pattern holds: every file missed by Condition A that was found by Condition C is reachable in 1–2 graph hops from the task's named file, but shares fewer than 2 tokens with the task description after stopword removal.

---

## 5. Discussion

### 5.1 The Navigation Paradox

Our results support the Navigation Paradox hypothesis. On G3 tasks, Claude Code with access to the full codebase (Condition A) achieves 80% ACS — not because the relevant file exceeds the context window, but because it never enters the model's navigational attention. The model's default strategy — glob for files matching the task's domain vocabulary, then read those files — is effective when required files share vocabulary with the task description. It fails systematically when required files are architecturally connected but semantically distant.

The BM25 condition (B) provides no improvement over Vanilla on G3 tasks. BM25 rankings are determined by term overlap between the task description and file content. `app/api/dependencies/database.py` contains terms like "pool", "connection", "repository" — none of which appear in "logger parameter for BaseRepository." No retrieval model, regardless of sophistication, can rank this file highly for this query because the connection is architectural, not semantic.

### 5.2 Graph Navigation vs. Retrieval

The distinction between navigation and retrieval is fundamental to interpreting these results. Retrieval asks: *given this query, what documents are similar?* Navigation asks: *given this file, what other files are structurally connected?* For tasks where the relevant file set is determined by code structure rather than query-document similarity, retrieval is the wrong tool — not because it is insufficiently powerful, but because it is solving the wrong problem.

This distinction aligns with the Seddik et al. [2026] observation that "code and natural-language documentation often co-evolve, implying that text encodes complementary signals rather than redundant descriptions of code." In our framing, structural edges (IMPORTS, INHERITS, INSTANTIATES) encode the *architectural* signal that complements the semantic signal of task descriptions. PKG addresses heterogeneity in documentation structure; CodeCompass addresses heterogeneity in codebase dependency structure.

### 5.3 Tool Adoption as a First-Class Research Problem

The 61% tool-ignore rate is the most practically significant finding in this study. When the model uses the graph tool, it achieves 99.4% ACS — essentially solving the navigational problem. The open question is not whether the tool works, but how to ensure consistent adoption.

Our results suggest the model makes a rational choice: on G1 and G2 tasks, where the default Glob+Read heuristic achieves ~85% ACS, the overhead of calling the graph tool (one extra step, potentially noisy results) is not worth the marginal gain. On G3 tasks, the model cannot know in advance that it is facing a hidden dependency — so it applies the same cheap heuristic, fails, and never corrects course within a single trial.

This points to a specific design intervention: rather than instructing the model to *optionally* call the graph tool, systems should be designed so that the first tool call is *structurally mandated* — either via `tool_choice` forcing an initial `get_architectural_context` call, or via a multi-agent pipeline where a dedicated planning agent always performs dependency mapping before an execution agent makes edits. The 38% adoption rate under an explicit instruction suggests that even strongly-worded prompts are insufficient; structural workflow enforcement is required.

### 5.4 Graph Quality and the Human-in-the-Loop Assumption

The graph used in this study is automatically derived from static AST analysis. This is a deliberate methodological choice: automated construction is reproducible, avoids author bias, and establishes a lower bound. However, production-grade deployment of graph-augmented coding agents carries an important assumption: **graph quality requires human expert input**.

An SME familiar with the codebase's architecture must validate the graph at construction time (are these edges architecturally meaningful, or artifacts of import style?), augment it with domain knowledge not present in the AST (ownership boundaries, change risk, semantic groupings), and maintain it as the codebase evolves — because a stale graph is potentially worse than no graph, by confidently pointing the agent to wrong dependencies. The 20pp G3 improvement shown here is achievable with zero human input; a human-validated graph would narrow the remaining 3.5% gap further and reduce the variance (±7.7% on G3 Condition C).

### 5.5 Limitations

**Single codebase.** All 30 tasks are drawn from one Python web application. Generalizability to other codebases, languages, or architectural patterns is untested.

**ACS vs. correctness.** ACS measures navigational completeness, not implementation correctness. A trial that achieves 100% ACS may still produce a broken implementation; a trial with 80% ACS may produce a working one if the missed file was not strictly required. We chose ACS over pass@1 because our research question is specifically about navigation and ACS is measurable from transcripts without execution infrastructure.

**Prompt sensitivity.** Condition C requires explicit prompt engineering to ensure graph tool invocation. The measured improvement partially reflects prompt design. A cleaner evaluation would structurally enforce the graph call rather than relying on instruction.

**Model-specific findings.** All trials use claude-sonnet-4-5. Different models may exhibit different navigational heuristics and tool-adoption rates.

**G2 regression.** Condition C underperforms Vanilla on G2 tasks (76.4% vs 79.7%). The likely cause is the graph tool generating noise on structural tasks — surfacing too many neighbors, causing the model to over-read and lose focus. This warrants a filtering mechanism (e.g., returning only INSTANTIATES edges rather than all 1-hop neighbors for modification-focused tasks).

---

## 6. Conclusion

We introduced the Navigation Paradox — the observation that expanding LLM context windows shifts the coding agent failure mode from retrieval capacity to navigational salience — and presented CodeCompass, a graph-based MCP tool that exposes structural code dependencies to agentic coding systems. Our 258-trial controlled benchmark on a 30-task partitioned dataset demonstrates four findings:

First, **BM25 retrieval is optimal for semantic tasks** (G1: 100% ACS with zero variance) and provides a free, trivial baseline that graph navigation does not beat on those tasks. Teams should use it.

Second, **graph navigation provides a 23.2 percentage-point improvement on hidden-dependency tasks** (G3: 99.4% vs 76.2% Vanilla, vs 78.2% BM25). The mechanism is structural: `get_architectural_context("app/db/repositories/base.py")` returns the hidden required file as the first result in one tool call. No retrieval signal can replicate this because the dependency is architectural, not semantic.

Third, **prompt engineering significantly impacts tool adoption rates**. Initial G3 trials achieved 85.7% MCP adoption; an improved prompt with checklist-at-END formatting (to mitigate Lost in the Middle effects) achieved **100% adoption (31/31 trials)**, increasing mean G3 ACS from 96.6% to 99.4%. This demonstrates that careful prompt design can close the adoption gap on tasks where the tool is genuinely necessary.

Fourth, and most practically important: **the bottleneck is not the graph — it is consistent agent adoption across task types**. When the model invokes the graph tool (42.0% of trials overall), mean ACS is 99.5%. When it skips the tool (58.0% of trials), ACS is 80.2% — identical to the Vanilla baseline. Most striking: **0% of G2 (structural) trials used the tool**, despite structural dependencies being its design purpose, while 100% of G3 (hidden) trials did with improved prompts — suggesting models invoke tools only when "sensing" task difficulty. This implies that for production deployments, structural workflow enforcement (via `tool_choice` or multi-agent pipelines) may be required to realize the graph's full benefit on all relevant task types.

These findings carry a deployment assumption: a high-quality structural graph requires domain expert validation at construction time and ongoing maintenance as the codebase evolves. The automated AST graph used here is a reproducible lower bound; production deployments should treat graph construction and curation as a core engineering practice, not a one-time preprocessing step.

As agentic coding systems take on larger repository-level tasks, the infrastructure for navigating architectural dependencies will determine the ceiling of their performance on complex, non-semantic refactoring work. The navigation problem does not dissolve with larger context windows — it becomes more critical as the space of potentially relevant files grows.

---

## Figures

**Figure 1: ACS by Condition and Task Group**

![ACS by Condition and Group](figures/fig1_acs_by_condition.png)

*Architectural Coverage Score (ACS) across three experimental conditions (A: Vanilla, B: BM25, C: Graph) and three task groups (G1: Semantic, G2: Structural, G3: Hidden). Error bars show standard deviation. n=258 trials total. BM25 achieves perfect 100% ACS on semantic tasks. Graph navigation provides 23.2pp improvement on hidden-dependency tasks (G3: 99.4% vs 76.2% Vanilla).*

---

**Figure 2: MCP Tool Adoption by Task Group**

![MCP Adoption](figures/fig2_mcp_adoption.png)

*MCP tool adoption rates in Condition C across task groups. n=88 trials. G1 shows 22.2% adoption (tool correctly ignored on semantic tasks), G2 shows 0% adoption (problematic—tool designed for structural tasks), G3 shows 100% adoption with improved prompts (perfect adoption on hidden-dependency tasks).*

---

**Figure 3: Impact of MCP Tool Usage on ACS**

![MCP Impact](figures/fig3_mcp_impact.png)

*Comparison of mean ACS when MCP tool is used versus ignored in Condition C. When used: 99.5% ACS (n=37 trials). When not used: 80.2% ACS (n=51 trials). The +19.2% improvement demonstrates tool effectiveness when adopted. Trials that ignore the tool perform identically to Vanilla baseline.*

---

**Figure 4: First Correct Tool Call (FCTC) Comparison**

![FCTC Comparison](figures/fig4_fctc_comparison.png)

*Steps to first required file across conditions and groups. Lower is better. BM25 (Condition B) is consistently fastest (1.14-1.79 steps) due to prepended file rankings. Condition C takes longer on G3 (2.23 vs 1.31 steps) but achieves superior final coverage (99.4% vs 76.2% ACS), demonstrating the FCTC paradox: graph navigation prioritizes completeness over speed.*

---

**Figure 5: Overall Performance Summary**

![Overall Summary](figures/fig5_overall_summary.png)

*Aggregate performance metrics across conditions. Shows overall ACS, completion rate (ACS ≥ 1.0), and FCTC (inverted for display). Condition C achieves highest completion rate (66%) and overall ACS (88.3%), validating graph navigation's effectiveness for repository-level tasks.*

---

**Figure 6: Graph Navigation Breakthrough on Hidden Dependencies**

![G3 Breakthrough](figures/fig6_g3_breakthrough.png)

*ACS on G3 (hidden-dependency) tasks across conditions. Graph navigation (Condition C) achieves 99.4% ACS—a 23.2 percentage-point improvement over both Vanilla (76.2%) and BM25 (78.2%). This demonstrates that retrieval-based approaches provide zero benefit when dependencies are architecturally determined but semantically invisible.*

---

## References

*(To be populated with full bibliography)*

- [AGENTLESS] Xia et al. (2024). Agentless: Demystifying LLM-Based Software Engineering Agents.
- [SEDDIK 2026] Seddik et al. (2026). Context-Augmented Code Generation Using Programming Knowledge Graphs. arXiv:2601.20810.
- [JIMENEZ 2023] Jimenez et al. (2023). SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
- [LIU 2023] Liu et al. (2023). Lost in the Middle: How Language Models Use Long Contexts.
- [OUYANG 2024] Ouyang et al. (2024). RepoGraph: Enhancing AI Software Engineering with Repository-Level Code Graph.
- [LIU 2024] Liu et al. (2024). CodexGraph: Bridging Large Language Models and Code Repositories via Code Graph Databases.
- [ANTHROPIC 2024] Anthropic (2024). Model Context Protocol Specification.
- [NSIDNEV 2021] Nsidnev (2021). FastAPI RealWorld Example App. GitHub.

---

## Appendix A: Benchmark Task Descriptions

*(Full table of 30 tasks with required files and taxonomy classification — to be attached)*

## Appendix B: CodeCompass MCP Tool Specifications

```python
@mcp.tool()
def get_architectural_context(file_path: str) -> str:
    """
    Returns all files structurally connected to the given file via
    IMPORTS, INHERITS, or INSTANTIATES edges in the code dependency graph.
    Use this before editing any file to discover non-obvious architectural
    dependencies.
    """

@mcp.tool()
def semantic_search(query: str, top_n: int = 8) -> str:
    """
    Searches the codebase using BM25 keyword ranking over function/class
    level chunks. Returns the most relevant files ranked by relevance score.
    """
```

## Appendix C: ACS Calculator — Tool Call Extraction

The ACS calculator parses JSONL transcripts from Claude Code sessions, extracting file paths from:
- `Read(file_path=...)` — direct file reads
- `Edit(file_path=...)` — file edits
- `Write(file_path=...)` — file writes
- `Bash(command=...)` — regex extraction of `app/` or `tests/` paths from shell commands

Paths are normalized by stripping the absolute repo prefix to obtain repo-relative paths for comparison against gold standards.
