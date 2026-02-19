#!/usr/bin/env python3
"""Clean up pandoc-generated LaTeX for arXiv submission."""
import re

with open('paper/draft_v1.tex', 'r') as f:
    content = f.read()

# Fix title - make it proper \title with subtitle on new line
content = content.replace(
    r'\author{}' + '\n' + r'\date{}',
    r'''\title{The Navigation Paradox in Large-Context Agentic Coding: \\
Graph-Structured Dependency Navigation Outperforms Retrieval in Architecture-Heavy Tasks}

\author{
    Tarakanath Paipuru \\
    Independent Researcher \\
    \texttt{Tarakanath.Paipuru@gmail.com}
}

\date{February 2026}'''
)

# Enable section numbering
content = content.replace(
    r'\setcounter{secnumdepth}{-\maxdimen} % remove section numbering',
    r'\setcounter{secnumdepth}{3} % enable section numbering'
)

# Add maketitle
content = content.replace(r'\begin{document}', r'\begin{document}' + '\n' + r'\maketitle')

# Fix abstract - convert subsection to environment
content = re.sub(r'\\subsection\{Abstract\}\\label\{abstract\}', r'\\begin{abstract}', content)

# Fix section headings
content = re.sub(r'\\subsection\{(\d+)\. ', r'\\section{', content)
content = re.sub(r'\\subsubsection\{(\d+)\.(\d+) ', r'\\subsection{', content)

with open('paper/draft_v1_arxiv.tex', 'w') as f:
    f.write(content)

print("✓ Created paper/draft_v1_arxiv.tex")
