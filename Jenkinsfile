pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        git credentialsId: 'github-access', url: 'https://github.com/Ayzazkhan/Godady-digilaxy-partner-page-automation.git', branch: 'main'
      }
    }



    stage('Process domains') {
      steps {
        script {
          // get domains list from file using python to avoid needing jq/plugin
          def domainsOutput = sh(script: "python3 - <<'PY'\nimport json\nprint('\\n'.join(list(json.load(open('data/domains.json')).keys())))\nPY", returnStdout: true).trim()
          def domains = domainsOutput.tokenize('\n')
          echo "Domains to process: ${domains}"

          for (d in domains) {
            def credId = "ftp-${d}"
            echo "Processing ${d} with credential id ${credId}"
            withCredentials([usernamePassword(credentialsId: credId, usernameVariable: 'FTP_USER', passwordVariable: 'FTP_PASS')]) {
              sh """
                export CURRENT_DOMAIN=${d}
                export FTP_USER=${FTP_USER}
                export FTP_PASS='${FTP_PASS}'
                python3 scripts/ftp_modify_inject.py
              """
            }
          }
        }
      }
    }
  }

  post {
    success { echo "✅ All domains processed" }
    failure { echo "❌ Some error occurred — check console" }
  }
}
