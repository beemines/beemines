# Profile maintenance

The README uses standalone SVG assets, including a typing banner and a bee that visits real contribution dates. Light and dark assets follow the reader's GitHub theme. There is no JavaScript in the README.

`Refresh profile` runs every six hours, on relevant source changes, or manually from Actions. GitHub may delay scheduled runs. It uses the repository's built-in `GITHUB_TOKEN`; no personal access token is stored here.

`selected-contributions.json` is a curated candidate list, not a list of claimed merged work. Add substantial features or correctness/reliability improvements there after reviewing their value. The generator checks the upstream PR's author and actual `merged` state before displaying it. Closed-but-unmerged PRs are excluded. New PRs do not enter this curated list automatically. Up to six merged selections are shown, newest first.

Language percentages are code-byte shares across public, original repositories. Forks and this profile repository are excluded. These numbers do not measure personal proficiency.

To refresh locally, provide a GitHub token through `GH_TOKEN` in the process environment and run `python scripts/generate.py`. Never commit credentials. A failed fetch fails the run rather than publishing invented or partial data.
