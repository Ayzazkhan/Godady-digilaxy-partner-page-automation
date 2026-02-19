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

          def successList = []
          def failedList  = []

          // ✅ One by one — no parallel
          for (line in rawOutput) {
            def parts        = line.split("\\|")
            def domain       = parts[0].trim()
            def host         = parts[1].trim()
            def credentialId = "ftp-${domain}"
            def ftpUsername  = "cicd@${domain}"

            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "▶ Processing : ${domain}"
            echo "🌐 Host      : ${host}"
            echo "🔐 Credential: ${credentialId}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

            try {
              withCredentials([
                usernamePassword(
                  credentialsId: credentialId,
                  usernameVariable: 'FTP_USER',
                  passwordVariable: 'FTP_PASS'
                )
              ]) {
                sh """
                  export CURRENT_DOMAIN='${domain}'
                  export FTP_HOST='${host}'
                  export FTP_USER='${ftpUsername}'
                  export FTP_PASS=\$FTP_PASS
                  python3 scripts/sftp_modify_inject.py
                """
              }
              successList.add(domain)
              echo "✅ DONE: ${domain}"
            } catch (err) {
              failedList.add(domain)
              echo "❌ FAILED: ${domain} — ${err.getMessage()}"
              // continues to next domain
            }
          }

          // ── Final Summary ──────────────────────────────
          echo ""
          echo "════════════════════════════════════════════════════"
          echo "                   FINAL SUMMARY                    "
          echo "════════════════════════════════════════════════════"
          echo "✅ SUCCESS — ${successList.size()} domains"
          successList.each { d -> echo "   ✔  ${d}" }
          echo ""
          echo "❌ FAILED  — ${failedList.size()} domains"
          failedList.each  { d -> echo "   ✖  ${d}" }
          echo "════════════════════════════════════════════════════"
          echo "📊 TOTAL: ${rawOutput.size()} | ✅ ${successList.size()} | ❌ ${failedList.size()}"
          echo "════════════════════════════════════════════════════"

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
