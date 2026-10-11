"""Copy the reviewed project into its standalone repository without its old Git history."""
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1]).resolve()
destination = Path.cwd()
old = "https://github.com/Manoj-619/incident-zero"
new = "https://github.com/Manoj-619/Orbit---Sentinal"
for path in source.rglob("*"):
    if not path.is_file() or ".git" in path.relative_to(source).parts:
        continue
    relative = path.relative_to(source)
    if str(relative) == "README.md" or str(relative).startswith(".github/workflows/"):
        continue
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        content = path.read_text()
    except UnicodeDecodeError:
        shutil.copy2(path, target)
        continue
    content = content.replace(old + "/tree/orbit-sentinel", new)
    content = content.replace(old, new).replace("ORBIT SENTINEL", "ORBIT SENTINAL")
    target.write_text(content)
print("Imported project files, binary assets, and standalone repository links.")
