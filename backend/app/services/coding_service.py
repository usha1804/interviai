"""
Coding interview service.

Problem generation  -> Groq AI
  - starter_code : skeleton with TODO (shown to user, NO solution)
  - solution_code: complete working solution (used ONLY for test validation, never sent to frontend)
Code execution      -> Local subprocess
Code review         -> Groq AI
"""
import json
import subprocess
import tempfile
import os
import sys
import shutil
from app.config import settings
from app.services.ai_service import _chat, get_groq_client


# ── Problem Generation ────────────────────────────────────────────

def generate_coding_problem(topic: str, difficulty: str = "MEDIUM") -> dict:
    client = get_groq_client()
    prompt = f"""You are a senior software engineer creating a coding interview problem.

Topic: {topic}
Difficulty: {difficulty}

STRICT RULES:
1. Input/output must be plain text lines — NO JSON arrays, NO brackets.
2. starter_code must be a SKELETON only:
   - Reads input from stdin with sys.stdin
   - Has a clear TODO comment where candidate writes logic
   - Does NOT contain any solution, algorithm, or answer
   - Prints nothing meaningful (just a placeholder print or pass)
3. solution_code must be a COMPLETE working Python program that:
   - Reads the same stdin format as starter_code
   - Solves the problem correctly
   - Prints the exact expected_output
4. test_cases inputs must match exactly what the code reads from stdin.
5. test_cases expected_outputs must match exactly what solution_code prints.

Return ONLY valid JSON (no markdown fences, no extra text):
{{
    "title": "problem title",
    "description": "problem statement with input/output format explained",
    "constraints": "input size constraints",
    "sample_input": "example stdin",
    "sample_output": "example stdout",
    "test_cases": [
        {{"input": "stdin", "expected_output": "stdout"}},
        {{"input": "stdin", "expected_output": "stdout"}},
        {{"input": "edge case stdin", "expected_output": "stdout"}}
    ],
    "expected_complexity": "O(n)",
    "hints": ["hint 1", "hint 2"],
    "starter_code": "import sys\\n\\ndef solve():\\n    data = sys.stdin.read().split()\\n    # TODO: implement your solution here\\n    pass\\n\\nsolve()\\n",
    "solution_code": "complete working python solution here"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=2000)
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        problem = json.loads(text[start:end])

        # Guarantee starter_code is a skeleton (never expose solution_code to user)
        if not problem.get("starter_code"):
            problem["starter_code"] = _make_skeleton()

        # Strip solution from starter if AI accidentally included it
        problem["starter_code"] = _ensure_skeleton(problem["starter_code"])

        # Keep solution_code server-side only — frontend never receives it
        return problem
    except Exception:
        return _fallback_problem()


def _make_skeleton() -> str:
    return (
        "import sys\n\n"
        "def solve():\n"
        "    data = sys.stdin.read().split()\n"
        "    # TODO: implement your solution here\n"
        "    pass\n\n"
        "solve()\n"
    )


def _ensure_skeleton(code: str) -> str:
    """If AI put a real solution in starter_code, replace with skeleton."""
    suspicious = [
        "seen[complement]", "seen[num]", "hashmap", "hash_map",
        "dp[i]", "dp[j]", "return result", "ans =", "answer =",
    ]
    for kw in suspicious:
        if kw in code:
            return _make_skeleton()
    return code


def _fallback_problem() -> dict:
    return {
        "title": "Sum of Array",
        "description": (
            "Given n integers, print their sum.\n\n"
            "Input format:\n"
            "Line 1: n (count of integers)\n"
            "Line 2: n space-separated integers\n\n"
            "Output: a single integer — the sum"
        ),
        "constraints": "1 <= n <= 10^5, -10^9 <= each number <= 10^9",
        "sample_input": "5\n1 2 3 4 5",
        "sample_output": "15",
        "test_cases": [
            {"input": "5\n1 2 3 4 5",   "expected_output": "15"},
            {"input": "3\n10 20 30",     "expected_output": "60"},
            {"input": "1\n-5",           "expected_output": "-5"},
        ],
        "expected_complexity": "O(n)",
        "hints": ["Read all numbers", "Use the built-in sum()"],
        "starter_code": (
            "import sys\n\n"
            "def solve():\n"
            "    data = sys.stdin.read().split()\n"
            "    n = int(data[0])\n"
            "    nums = list(map(int, data[1:n+1]))\n"
            "    # TODO: compute and print the sum\n"
            "    pass\n\n"
            "solve()\n"
        ),
        "solution_code": (
            "import sys\n\n"
            "def solve():\n"
            "    data = sys.stdin.read().split()\n"
            "    n = int(data[0])\n"
            "    nums = list(map(int, data[1:n+1]))\n"
            "    print(sum(nums))\n\n"
            "solve()\n"
        ),
    }


# ── Local subprocess helpers ──────────────────────────────────────

def _exec(cmd: list, stdin: str, cwd: str = None) -> dict:
    try:
        r = subprocess.run(
            cmd,
            input=stdin or "",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        return {
            "output": r.stdout.strip(),
            "stderr": r.stderr.strip(),
            "compile_error": "",
            "status": "Accepted" if r.returncode == 0 else "Runtime Error",
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": "", "compile_error": "", "status": "Time Limit Exceeded"}
    except FileNotFoundError as e:
        return {"output": "", "stderr": str(e), "compile_error": "", "status": "Runtime Error"}


def _run_python(code: str, stdin: str) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        return _exec([sys.executable, path], stdin)
    finally:
        _safe_remove(path)


def _run_javascript(code: str, stdin: str) -> dict:
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        return _not_installed("Node.js", "https://nodejs.org")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        return _exec([node, path], stdin)
    finally:
        _safe_remove(path)


def _run_java(code: str, stdin: str) -> dict:
    javac = shutil.which("javac")
    java = shutil.which("java")
    if not javac or not java:
        return _not_installed("Java JDK", "https://adoptium.net")
    tmpdir = tempfile.mkdtemp()
    try:
        class_name = "Main"
        for line in code.splitlines():
            line = line.strip()
            if line.startswith("public class "):
                class_name = line.split()[2].rstrip("{")
                break
        src = os.path.join(tmpdir, f"{class_name}.java")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        cr = subprocess.run([javac, src], capture_output=True, text=True, timeout=15)
        if cr.returncode != 0:
            return {"output": "", "stderr": "", "compile_error": cr.stderr.strip(), "status": "Compilation Error"}
        return _exec([java, "-cp", tmpdir, class_name], stdin)
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": "", "compile_error": "", "status": "Time Limit Exceeded"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_cpp(code: str, stdin: str) -> dict:
    gpp = shutil.which("g++")
    if not gpp:
        return _not_installed("G++ (MinGW)", "https://www.mingw-w64.org/downloads/")
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "main.cpp")
    exe = os.path.join(tmpdir, "main.exe" if sys.platform == "win32" else "main")
    try:
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        cr = subprocess.run([gpp, src, "-o", exe, "-std=c++17"], capture_output=True, text=True, timeout=15)
        if cr.returncode != 0:
            return {"output": "", "stderr": "", "compile_error": cr.stderr.strip(), "status": "Compilation Error"}
        return _exec([exe], stdin)
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": "", "compile_error": "", "status": "Time Limit Exceeded"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_c(code: str, stdin: str) -> dict:
    gcc = shutil.which("gcc")
    if not gcc:
        return _not_installed("GCC (MinGW)", "https://www.mingw-w64.org/downloads/")
    tmpdir = tempfile.mkdtemp()
    src = os.path.join(tmpdir, "main.c")
    exe = os.path.join(tmpdir, "main.exe" if sys.platform == "win32" else "main")
    try:
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        cr = subprocess.run([gcc, src, "-o", exe], capture_output=True, text=True, timeout=15)
        if cr.returncode != 0:
            return {"output": "", "stderr": "", "compile_error": cr.stderr.strip(), "status": "Compilation Error"}
        return _exec([exe], stdin)
    except subprocess.TimeoutExpired:
        return {"output": "", "stderr": "", "compile_error": "", "status": "Time Limit Exceeded"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _not_installed(name: str, url: str) -> dict:
    return {
        "output": "",
        "stderr": f"{name} is not installed. Install from {url} and restart the backend.",
        "compile_error": "",
        "status": "Not Installed",
    }


def _safe_remove(path: str):
    try:
        os.unlink(path)
    except Exception:
        pass


_RUNNERS = {
    "python":     _run_python,
    "javascript": _run_javascript,
    "java":       _run_java,
    "cpp":        _run_cpp,
    "c":          _run_c,
}


def run_code(code: str, language: str, stdin: str = "") -> dict:
    """Execute code locally — no external API required."""
    runner = _RUNNERS.get(language.lower())
    if not runner:
        return {"output": "", "stderr": f"Unsupported language: {language}", "compile_error": "", "status": "Error"}
    return runner(code, stdin or "")


def run_test_cases(code: str, language: str, test_cases: list) -> dict:
    """Run solution_code (not starter_code) against all test cases."""
    passed = 0
    results = []

    def normalize(s: str) -> str:
        return "\n".join(line.strip() for line in str(s).strip().splitlines() if line.strip())

    for tc in test_cases:
        result = run_code(code, language, tc.get("input", ""))
        actual = normalize(result.get("output") or "")
        expected = normalize(tc.get("expected_output") or "")
        ok = actual == expected
        if ok:
            passed += 1
        results.append({
            "input": tc.get("input"),
            "expected": expected,
            "actual": actual,
            "passed": ok,
            "status": result.get("status", ""),
        })
    return {"passed": passed, "total": len(test_cases), "results": results}


# ── AI Code Review ────────────────────────────────────────────────

def ai_review_code(problem: str, code: str, language: str, test_result: dict) -> dict:
    client = get_groq_client()
    prompt = f"""You are a Senior Software Engineer reviewing a coding interview submission.

Problem: {problem}
Language: {language}
Candidate's Code:
```
{code[:2000]}
```
Test Results: {test_result['passed']}/{test_result['total']} test cases passed.

Return ONLY this JSON:
{{
    "score": <0-100>,
    "time_complexity": "<e.g. O(n)>",
    "space_complexity": "<e.g. O(1)>",
    "correctness": "<assessment>",
    "code_quality": "<assessment>",
    "strengths": ["<s1>", "<s2>"],
    "improvements": ["<i1>", "<i2>"],
    "optimized_approach": "<brief description>",
    "overall_feedback": "<2-3 sentence summary>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1000)
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "score": 60,
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "correctness": "Partially correct",
            "code_quality": "Average",
            "strengths": ["Attempted the problem"],
            "improvements": ["Review edge cases", "Optimize time complexity"],
            "optimized_approach": "Consider using a hash map for O(n) solution.",
            "overall_feedback": "Good attempt. Focus on edge cases and optimizing complexity.",
        }
