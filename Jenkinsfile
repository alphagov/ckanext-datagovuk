#!/usr/bin/env groovy

library("govuk")

REPOSITORY = 'ckanext-datagovuk'

node ('!(ci-agent-4)') {

  try {
    stage('Checkout') {
      govuk.checkoutFromGitHubWithSSH(REPOSITORY)
      govuk.cleanupGit()
      govuk.mergeIntoBranch('main-2.9')
    }

    if (env.BRANCH_NAME == 'main-2.9') {
      stage('Installing Packages for python 3 release') {
        sh("rm -rf ./venv")
        sh("python3.6 -m venv ./venv")
        sh("./bin/install-dependencies.sh ./venv/bin/pip")
      }
    } else {
      stage('Installing Packages for python 2 release') {
        sh("rm -rf ./venv")
        sh("virtualenv --python=/opt/python2.7/bin/python --no-site-packages ./venv")
        sh("bash -c 'venv/bin/python -m pip install --upgrade 'pip==20.3.4''")
        sh("./bin/install-dependencies.sh ./venv/bin/pip")
      }
    }

    stage('Tests') {
      govuk.setEnvar("GOVUK_ENV", "ci")
      sh("bash -c 'source venv/bin/activate ; ./bin/jenkins-tests.sh'")
    }

    if (govuk.hasDockerfile()) {
      govuk.dockerBuildTasks([:], "ckan")
    }

    if (env.BRANCH_NAME == 'main') {
      stage('Push release tag') {
        govuk.pushTag(REPOSITORY, BRANCH_NAME, 'release_' + BUILD_NUMBER, 'main')
      }

      if (govuk.hasDockerfile()) {
        stage("Tag Docker image") {
          govuk.dockerTagBranch("ckan", env.BRANCH_NAME, env.BUILD_NUMBER)
        }
      }
    }
    else if (env.BRANCH_NAME == 'main-2.9') {
      sh("echo 'Build successful, now deploy ckan29 to Integration manually through Jenkins'")
    }
  } catch (e) {
    currentBuild.result = 'FAILED'
    step([$class: 'Mailer',
          notifyEveryUnstableBuild: true,
          recipients: 'govuk-ci-notifications@digital.cabinet-office.gov.uk',
          sendToIndividuals: true])
    throw e
  }

  // Wipe the workspace
  deleteDir()
}
