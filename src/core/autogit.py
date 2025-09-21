#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from datetime import datetime
import os
import click  # 保留 click 库，以便在命令行中仍然可用


class AutoGitResult:
    """Git操作结果类"""

    def __init__(self, success=False, message="", details="", step=""):
        self.success = success
        self.message = message  # 主要信息
        self.details = details  # 详细信息
        self.step = step  # 当前步骤


def autogit(path, message=None, push=True, silent=False):
    """
    自动执行 git add, commit 和 push 操作

    参数:
    path (str): Git 仓库的路径。
    message (str): 自定义提交信息。
    push (bool): 是否推送到远程仓库。
    silent (bool): 是否静默模式（不打印到终端）。

    返回:
    AutoGitResult: 操作结果对象
    """

    def log_print(msg):
        """根据silent参数决定是否打印"""
        if not silent:
            print(msg)

    # 检查路径是否存在
    if not os.path.isdir(path):
        error_msg = f"路径 '{path}' 不存在或不是一个目录"
        log_print(f"❌ 错误: {error_msg}")
        return AutoGitResult(False, "路径无效", error_msg, "检查路径")

    # 检查是否在git仓库中
    git_dir_check = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                                   cwd=path, capture_output=True, text=True)
    if git_dir_check.returncode != 0:
        error_msg = f"路径 '{path}' 不是一个Git仓库"
        log_print(f"❌ 错误: {error_msg}")
        return AutoGitResult(False, "不是Git仓库", error_msg, "检查Git仓库")

    try:
        # Git add .
        log_print("📁 正在添加文件...")
        result = subprocess.run(['git', 'add', '.'], cwd=path, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Git add 失败: {result.stderr.strip()}"
            log_print(f"❌ {error_msg}")
            return AutoGitResult(False, "添加文件失败", error_msg, "git add")

        # 检查是否有文件需要提交
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=path, capture_output=True)
        if result.returncode == 0:
            info_msg = "没有文件需要提交"
            log_print(f"ℹ️  {info_msg}")
            return AutoGitResult(True, info_msg, "工作区是干净的", "检查变更")

        # Git commit
        if message is None:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto commit: {current_date}"

        log_print(f"💾 正在提交: {message}")
        result = subprocess.run(['git', 'commit', '-m', message], cwd=path, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"Git commit 失败: {result.stderr.strip()}"
            log_print(f"❌ {error_msg}")
            return AutoGitResult(False, "提交失败", error_msg, "git commit")

        log_print("✅ 提交成功!")

        # Git push (如果启用)
        if push:
            log_print("🚀 正在推送到远程仓库...")
            result = subprocess.run(['git', 'push'], cwd=path, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error_msg = f"Git push 失败: {result.stderr.strip()}"
                hint_msg = "可能需要先设置远程仓库或者检查网络连接"
                log_print(f"❌ {error_msg}")
                log_print(f"💡 提示: {hint_msg}")
                return AutoGitResult(False, "推送失败", f"{error_msg}\n提示: {hint_msg}", "git push")

            success_msg = "提交并推送成功!"
            log_print("🎉 推送成功!")
            return AutoGitResult(True, success_msg, f"已提交: {message}", "完成")
        else:
            success_msg = "提交成功 (跳过推送)"
            log_print("ℹ️  跳过推送步骤")
            return AutoGitResult(True, success_msg, f"已提交: {message}", "完成")

    except subprocess.TimeoutExpired:
        error_msg = "操作超时，可能是网络问题"
        log_print(f"❌ 错误: {error_msg}")
        return AutoGitResult(False, "操作超时", error_msg, "网络超时")
    except FileNotFoundError:
        error_msg = "找不到git命令，请确保已安装Git"
        log_print(f"❌ 错误: {error_msg}")
        return AutoGitResult(False, "Git未安装", error_msg, "检查Git安装")
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        log_print(f"❌ {error_msg}")
        return AutoGitResult(False, "未知错误", error_msg, "异常处理")


# 保留命令行入口，但使用新的函数
@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--message', '-m', default=None, help='自定义提交信息')
@click.option('--push/--no-push', default=True, help='是否推送到远程仓库')
def autogit_cli(path, message, push):
    """自动执行 git add, commit 和 push 操作"""
    result = autogit(path, message, push, silent=False)
    if not result.success:
        sys.exit(1)


if __name__ == '__main__':
    autogit_cli()