#!/usr/bin/env node

import process from 'node:process'
import ospath from 'node:path'
import { fileURLToPath } from 'node:url'
import { run } from '../vendor/asciidoc-tck/harness/lib/test-framework.js'

const __dirname = ospath.dirname(fileURLToPath(import.meta.url))
const PACKAGE_DIR = ospath.join(__dirname, '../vendor/asciidoc-tck')

const adapterCommand = process.argv[2]
if (!adapterCommand) {
  console.error('Usage: node bin/run-tck-json.mjs <adapter-command>')
  process.exit(1)
}

process.env.ASCIIDOC_TCK_TESTS = ospath.join(PACKAGE_DIR, 'tests')
process.env.ASCIIDOC_TCK_ADAPTER_MODE = 'cli'
process.env.ASCIIDOC_TCK_ADAPTER_CLI_COMMAND = adapterCommand

const testFile = ospath.join(PACKAGE_DIR, 'harness/lib/suites/index.js')

const ac = new AbortController()
const testsStream = run({
  files: [testFile],
  signal: ac.signal,
})

const results = {
  passes: [],
  failures: [],
}

for await (const event of testsStream) {
  if (event.type === 'test:pass' && event.data.details.type !== 'suite') {
    results.passes.push(event.data.name)
  }
  if (event.type === 'test:fail' && event.data.details.type !== 'suite') {
    results.failures.push({
      name: event.data.name,
      error: event.data.details.error ? event.data.details.error.message : 'Unknown error',
    })
  }
}

console.log(JSON.stringify(results, null, 2))
