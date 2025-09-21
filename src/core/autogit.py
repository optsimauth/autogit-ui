#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import subprocess
import sys
from datetime import datetime
import os

#
# @click.command()
# @click.option('--message', '-m', default=None, help='自定义提交信息')
# @click.option('--push/--no-push', default=True, help='是否推送到远程仓库')
# def autogit(message, push):
#     """自动执行 git add, commit 和 push 操作"""
#
#     # 检查是否在git仓库中
#     if not os.path.exists('.git') and not subprocess.run(['git', 'rev-parse', '--git-dir'],
#                                                          capture_output=True, text=True, encoding='utf-8',
#                                                          errors='ignore').returncode == 0:
#         click.echo(click.style("❌ 错误: 当前目录不是一个Git仓库", fg='red'))
#         sys.exit(1)
#
#     try:
#         # Git add .
#         click.echo(click.style("📁 正在添加文件...", fg='blue'))
#         result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
#         if result.returncode != 0:
#             click.echo(click.style(f"❌ Git add 失败: {result.stderr}", fg='red'))
#             sys.exit(1)
#
#         # 检查是否有文件需要提交
#         result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
#         if result.returncode == 0:
#             click.echo(click.style("ℹ️  没有文件需要提交", fg='yellow'))
#             return
#
#         # Git commit
#         if message is None:
#             current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             message = f"Auto commit: {current_date}"
#
#         click.echo(click.style(f"💾 正在提交: {message}", fg='blue'))
#         result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, text=True)
#         if result.returncode != 0:
#             click.echo(click.style(f"❌ Git commit 失败: {result.stderr}", fg='red'))
#             sys.exit(1)
#
#         click.echo(click.style("✅ 提交成功!", fg='green'))
#
#         # Git push (如果启用)
#         if push:
#             click.echo(click.style("🚀 正在推送到远程仓库...", fg='blue'))
#             result = subprocess.run(['git', 'push'], capture_output=True, text=True)
#             if result.returncode != 0:
#                 click.echo(click.style(f"❌ Git push 失败: {result.stderr}", fg='red'))
#                 click.echo(click.style("💡 提示: 可能需要先设置远程仓库或者检查网络连接", fg='yellow'))
#                 sys.exit(1)
#
#             click.echo(click.style("🎉 推送成功!", fg='green'))
#         else:
#             click.echo(click.style("ℹ️  跳过推送步骤", fg='yellow'))
#
#     except FileNotFoundError:
#         click.echo(click.style("❌ 错误: 找不到git命令，请确保已安装Git", fg='red'))
#         sys.exit(1)
#     except Exception as e:
#         click.echo(click.style(f"❌ 未知错误: {str(e)}", fg='red'))
#         sys.exit(1)
#
#
# if __name__ == '__main__':
#     autogit()

# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from datetime import datetime
import os
import click  # 保留 click 库，以便在命令行中仍然可用


def autogit(path, message=None, push=True):
    """
    自动执行 git add, commit 和 push 操作

    参数:
    path (str): Git 仓库的路径。
    message (str): 自定义提交信息。
    push (bool): 是否推送到远程仓库。
    """

    # 检查路径是否存在
    if not os.path.isdir(path):
        print(f"❌ 错误: 路径 '{path}' 不存在或不是一个目录")
        return False

    # 检查是否在git仓库中
    git_dir_check = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=path, capture_output=True,
                                   text=True)
    if git_dir_check.returncode != 0:
        print(f"❌ 错误: 路径 '{path}' 不是一个Git仓库")
        return False

    try:
        # Git add .
        print("📁 正在添加文件...")
        result = subprocess.run(['git', 'add', '.'], cwd=path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Git add 失败: {result.stderr}")
            return False

        # 检查是否有文件需要提交
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=path, capture_output=True)
        if result.returncode == 0:
            print("ℹ️  没有文件需要提交")
            return True

        # Git commit
        if message is None:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto commit: {current_date}"

        print(f"💾 正在提交: {message}")
        result = subprocess.run(['git', 'commit', '-m', message], cwd=path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Git commit 失败: {result.stderr}")
            return False

        print("✅ 提交成功!")

        # Git push (如果启用)
        if push:
            print("🚀 正在推送到远程仓库...")
            result = subprocess.run(['git', 'push'], cwd=path, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Git push 失败: {result.stderr}")
                print("💡 提示: 可能需要先设置远程仓库或者检查网络连接")
                return False
            print("🎉 推送成功!")
        else:
            print("ℹ️  跳过推送步骤")

        return True

    except FileNotFoundError:
        print("❌ 错误: 找不到git命令，请确保已安装Git")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False


# 保留命令行入口，但使用新的函数
@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--message', '-m', default=None, help='自定义提交信息')
@click.option('--push/--no-push', default=True, help='是否推送到远程仓库')
def autogit_cli(path, message, push):
    """自动执行 git add, commit 和 push 操作"""
    autogit(path, message, push)


if __name__ == '__main__':
    autogit_cli()