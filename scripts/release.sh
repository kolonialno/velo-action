make version
export VERSION=$(cat appversion.txt)
export docker_image="docker://europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:${VERSION}" && echo $docker_image

make image
docker tag europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:dev europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:$VERSION
docker push -a europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action

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

yq eval -i '.runs.image = "docker://europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:latest"' action.yml

git add action.yml
git commit -m "Set image to latest for future development"
git push
