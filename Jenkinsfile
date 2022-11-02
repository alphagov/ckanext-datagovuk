#!/usr/bin/env groovy

library("govuk")

REPOSITORY = 'ckanext-datagovuk'

node ('!(ci-agent-4)') {

  try {
    stage('Checkout') {
      govuk.checkoutFromGitHubWithSSH(REPOSITORY)
      govuk.cleanupGit()
      govuk.mergeIntoBranch('main')
    }

    stage('Installing Packages for python 3 release') {
      sh("rm -rf ./venv")
      sh("python3.6 -m venv ./venv")
      sh("bash -c 'venv/bin/python -m pip install --upgrade 'pip==21.2.2''")
      sh("./bin/install-dependencies.sh ./venv/bin/pip")
    }

    stage('Tests') {
      govuk.setEnvar("GOVUK_ENV", "ci")
      sh("bash -c 'source venv/bin/activate ; ./bin/jenkins-tests.sh'")
    }

    if (env.BRANCH_NAME == 'main') {
      stage('Push release tag') {
        govuk.pushTag(REPOSITORY, BRANCH_NAME, 'release_' + BUILD_NUMBER, 'main')
      }

      stage('Deploy to Integration') {
        govuk.deployIntegration('ckan', BRANCH_NAME, 'release_' + BUILD_NUMBER, 'deploy')
      }
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
