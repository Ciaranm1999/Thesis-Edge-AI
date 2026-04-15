# Thesis report (LaTeX)

This folder contains the Hanze SSE thesis template imported for use with VS Code + LaTeX Workshop.

## Where to edit

- Main entrypoint: `template/main.tex`
  - Update `\\title{...}`, `\\author{...}`, `\\supervisor{...}`, and `\\courseyear{...}`.
- Chapter content: `template/chapters/` (each `\\input{chapters/...}` in `main.tex` maps to one file).
- References: `template/references.bib`
- Figures: `template/images/`

## Build / view PDF in VS Code

1. Install a TeX distribution (Windows): MiKTeX (recommended) or TeX Live.
2. Open the repository root in VS Code.
3. Open `template/main.tex` and run **LaTeX Workshop: Build LaTeX project**.

Build outputs (PDF + aux files) go to: `template/out/`.

### If bibliography or acronyms don’t update

Use the recipe: **pdflatex → biber → makeglossaries → pdflatex ×2** in the LaTeX Workshop build menu.
