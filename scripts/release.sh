make version
export VERSION=$(cat appversion.txt)
export docker_image="docker://odacom/velo-action:${VERSION}" && echo $docker_image

make image
docker tag odacom/velo-action:dev odacom/velo-action:$VERSION
docker push -a odacom/velo-action

yq eval -i '.runs.image = env(docker_image)' action.yml

git add action.yml
git commit -m "Release v${VERSION}"

# must commit before tag
git tag "v${VERSION}"

git push
git push --tags origin

gh release create v$VERSION \
    --title "v${VERSION}" \
    --notes "Velo-action release"

echo "Update the release notes manually in the github release page."


echo "Reset action image to latest for future development."

yq eval -i '.runs.image = "docker://odacom/velo-action:latest"' action.yml

git add action.yml
git commit -m "Set image to latest for future development"
git push
