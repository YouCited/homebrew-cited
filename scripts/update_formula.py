"""Regenerate Formula/cited.rb for a released cited-cli version.

    python3 scripts/update_formula.py 0.8.1

Uses the GitHub tag tarball for cited-cli and the PyPI sdist of every
dependency it resolves to (cited-core included), the same as release.sh in
cited-mcp-infra did. Rust is added as a build dependency only when one of
those sdists needs it, because it pulls in llvm (~2 GB).

Run it on macOS with Python 3.12, like the formula: pip resolves per platform,
and on Linux keyring adds SecretStorage and cryptography (a Rust build).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
import venv
from pathlib import Path

REPO = "YouCited/cited-cli"
FORMULA = Path(__file__).resolve().parent.parent / "Formula" / "cited.rb"
SKIP = {"cited-cli", "pip", "setuptools", "wheel"}
RUST_BUILT = {"pydantic-core", "cryptography", "jiter", "rpds-py"}

TEMPLATE = """class Cited < Formula
  include Language::Python::Virtualenv

  desc "CLI for the Cited GEO platform"
  homepage "https://youcited.com"
  url "{url}"
  sha256 "{sha256}"
  license "Proprietary"

  depends_on "python@3.12"
{rust}
{resources}
  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "cited-cli", shell_output("#{{bin}}/cited version")
  end
end
"""


def fetch(url: str, attempts: int = 30) -> bytes:
    """GET with retries: the tag tarball and PyPI pages can lag a release."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return bytes(resp.read())
        except OSError as e:
            if attempt == attempts - 1:
                raise SystemExit(f"Could not fetch {url}: {e}") from e
            time.sleep(10)
    raise AssertionError("unreachable")


def resolved_packages(tarball: Path, workdir: Path) -> list[tuple[str, str]]:
    """Install cited-cli from the tarball in a scratch venv; return what pip resolved."""
    env_dir = workdir / "venv"
    venv.create(env_dir, with_pip=True)
    python = env_dir / "bin" / "python"
    subprocess.run([python, "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=True)
    # Right after a release, PyPI's index can lag the upload of cited-core.
    for attempt in range(10):
        install = [python, "-m", "pip", "install", "--quiet", "--no-cache-dir", str(tarball)]
        if subprocess.run(install).returncode == 0:
            break
        if attempt == 9:
            raise SystemExit("pip could not install the release after 10 tries")
        time.sleep(30)
    listed = subprocess.run(
        [python, "-m", "pip", "list", "--format=json"],
        check=True,
        capture_output=True,
        text=True,
    )
    packages = [(p["name"], p["version"]) for p in json.loads(listed.stdout)]
    return sorted(
        ((n, v) for n, v in packages if n.lower().replace("_", "-") not in SKIP),
        key=lambda p: p[0].lower(),
    )


def resource_block(name: str, version: str) -> str:
    data = json.loads(fetch(f"https://pypi.org/pypi/{name}/{version}/json", attempts=3))
    sdist = next((u for u in data["urls"] if u["packagetype"] == "sdist"), None)
    if sdist is None:
        raise SystemExit(f"No sdist on PyPI for {name}=={version}")
    resource = name.lower().replace("_", "-").replace(".", "-")
    return (
        f'  resource "{resource}" do\n'
        f'    url "{sdist["url"]}"\n'
        f'    sha256 "{sdist["digests"]["sha256"]}"\n'
        f"  end\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_formula.py <version>")
    if sys.platform != "darwin":
        raise SystemExit("Run this on macOS: dependencies resolve per platform")
    version = sys.argv[1].removeprefix("v")
    url = f"https://github.com/{REPO}/archive/refs/tags/v{version}.tar.gz"

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        tarball = workdir / "source.tar.gz"
        tarball.write_bytes(fetch(url))
        sha256 = hashlib.sha256(tarball.read_bytes()).hexdigest()
        packages = resolved_packages(tarball, workdir)

    names = {n.lower().replace("_", "-") for n, _ in packages}
    if "cited-core" not in names:
        raise SystemExit("cited-core is missing from the resolved packages")
    resources = "\n".join(resource_block(n, v) for n, v in packages)
    rust = '  depends_on "rust" => :build\n' if names & RUST_BUILT else ""
    FORMULA.write_text(TEMPLATE.format(url=url, sha256=sha256, rust=rust, resources=resources))
    print(f"Formula/cited.rb -> v{version}: {len(packages)} resources, rust={'yes' if rust else 'no'}")


if __name__ == "__main__":
    main()
