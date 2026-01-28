from datetime import datetime
import os

# Mock objects
class MockCommit:
    def __init__(self, sha):
        self.sha = sha
        self.commit = type('obj', (object,), {
            'author': type('obj', (object,), {'date': datetime.now()})
        })

class MockBranch:
    def __init__(self, name):
        self.name = name
        self.commit = type('obj', (object,), {'sha': 'abc'})

class MockRepo:
    def get_branches(self):
        return [MockBranch('main'), MockBranch('feat/test')]
    def get_commit(self, sha):
        return MockCommit(sha)

class MockGH:
    def get_repo(self, name):
        return MockRepo()

gh = MockGH()

def get_repo_branches(repo_full_name):
    if not gh or not repo_full_name:
        return ["main"]
    try:
        repo = gh.get_repo(repo_full_name)
        branches = list(repo.get_branches())
        branch_info = []
        for b in branches:
            commit = repo.get_commit(b.commit.sha)
            date = commit.commit.author.date
            branch_info.append((b.name, date))

        branch_info.sort(key=lambda x: x[1], reverse=True)
        return [b[0] for b in branch_info]
    except Exception as e:
        print(f"Error: {e}")
        return ["main"]

print(f"Branches: {get_repo_branches('test/repo')}")
