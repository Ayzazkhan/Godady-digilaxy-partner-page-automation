pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  stages {

    stage('Checkout') {
      steps {
        git branch: 'main',
            url: 'https://github.com/Ayzazkhan/Godady-digilaxy-partner-page-automation.git',
            credentialsId: 'github-access'
      }
    }

    stage('Inject Partner Content') {
      steps {
        script {

          def rawOutput = sh(
            script: """
              python3 - <<'PY'
import json
data = json.load(open('data/domains.json'))
for domain, info in data.items():
    print(f"{domain}|{info['host']}")
PY
            """,
            returnStdout: true
          ).trim().split("\n")

          echo "📊 Total domains: ${rawOutput.size()}"

          def parallelTasks = [:]
          def results       = [:]

          for (line in rawOutput) {
            def parts  = line.split("\\|")
            def domain = parts[0].trim()
            def host   = parts[1].trim()

            // ✅ Credential ID: ftp-domain.com
            // ✅ FTP Username : cicd@domain.com
            def credentialId = "ftp-${domain}"
            def ftpUsername  = "cicd@${domain}"

            def d = domain
            def h = host
            def c = credentialId
            def u = ftpUsername

            parallelTasks[d] = {
              echo "▶ Starting: ${d}"
              try {
                withCredentials([
                  usernamePassword(
                    credentialsId: c,
                    usernameVariable: 'FTP_USER',
                    passwordVariable: 'FTP_PASS'
                  )
                ]) {
                  sh """
                    export CURRENT_DOMAIN='${d}'
                    export FTP_HOST='${h}'
                    export FTP_USER='${u}'
                    export FTP_PASS=\$FTP_PASS
                    python3 scripts/sftp_modify_inject.py
                  """
                }
                results[d] = 'SUCCESS'
                echo "✅ DONE: ${d}"
              } catch (err) {
                results[d] = 'FAILED'
                echo "❌ FAILED: ${d} — ${err.getMessage()}"
              }
            }
          }

          parallel parallelTasks

          def successList = results.findAll { it.value == 'SUCCESS' }.keySet().sort()
          def failedList  = results.findAll { it.value == 'FAILED'  }.keySet().sort()

          echo "════════════════════════════════════════════"
          echo "               FINAL SUMMARY                "
          echo "════════════════════════════════════════════"
          echo "✅ SUCCESS: ${successList.size()} domains"
          successList.each { echo "   ✔ ${it}" }
          echo ""
          echo "❌ FAILED: ${failedList.size()} domains"
          failedList.each  { echo "   ✖ ${it}" }
          echo "════════════════════════════════════════════"

          if (failedList.size() > 0) {
            currentBuild.result = 'UNSTABLE'
          }
        }
      }
    }
  }

  post {
    success  { echo "🎉 All domains completed successfully" }
    unstable { echo "⚠️ Completed with failures — check summary above" }
    failure  { echo "❌ Pipeline failed" }
  }
}
