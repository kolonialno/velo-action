make version
export VERSION=$(cat appversion.txt)
export docker_image="docker://odacom/velo-action:${VERSION}" && echo $docker_image

yq eval -i '.runs.image = env(docker_image)' action.yml

git tag "v${VERSION}" --force

git add action.yml
git commit -m "Release v${VERSION}"
git push
git push --tags origin

gh release create v$VERSION \
    --title "v${VERSION}"