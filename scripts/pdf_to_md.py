#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 转 Markdown 脚本

特性：
- 基于 PyMuPDF（pymupdf）提取文本与字体大小，采用简单启发式生成 Markdown
- 支持单文件或目录批量转换（可递归）
- 支持指定输出目录、覆盖策略

用法示例：
  单文件：
    python scripts/pdf_to_md.py /path/to/file.pdf
    python scripts/pdf_to_md.py /path/to/file.pdf -o /path/to/output

  批量（目录）：
    python scripts/pdf_to_md.py /path/to/dir_with_pdfs -r -o ./converted

依赖：
  pip install pymupdf

注意：
- PDF 转 Markdown 的质量取决于原始 PDF 的结构与嵌入信息。本脚本采用启发式方法，
  通过比较字体大小粗略生成「# / ##」标题，其余作为段落文本。
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except Exception as e:
    print("错误：未安装依赖 pymupdf。请先安装：")
    print("  pip install pymupdf")
    raise


@dataclass
class MergeConfig:
    same_column_tolerance: float = 12.0  # 同列 x 中心容差（pt）
    vertical_gap_limit: float = 60.0     # 相邻行允许最大垂直间距（pt）的基础值
    vertical_gap_factor: float = 3.0     # 允许垂直间距 = max(vertical_gap_limit, factor * 平均行高)
    min_vertical_run: int = 3            # 触发竖排合并的最小连续行数


def extract_page_markdown(page: "fitz.Page", cfg: MergeConfig) -> str:
    """
    从单页提取 Markdown 文本。
    改进点：
    - 使用 page.get_text('words') 横向拼接同一行，避免中文竖排（每字一行）问题
    - 基于行高（y1-y0）的分布估算标题阈值
    - 使用 page.find_tables() 识别表格并输出为 Markdown 表格
    - 依据元素的 y 坐标将文本行与表格按阅读顺序合并
    """
    # 1) 提取词并组行为文本块（含 bbox）
    words = page.get_text("words")  # (x0, y0, x1, y1, "w", block_no, line_no, word_no)
    lines_map: dict[tuple[int, int], list[tuple[float, float, float, float, str]]] = {}
    for x0, y0, x1, y1, w, bno, lno, wno in words:
        key = (int(bno), int(lno))
        lines_map.setdefault(key, []).append((x0, y0, x1, y1, w))

    # line: (y_center, x_center, x0, y0, x1, y1, text, line_height)
    raw_lines: list[tuple[float, float, float, float, float, float, str, float]] = []
    for (bno, lno), items in lines_map.items():
        items.sort(key=lambda t: t[0])  # 按 x0 升序
        text = "".join([it[4] for it in items]).strip()
        if not text:
            continue
        x0 = min(it[0] for it in items)
        y0 = min(it[1] for it in items)
        x1 = max(it[2] for it in items)
        y1 = max(it[3] for it in items)
        y_center = (y0 + y1) / 2.0
        x_center = (x0 + x1) / 2.0
        heights = [abs(it[3] - it[1]) for it in items]
        line_height = sum(heights) / len(heights) if heights else 0.0
        raw_lines.append((y_center, x_center, x0, y0, x1, y1, text, line_height))

    # 1.1) 竖排文本合并：同列且短文本（<=2）的相邻行按 y 合并
    raw_lines.sort(key=lambda t: (t[0], t[1]))
    merged_lines: list[tuple[float, float, float, float, float, float, str, float]] = []
    group: list[tuple[float, float, float, float, float, float, str, float]] = []
    def flush_group():
        nonlocal group, merged_lines
        if not group:
            return
        all_short = all(len(g[6]) <= 2 for g in group)
        if len(group) >= cfg.min_vertical_run and all_short:
            xs = [g[1] for g in group]
            if (max(xs) - min(xs)) <= cfg.same_column_tolerance:
                group_sorted = sorted(group, key=lambda t: t[0])
                text = "".join(g[6] for g in group_sorted)
                x0 = min(g[2] for g in group_sorted)
                y0 = min(g[3] for g in group_sorted)
                x1 = max(g[4] for g in group_sorted)
                y1 = max(g[5] for g in group_sorted)
                y_center = (y0 + y1) / 2.0
                x_center = (x0 + x1) / 2.0
                h = sum(g[7] for g in group_sorted) / len(group_sorted)
                merged_lines.append((y_center, x_center, x0, y0, x1, y1, text, h))
                group = []
                return
        merged_lines.extend(group)
        group = []
    for ln in raw_lines:
        if not group:
            group = [ln]
        else:
            avg_h = (group[-1][7] + ln[7]) / 2.0
            same_col = abs(ln[1] - group[-1][1]) <= cfg.same_column_tolerance
            near_vert = abs(ln[0] - group[-1][0]) <= max(cfg.vertical_gap_limit, cfg.vertical_gap_factor * max(1.0, avg_h))
            if same_col and near_vert:
                group.append(ln)
            else:
                flush_group()
                group = [ln]
    flush_group()
    line_items = merged_lines

    # 2) 表格识别
    table_items: List[Tuple[float, str, tuple[float, float, float, float]]] = []
    try:
        tables = page.find_tables()
        for tb in tables:
            y_top = float(tb.bbox[1])
            data = tb.extract()
            if not data:
                continue
            header = data[0]
            rows = data[1:] if len(data) > 1 else []
            def to_row(cells: List[str]) -> str:
                return "| " + " | ".join((c or "").replace("\n", " ").strip() for c in cells) + " |"
            md_lines = []
            md_lines.append(to_row(header))
            md_lines.append("| " + " | ".join("---" for _ in header) + " |")
            for r in rows:
                if len(r) < len(header):
                    r = r + [""] * (len(header) - len(r))
                md_lines.append(to_row(r))
            table_md = "\n".join(md_lines) + "\n\n"
            table_items.append((y_top, table_md, (float(tb.bbox[0]), float(tb.bbox[1]), float(tb.bbox[2]), float(tb.bbox[3]))))
    except Exception:
        pass

    # 2.1) 剔除表格区域内的文本行，避免重复
    def is_inside_any_table(x_center: float, y_center: float) -> bool:
        for _, _, (x0, y0, x1, y1) in table_items:
            if (x0 - 2) <= x_center <= (x1 + 2) and (y0 - 2) <= y_center <= (y1 + 2):
                return True
        return False
    line_items = [ln for ln in line_items if not is_inside_any_table(ln[1], ln[0])]

    # 3) 估算标题阈值（基于行高）
    sizes = sorted([ln[7] for ln in line_items if ln[7] > 0])
    if not sizes:
        sizes = [0.0]
    median = sizes[len(sizes) // 2]
    upper_q = sizes[int(len(sizes) * 0.8)]
    heading_threshold = max(median * 1.25, upper_q)

    # 4) 合并文本与表格为统一流并按 y 排序
    flow: List[Tuple[float, str, str]] = []
    prev_was_heading = False
    for y, x, x0, y0, x1, y1, text, h in line_items:
        if not text:
            continue
        if h >= heading_threshold:
            flow.append((y, "h2" if prev_was_heading else "h1", text))
            prev_was_heading = True
        else:
            flow.append((y, "text", text))
            prev_was_heading = False
    for y, table_md, _ in table_items:
        flow.append((y, "table", table_md))
    flow.sort(key=lambda t: t[0])

    # 5) 生成 Markdown
    out_lines: List[str] = []
    for _, typ, content in flow:
        if typ == "h1":
            out_lines.append(f"# {content}")
        elif typ == "h2":
            out_lines.append(f"## {content}")
        elif typ == "table":
            out_lines.append(content.rstrip())
        else:
            out_lines.append(content)
    return "\n".join(out_lines).strip() + "\n\n"


def convert_pdf_to_markdown(input_pdf: Path, cfg: Optional[MergeConfig] = None) -> str:
    """
    将单个 PDF 转为 Markdown 字符串。
    """
    cfg = cfg or MergeConfig()
    doc = fitz.open(input_pdf.as_posix())
    parts: List[str] = []
    for page in doc:
        parts.append(extract_page_markdown(page, cfg))
    doc.close()
    content = "".join(parts)
    # 简单清理：压缩多余空行
    lines = [line.rstrip() for line in content.splitlines()]
    cleaned: List[str] = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def write_output(md_text: str, input_pdf: Path, output_dir: Path | None, overwrite: bool) -> Path:
    """
    写出 .md 文件，返回输出路径。
    """
    if output_dir is None:
        output_path = input_pdf.with_suffix(".md")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / (input_pdf.stem + ".md")

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在（使用 --overwrite 覆盖）：{output_path}")

    output_path.write_text(md_text, encoding="utf-8")
    return output_path


def find_pdfs_in_dir(root: Path, recursive: bool) -> List[Path]:
    pattern = "**/*.pdf" if recursive else "*.pdf"
    return sorted([p for p in root.glob(pattern) if p.is_file()])


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="将 PDF 文件转换为 Markdown 文件（启发式标题识别）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=str, help="输入路径：PDF 文件或包含 PDF 的目录")
    parser.add_argument("-o", "--output-dir", type=str, default=None, help="输出目录（默认与输入 PDF 同目录）")
    parser.add_argument("-r", "--recursive", action="store_true", help="目录模式递归查找 PDF")
    parser.add_argument("--overwrite", action="store_true", help="若输出文件已存在则覆盖")
    # 竖排文本合并参数
    parser.add_argument("--same-col-tol", type=float, default=12.0, help="同列判定的 x 容差（pt）")
    parser.add_argument("--vert-gap", type=float, default=60.0, help="相邻行允许的基础垂直间距（pt）")
    parser.add_argument("--vert-gap-factor", type=float, default=3.0, help="垂直间距系数（与平均行高相乘）")
    parser.add_argument("--min-vertical-run", type=int, default=3, help="触发竖排合并的最小连续行数")

    args = parser.parse_args(argv)
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    if not input_path.exists():
        print(f"错误：输入路径不存在：{input_path}")
        return 2

    converted: List[Path] = []

    try:
        if input_path.is_file():
            if input_path.suffix.lower() != ".pdf":
                print(f"错误：输入文件不是 PDF：{input_path}")
                return 2
            cfg = MergeConfig(
                same_column_tolerance=args.same_col_tol,
                vertical_gap_limit=args.vert_gap,
                vertical_gap_factor=args.vert_gap_factor,
                min_vertical_run=args.min_vertical_run,
            )
            md = convert_pdf_to_markdown(input_pdf=input_path, cfg=cfg)
            out = write_output(md, input_path, output_dir, args.overwrite)
            converted.append(out)
        else:
            pdfs = find_pdfs_in_dir(input_path, args.recursive)
            if not pdfs:
                print("未在目录中找到 PDF 文件。")
                return 1
            for pdf in pdfs:
                try:
                    cfg = MergeConfig(
                        same_column_tolerance=args.same_col_tol,
                        vertical_gap_limit=args.vert_gap,
                        vertical_gap_factor=args.vert_gap_factor,
                        min_vertical_run=args.min_vertical_run,
                    )
                    md = convert_pdf_to_markdown(pdf, cfg=cfg)
                    out = write_output(md, pdf, output_dir, args.overwrite)
                    converted.append(out)
                except Exception as per_file_err:
                    print(f"转换失败：{pdf} -> {per_file_err}")
    except FileExistsError as exists_err:
        print(str(exists_err))
        return 3
    except Exception as e:
        print(f"转换过程中发生错误：{e}")
        return 1

    if converted:
        print("转换完成：")
        for p in converted:
            print(f"  {p}")
        return 0
    else:
        print("没有生成任何文件。")
        return 1


if __name__ == "__main__":
    sys.exit(main())


