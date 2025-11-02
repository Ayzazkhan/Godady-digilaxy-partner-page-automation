pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        git credentialsId: 'github-access', url: 'https://github.com/Ayzazkhan/Godady-digilaxy-partner-page-automation.git', branch: 'main'
      }
    }



    stage('Update all domains') {
      steps {
        script {
          def domains = ['academiccoursehelp.com']
          for (d in domains) {
            withCredentials([usernamePassword(credentialsId: "ftp-${d}", usernameVariable: 'FTP_USER', passwordVariable: 'FTP_PASS')]) {
              sh """
                export CURRENT_DOMAIN=${d}
                export FTP_USER=${FTP_USER}
                export FTP_PASS=${FTP_PASS}
                python3 scripts/sftp_modify_inject.py
              """
            }
          }
        }
      }
    }
  }
  post {
    success { echo "All done" }
    failure { echo "See console for errors" }
  }
}
