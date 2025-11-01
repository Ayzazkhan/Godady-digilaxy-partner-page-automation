pipeline {
  agent any

  environment {
    CURRENT_DOMAIN = "academiccoursehelp.com"
  }

  stages {
    stage('Checkout Repository') {
      steps {
        git branch: 'main', url: 'https://github.com/Ayzazkhan/Godady-digilaxy-partner-page-automation.git'
      }
    }

    stage('Install Dependencies') {
      steps {
        sh '''
          sudo apt update -y
          sudo apt install -y python3-pip
          pip3 install paramiko beautifulsoup4 requests
        '''
      }
    }

    stage('Inject Partner Block') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'ftp-academiccoursehelp.com',
          usernameVariable: 'FTP_USER',
          passwordVariable: 'FTP_PASS'
        )]) {
          sh '''
            export CURRENT_DOMAIN=${CURRENT_DOMAIN}
            export FTP_USER=${FTP_USER}
            export FTP_PASS=${FTP_PASS}
            python3 scripts/sftp_modify_inject.py
          '''
        }
      }
    }
  }

  post {
    success {
      echo "✅ Deployment successful for ${env.CURRENT_DOMAIN}"
    }
    failure {
      echo "❌ Deployment failed for ${env.CURRENT_DOMAIN}"
    }
  }
}
