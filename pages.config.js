export default {
  build: {
    command: "pip install -r requirements.txt",
    outputDirectory: "templates",
    environment: {
      PYTHON_VERSION: "3.11"
    }
  },
  routes: [
    {
      pattern: "/*",
      script: "worker.js"
    }
  ]
}
