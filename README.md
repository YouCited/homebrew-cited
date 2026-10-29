# Homebrew Tap for Cited CLI

## Install

```bash
brew install youcited/cited/cited
```

Use the full name: Homebrew 7 only loads formulae from trusted taps, and installing by full name trusts just this formula.

## Upgrading an older install

If you tapped this repo and installed before Homebrew 7, trust the formula once (safe to re-run), then upgrade:

```bash
brew trust --formula youcited/cited/cited
brew upgrade cited
```

## Source

https://github.com/YouCited/cited-cli

## Updates

`Formula/cited.rb` is generated, so don't edit it by hand. Every 30 minutes the "Update formula" workflow checks PyPI for a newer cited-cli. When it finds one, it regenerates the formula with `scripts/update_formula.py` (on macOS, with Python 3.12), then runs `brew install` and `brew test` and a free audit on a macOS runner, and commits the formula only if they pass. To update right away, run the workflow from the Actions tab, optionally with a version.
