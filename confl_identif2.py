import os
import subprocess
import tempfile
import git
from git import Repo
import re

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import typing as tp

def clone(repository_url: str) -> str | None:
    repo_name = repository_url.split('/')[-1].replace('.git', '')

    command = ['git', 'clone', repository_url]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(stderr.decode())

    else:
        return os.path.abspath(repo_name)


def get_all_branches(repo_path: str) -> list[str]:
    res: list[str] = []

    repo = Repo(repo_path)
    branches_list = repo.git.branch("-a").splitlines()

    temp_res: list[str] = []
    for b in branches_list:
        temp_res += b.split()

    for s in temp_res:
        if s == "*":
            continue

        if s == "->":
            continue

        if s == "remotes/origin/HEAD":
            continue

        to_build_branch = s.split("/")
        start = 0

        while True:
            if to_build_branch[start] == "remotes" or to_build_branch[start] == "origin":
                start += 1
                continue

            break

        branch = "/".join(to_build_branch[start:])
        res.append(branch)

    return list(set(res))

def analyze_merge_commits_in_exact_branch(repo_path: str, branch: str) -> tuple[dict[str, dict[str, bool | None]], list[tp.Any]]:
    results: dict[str, dict[str, bool | None]] = {}
    repo = Repo(repo_path)

    repo.git.checkout(branch)
    merge_commits = [commit for commit in repo.iter_commits() if len(commit.parents) > 1]

    data: list[tp.Any] = []

    for merge_commit in merge_commits:
        commit_hash = merge_commit.hexsha
        print(f"Merge-commit: {commit_hash}")
        results[commit_hash] = {}
        results[commit_hash]['remerged'] = False
        results[commit_hash]['identical'] = None

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                repo_clone = Repo.clone_from(repo_path, temp_dir)
                repo_clone.git.checkout(merge_commit.hexsha)

                parent1_hexsha = merge_commit.parents[0].hexsha
                parent2_hexsha = merge_commit.parents[1].hexsha

                try:
                    repo_clone.git.checkout(branch)
                    repo_clone.git.reset('--hard', parent1_hexsha)

                except Exception as e:
                    print(f"Ошибка при откате merge-коммита: {e}")
                    results[commit_hash]['remerged'] = False
                    continue

                try:
                    repo_clone.git.merge(parent2_hexsha)
                    repo_clone.index.commit("Retrying merge commit")
                    results[commit_hash]['remerged'] = True
                except Exception as e:
                    print(f"Ошибка при повторном слиянии: {e}")
                    results[commit_hash]['remerged'] = False

                    result = repo_clone.git.diff("--name-only", "--diff-filter=U")
                    conflicted_files = result.strip().splitlines()

                    if conflicted_files:
                        for file_name in conflicted_files:
                            print(f"  Файл: {file_name}")

                            file_path = os.path.join(repo_clone.working_dir, file_name)
                            with open(file_path, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                conflict_blocks = find_conflict_blocks(lines)

                                if conflict_blocks:
                                    for start, end in conflict_blocks:
                                        print(f"  Конфликтный блок строк: {start + 1} - {end + 1}")
                                        content = ""

                                        for i in range(start, end + 1):
                                            print(f"  {i + 1:4}: {lines[i].strip()}")
                                            content += f"{i + 1:4}: {lines[i].strip()}"
                                            content += "\n"

                                        data.append({
                                            "commit": commit_hash,
                                            "file": file_name,
                                            "start": start + 1,
                                            "end": end + 1,
                                            "content": content
                                        })

                                else:
                                    print("    Не удалось найти явные маркеры конфликтов в файле.")
                    continue

                try:
                    current_state = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'], cwd=temp_dir).decode('utf-8').splitlines()
                    original_state = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', merge_commit.hexsha], cwd=temp_dir).decode('utf-8').splitlines()

                    current_state.sort()
                    original_state.sort()
                    results[commit_hash]['identical'] = (current_state == original_state)


                except Exception as e:
                    print(f"Ошибка при сравнении результатов: {e}")
                    results[commit_hash]['identical'] = None

            except Exception as e:
                print(f"Общая ошибка при обработке merge-коммита {commit_hash}: {e}")
                results[commit_hash]['remerged'] = False
                results[commit_hash]['identical'] = None

    return results, data

def analyze_all_merge_commits(repo_path: str) -> None:
    branches = get_all_branches(repo_path)
    data: list[tp.Any] = []

    for branch in branches:
        print("-------------------------------------")
        print(f"Branch: {branch}")
        res_b, tmp_data = analyze_merge_commits_in_exact_branch(repo_path, branch)
        data += tmp_data

        for sha, res in res_b.items():
            print(f"{sha}: {res}")

        print("-------------------------------------")

    repo = Repo(repo_path)
    name = repo.remotes.origin.url.split('/')[-1].replace('.git', '')
    df = pd.DataFrame(data)
    unique_df = df.drop_duplicates()
    unique_df.to_parquet(f'{name}-conflicts.parquet', engine='pyarrow')


def find_conflict_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """
    Returns:
        Список кортежей (start, end), где start - индекс начала конфликтного блока, end - индекс конца.
    """
    conflict_blocks: list[tuple[int, int]] = []
    start = -1

    for i, line in enumerate(lines):
        if line.startswith("<<<<<<<"):
            start = i
        elif line.startswith(">>>>>>>"):
            if start is not None:
                conflict_blocks.append((start, i))
                start = None
    return conflict_blocks

url = "https://github.com/nomic-ai/gpt4all.git"
repo_path = clone(url)

# branch = "dev4.0"

# print(analyze_merge_commits_in_exact_branch(repo_path, branch))
analyze_all_merge_commits(repo_path)
'''branches = get_all_branches(repo_path)
for b in branches:
    print(b)'''