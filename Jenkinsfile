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

          // Load domains + hosts from domains.json
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

          // Build parallel tasks map
          def parallelTasks = [:]
          def successList   = [].asSynchronized()
          def failedList    = [].asSynchronized()

          for (line in rawOutput) {
            def parts        = line.split("\\|")
            def domain       = parts[0].trim()
            def host         = parts[1].trim()
            def credentialId = "ftp-${domain}"
            def ftpUsername  = "partners@${domain}"

            // Capture for closure
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
                successList.add(d)
                echo "✅ DONE: ${d}"
              } catch (err) {
                echo "❌ FAILED: ${d} — ${err.getMessage()}"
                failedList.add(d)
                // No crash — continue other domains
              }
            }
          }

          // Run all domains in parallel
          parallel parallelTasks

          // ── Final Summary ──────────────────────────────
          echo ""
          echo "════════════════════════════════════════════"
          echo "               FINAL SUMMARY                "
          echo "════════════════════════════════════════════"
          echo "✅ SUCCESS: ${successList.size()} domains"
          successList.sort().each { echo "   ✔ ${it}" }
          echo ""
          echo "❌ FAILED: ${failedList.size()} domains"
          failedList.sort().each { echo "   ✖ ${it}" }
          echo "════════════════════════════════════════════"

          if (failedList.size() > 0) {
            currentBuild.result = 'UNSTABLE'
            echo "⚠️ Build UNSTABLE — ${failedList.size()} domain(s) failed"
          }
        }
      }
    }
  }

  post {
    success  { echo "🎉 All domains completed successfully" }
    unstable { echo "⚠️ Completed with some failures — check summary above" }
    failure  { echo "❌ Pipeline failed — check console output" }
  }
}
