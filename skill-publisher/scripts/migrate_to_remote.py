#!/usr/bin/env python3
"""Move selected local skills into a remote checkout and leave symlink stubs."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def die(message: str) -> None:
    raise SystemExit(f"error: {message}")


def is_empty_status(repo: Path) -> bool:
    return not run_git(repo, "status", "--porcelain").stdout.strip()


def tracked(repo: Path, relative: str) -> bool:
    return run_git(repo, "ls-files", "--error-unmatch", "--", relative, check=False).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将 custom-skills 中选定的实体目录迁移到远端 checkout，并创建软链接。"
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path.cwd(),
        help="custom-skills 根目录，默认是当前目录",
    )
    parser.add_argument(
        "--remote-root",
        type=Path,
        required=True,
        help="已 clone 的远端多 skill 仓库目录",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际移动目录、修改父仓库索引并创建软链接；默认只预览",
    )
    parser.add_argument("skills", nargs="+", help="要迁移的 skill 目录名")
    args = parser.parse_args()

    source_root = args.source_root.expanduser().resolve()
    remote_root = args.remote_root.expanduser().resolve()
    if not (source_root / ".git").exists():
        die(f"source root 不是 Git 工作区：{source_root}")
    if not (remote_root / ".git").exists():
        die(f"remote root 不是 Git 工作区：{remote_root}")
    if not is_empty_status(source_root):
        die("source root 有未提交改动，请先处理后再迁移")
    if not is_empty_status(remote_root):
        die("remote root 有未提交改动，请先处理后再迁移")

    items: list[tuple[str, Path, Path, bool]] = []
    for name in args.skills:
        source = source_root / name
        target = remote_root / name
        if Path(name).name != name or name in {"", ".", ".."}:
            die(f"skill 名称必须是直接子目录名：{name!r}")
        if not source.is_dir() or source.is_symlink():
            die(f"源目录不存在或已经是软链接：{source}")
        if not (source / "SKILL.md").is_file():
            die(f"缺少 SKILL.md：{source}")
        if os.path.lexists(target):
            die(f"远端目标已存在，不覆盖：{target}")
        items.append((name, source, target, tracked(source_root, name)))

    print("迁移计划：")
    for name, source, target, is_tracked in items:
        print(f"  {source} -> {target} (父仓库 tracked={is_tracked})")
    if not args.apply:
        print("dry-run：未修改任何文件。需要执行时添加 --apply。")
        return 0

    for name, source, target, is_tracked in items:
        if is_tracked:
            result = run_git(source_root, "rm", "-r", "--cached", "--", name, check=False)
            if result.returncode != 0:
                die(result.stderr.strip() or f"无法从父仓库索引移除：{name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        os.symlink(str(target), str(source))
        exclude = source_root / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        line = f"/{name}\n"
        if line not in existing.splitlines(keepends=True):
            with exclude.open("a", encoding="utf-8") as handle:
                handle.write(line)

    print("迁移完成。远端仓库尚未 commit 或 push。")
    print("建议先检查软链接和 SKILL.md，再在远端 checkout 中提交。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        die(f"找不到命令或路径：{shlex.join(exc.filename if isinstance(exc.filename, list) else [str(exc.filename)])}")
