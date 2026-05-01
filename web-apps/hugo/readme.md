Init hugo: 
docker run --rm -it --entrypoint /bin/sh -v hugo_data:/src hugomods/hugo:exts-non-root
hugo new project quickstart
cd quickstart
git init
git submodule add https://github.com/theNewDynamic/gohugo-theme-ananke.git themes/ananke
echo "theme = 'ananke'" >> hugo.toml
hugo server