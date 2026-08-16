# MkDocs - GitBook alternative, on GitHub pages

https://squidfunk.github.io/mkdocs-material/ 

```bash
brew install python
pip3 install mkdocs-material
git clone git@github.com:<...>/<...>.git
cd $destination_folder
mkdocs new .
echo "<DOMAIN_NAME>" > CNAME
tee -a mkdocs.yml  > /dev/null <<EOT
theme:
  name: material
EOT

mkdir -p .github/workflows
tee -a .github/workflows/ci.yml  > /dev/null <<EOT
name: ci 
on:
  push:
    branches:
      - master 
      - main
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.x
      - run: pip install mkdocs-material 
      - run: mkdocs gh-deploy --force
EOT

mkdocs serve

# edit files as required
mkdocs build

# git commit & push files
# setup gh-pages branch as source of the github pages
```

Markdown extensions: https://python-markdown.github.io/extensions/
