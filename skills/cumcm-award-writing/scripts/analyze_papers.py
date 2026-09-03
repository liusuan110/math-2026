#!/usr/bin/env python3
"""Extract descriptive writing-style signals from Chinese CUMCM papers.

The output is evidence for human review, not a quality score or an AI detector.
PDF, LaTeX, Markdown, and plain-text inputs are supported.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

PHRASES = (
    "本文", "针对", "首先", "其次", "最后", "综上所述", "进一步", "因此",
    "结果表明", "由图", "由表", "可见", "说明", "验证", "检验", "敏感性",
    "误差", "相较于", "提高", "降低", "我们", "不妨", "值得注意",
    "准确性和有效性", "具有一定", "提供理论依据", "多个维度", "机器精度",
)

SECTION_WORDS = (
    "摘要", "问题重述", "问题分析", "模型假设", "符号说明", "模型建立",
    "模型求解", "结果分析", "模型检验", "灵敏度分析", "误差分析", "模型评价",
    "结论", "参考文献", "附录",
)


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path: Path) -> tuple[str, int, list[int]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit("PDF analysis requires pypdf: install it or analyze a LaTeX/text source instead.") from exc
    reader = PdfReader(str(path))
    page_texts = [clean_text(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(page_texts), len(reader.pages), [len(t) for t in page_texts]


def extract_text_source(path: Path) -> tuple[str, int, list[int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".tex":
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        if "\\begin{document}" in text:
            text = text.split("\\begin{document}", 1)[1]
        text = text.split("\\begin{appendices}", 1)[0]
        for env in ("equation", "align", "align*", "gather", "lstlisting", "lstinputlisting"):
            text = re.sub(
                rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
                " ", text, flags=re.S,
            )
        text = re.sub(r"\$.*?\$", " ", text, flags=re.S)
        text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.S)
        text = re.sub(r"\\(?:section|subsection|subsubsection|caption)\*?\{([^{}]*)\}", r"\n\n\1\n\n", text)
        text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
        for _ in range(3):
            text = re.sub(r"\{([^{}]*)\}", r"\1", text)
        text = text.replace("~", " ").replace("\\", " ")
    text = clean_text(text)
    return text, 1, [len(text)]


def extract(path: Path) -> tuple[str, int, list[int]]:
    if path.suffix.lower() == ".pdf":
        return extract_pdf(path)
    if path.suffix.lower() in {".tex", ".md", ".txt"}:
        return extract_text_source(path)
    raise ValueError(f"Unsupported input type: {path.suffix}")


def chinese_char_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def sentence_lengths(text: str) -> list[int]:
    sentences = re.split(r"[。！？!?；;]+", text)
    return [chinese_char_count(s) for s in sentences if chinese_char_count(s) >= 4]


def paragraph_lengths(text: str) -> list[int]:
    paragraphs = re.split(r"\n\s*\n", text)
    return [chinese_char_count(p) for p in paragraphs if chinese_char_count(p) >= 12]


def per_10k(count: int, chars: int) -> float:
    return round(count * 10000 / chars, 2) if chars else 0.0


def analyze(path: Path) -> dict:
    text, pages, page_chars = extract(path)
    chars = chinese_char_count(text)
    sentences = sentence_lengths(text)
    paragraphs = paragraph_lengths(text)
    phrase_counts = Counter({phrase: text.count(phrase) for phrase in PHRASES})
    return {
        "file": str(path.resolve()),
        "pages": pages,
        "extracted_chinese_chars": chars,
        "nonempty_pages": sum(n > 30 for n in page_chars),
        "mean_sentence_chars": round(sum(sentences) / len(sentences), 2) if sentences else 0,
        "median_sentence_chars": sorted(sentences)[len(sentences) // 2] if sentences else 0,
        "mean_paragraph_chars": round(sum(paragraphs) / len(paragraphs), 2) if paragraphs else 0,
        "phrase_counts": dict(phrase_counts),
        "phrase_per_10k": {k: per_10k(v, chars) for k, v in phrase_counts.items()},
        "section_mentions": {word: text.count(word) for word in SECTION_WORDS},
        "warning": (
            "Low text extraction coverage; inspect rendered pages or source files."
            if pages and sum(n > 30 for n in page_chars) / pages < 0.6
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("papers", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    missing = [str(p) for p in args.papers if not p.is_file()]
    if missing:
        raise SystemExit("Missing PDF(s): " + ", ".join(missing))

    result = {"papers": [analyze(path) for path in args.papers]}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
