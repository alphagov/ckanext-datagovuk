#!/bin/bash

set -eux

if [[ ${IS_TAG:-} = "true" ]]; then
  export IMAGE_TAG="${GH_REF}"
  export SOURCE_BRANCH="main"
else
  export IMAGE_TAG=$(gh api repos/alphagov/ckanext-datagovuk/branches/${GH_REF} | jq .commit.sha -r)
  export SOURCE_BRANCH=${GH_REF}
fi

git config --global user.email "govuk-ci@users.noreply.github.com"
git config --global user.name "govuk-ci"

git clone https://${GH_TOKEN}@github.com/alphagov/govuk-ckan-charts.git charts

cd charts/charts/ckan/images

for ENV in $(echo $ENVS | tr "," " "); do
  (
    BRANCH="ci/${IMAGE_TAG}-${ENV}"

    if git show-ref --quiet refs/heads/${BRANCH}; then
      echo "Branch ${BRANCH} already exists on govuk-ckan-charts"
    else
      git checkout -b ${BRANCH}

      cd "${ENV}"
      for APP in ckan pycsw solr; do
        yq -i '.tag = env(IMAGE_TAG)' "${APP}.yaml"
        yq -i '.branch = env(SOURCE_BRANCH)' "${APP}.yaml"
        git add "${APP}.yaml"
      done
      git commit -m "Update image tags for ${ENV} to ${IMAGE_TAG}"
      git push --set-upstream origin "${BRANCH}"
      gh pr create --title "Update image tags for ${ENV} (${IMAGE_TAG})" --base main --head "${BRANCH}" --fill
    fi
  )
done
