# HCRL (ARCHITECT) media sources

- `make_charts.py`: `sr-by-task.svg` (Tables 1 and 2 of arXiv 2607.23784v1) and
  `language-ablation.svg` (Table 3), numbers transcribed from the paper.
- `make_diagram.py`: `harness-diagram.svg`, drawn from EricJGoossen/VLA_benchmarking's README and code.
- Videos: the rollout clips on the paper's website, whose source is
  github.com/robo-architect/robo-architect.github.io (the videos are served from
  storage.googleapis.com/architect-project-vids-b4ed5e/videos/<task>__<method>.mp4).
  - `rollout-*.mp4`: single π0 / π0.5 clips, re-encoded (crf 26, metadata stripped).
  - `compare-*.mp4`: the four methods on one task in a labeled 2×2 grid (ffmpeg xstack, each cell
    padded to the longest clip by holding its last frame).
  - `hero-architect.mp4`: the ARCHITECT clips for the bowl, drawer and cloth tasks, back to back at 1280×720.
  - `architect-video.mp4`: the supplementary video (`architect_teaser.mp4`), at 960 px wide.
- Figures from the website: `architect-overview.png`, `human-eval-queries.png` (compare_05_vs_06),
  `human-eval-success.png` (compare_03_vs_04).
- From the PDF: `human-eval-*.jpg` (pdfimages, pages 17 and 18), `paper-page-1.jpg` and
  `paper-page-14.jpg` (pdftoppm at 90 dpi).
