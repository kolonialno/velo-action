#!/bin/sh -l
set -e

cd $GITHUB_WORKSPACE

export MODE=$INPUT_MODE
echo MODE=$INPUT_MODE

gitversion

echo "After gitversion"

gitversion > appversion.json

cat appversion.json

cat > releasenotes.md << EOF
{
"commit_id": "${GITHUB_SHA}",
"branch_name": "${GITHUB_REF}"
}
EOF

cat releasenotes.md

jq -r '.SemVer' appversion.json > appversion.txt

VERSION=$(cat appversion.txt)
echo VERSION=$VERSION

echo "::set-output name=version::$VERSION"

if [ "$MODE" = 'DEPLOY' ]; then

    export OCTOPUS_CLI_SERVER=$INPUT_OCTOPUS_CLI_SERVER
    export OCTOPUS_CLI_API_KEY=$INPUT_OCTOPUS_CLI_API_KEY
    export PROJECT=$INPUT_PROJECT

    echo $INPUT_SERVICE_ACCOUNT_KEY | base64 -d > /key.json
    export GOOGLE_APPLICATION_CREDENTIALS=/key.json

    gcloud auth activate-service-account --quiet --key-file /key.json

    cd .deploy

    gsutil -m cp -r . gs://nube-velo-prod-deploy-artifacts/$PROJECT/$VERSION/

    octo create-release --project=$PROJECT --version=$VERSION --releaseNoteFile=$GITHUB_WORKSPACE/releasenotes.md --ignoreExisting

    octo deploy-release --project=$PROJECT --version=$VERSION --deployTo=$ENVIRONMENT
fi
