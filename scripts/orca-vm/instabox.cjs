const cp = require('child_process');
const fs = require('fs');

const NL = String.fromCharCode(10);
const env = process.env;

const log = (message) => {
  process.stderr.write('[instabox] ' + message + NL);
};

const fail = (message) => {
  log(message);
  process.exit(1);
};

const run = (args, options) => {
  const result = cp.spawnSync('instabox', args, {
    encoding: 'utf8',
    stdio: [options && options.input !== undefined ? 'pipe' : 'ignore', 'pipe', 'pipe'],
    input: options && options.input,
    env: env,
    timeout: ((options && options.timeoutSeconds) || 900) * 1000,
    windowsHide: true,
  });
  if (result.error) {
    if (result.error.code === 'ENOENT') {
      fail('The instabox CLI is not on PATH. Run npx instabox@latest in a terminal to sign in and install it, then restart Orca.');
    }
    fail('instabox ' + args[0] + ': ' + result.error.message);
  }
  if (result.stderr && !(options && options.quiet)) {
    process.stderr.write(result.stderr);
  }
  return result;
};

const must = (args, options) => {
  const result = run(args, options);
  if (result.status !== 0) {
    throw new Error('instabox ' + args[0] + ' failed with exit code ' + result.status + '.');
  }
  return result.stdout;
};

const QUOTE = String.fromCharCode(39);
const BACKSLASH = String.fromCharCode(92);
const shellQuote = (value) => QUOTE + String(value).split(QUOTE).join(QUOTE + BACKSLASH + QUOTE + QUOTE) + QUOTE;

const remote = (machineId, command, flags, options) => run(['exec', machineId].concat(flags || [], ['--', command]), options);

const slug = (value) => {
  let out = '';
  for (const ch of String(value || '').toLowerCase()) {
    const alnum = (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9');
    out += alnum ? ch : '-';
  }
  return out.split('-').filter(Boolean).join('-');
};

const machineName = (workspaceName, instanceId) => {
  const suffix = slug(instanceId).split('-').join('').slice(-8) || String(Date.now()).slice(-8);
  const base = slug(workspaceName).slice(0, 40).split('-').filter(Boolean).join('-') || 'workspace';
  return 'orca-' + base + '-' + suffix;
};

const originUrl = () => {
  const result = cp.spawnSync('git', ['remote', 'get-url', 'origin'], {
    cwd: env.ORCA_REPO_PATH || process.cwd(),
    encoding: 'utf8',
    windowsHide: true,
  });
  return result.status === 0 ? result.stdout.trim() : '';
};

const currentBranch = () => {
  const result = cp.spawnSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], {
    cwd: env.ORCA_REPO_PATH || process.cwd(),
    encoding: 'utf8',
    windowsHide: true,
  });
  if (result.status === 0) {
    const b = result.stdout.trim();
    if (b && b !== 'HEAD') {
      return b;
    }
  }
  return 'main';
};

const currentHead = () => {
  const result = cp.spawnSync('git', ['rev-parse', 'HEAD'], {
    cwd: env.ORCA_REPO_PATH || process.cwd(),
    encoding: 'utf8',
    windowsHide: true,
  });
  return result.status === 0 ? result.stdout.trim() : '';
};

const httpsCloneUrl = (url) => {
  if (url.startsWith('https://') || url.startsWith('http://')) {
    return url;
  }
  if (url.startsWith('ssh://')) {
    const rest = url.slice('ssh://'.length);
    const hostAndPath = rest.includes('@') ? rest.slice(rest.indexOf('@') + 1) : rest;
    const slash = hostAndPath.indexOf('/');
    const host = hostAndPath.slice(0, slash).split(':')[0];
    return 'https://' + host + hostAndPath.slice(slash);
  }
  const scp = url.indexOf(':');
  if (url.includes('@') && scp > url.indexOf('@') && !url.includes('://')) {
    return 'https://' + url.slice(url.indexOf('@') + 1, scp) + '/' + url.slice(scp + 1);
  }
  return '';
};

const withoutCredentials = (url) => {
  const scheme = url.indexOf('://') + 3;
  const at = url.indexOf('@', scheme);
  const slash = url.indexOf('/', scheme);
  return at > 0 && (slash < 0 || at < slash) ? url.slice(0, scheme) + url.slice(at + 1) : url;
};

const repoDirName = (url) => {
  const last = url.split('/').filter(Boolean).pop() || '';
  return slug(last.endsWith('.git') ? last.slice(0, -4) : last) || 'repo';
};

const readPayload = () => {
  let payload = {};
  try {
    payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (e) {}
  const userData = (payload.recipeResult && payload.recipeResult.userData) || {};
  let machineId = userData.machineId;
  if (!machineId && (payload.instanceId || env.ORCA_VM_INSTANCE_ID)) {
    machineId = machineName(
      env.ORCA_WORKSPACE_NAME || payload.workspaceName || 'workspace',
      payload.instanceId || env.ORCA_VM_INSTANCE_ID
    );
  }
  if (!machineId) {
    fail('This workspace has no Instabox machine id in its recipe result.');
  }
  return { machineId: machineId, recipeResult: payload.recipeResult };
};

const machineState = (machineId) => {
  const result = run(['get', machineId, '--json'], { quiet: true });
  if (result.status !== 0) {
    const output = (result.stdout || '') + (result.stderr || '');
    const missing = ['no sandbox with', 'not_found', 'not found'].some((text) => output.includes(text));
    return missing ? 'gone' : 'unknown';
  }
  const machine = JSON.parse(result.stdout);
  return String(machine.state || machine.status || 'unknown').toLowerCase();
};

const removeMachine = (machineId) => {
  if (run(['rm', machineId, '--yes']).status === 0 || run(['rm', machineId]).status === 0) {
    return true;
  }
  return machineState(machineId) === 'gone';
};

const connectionResult = (machineId, machineName, projectRoot) => {
  const token = JSON.parse(must(['ssh-token', machineId, '--ttl', 'never', '--json']));
  return {
    schemaVersion: 2,
    checkoutMode: 'provisioned-root',
    connection: {
      type: 'ssh',
      projectRoot: projectRoot,
      target: {
        label: 'Instabox ' + machineName,
        host: token.host,
        port: token.port,
        username: token.token,
      },
    },
    userData: {
      provider: 'instabox',
      machineId: machineId,
      machineName: machineName,
    },
  };
};

const SECRET_NAMES = ['GH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'OPENAI_API_KEY'];

const agentSecrets = () => {
  const result = run(['secrets', 'ls', '--json'], { quiet: true });
  if (result.status !== 0) {
    return [];
  }
  try {
    const saved = (JSON.parse(result.stdout).items || []).map((item) => item.name);
    return SECRET_NAMES.filter((secret) => saved.includes(secret));
  } catch (error) {
    return [];
  }
};

const CLAUDE_ONBOARDED = [
  'const fs = require(~fs~);',
  'const file = require(~os~).homedir() + ~/.claude.json~;',
  'let config = {};',
  'try { config = JSON.parse(fs.readFileSync(file, ~utf8~)); } catch (error) {}',
  'config.hasCompletedOnboarding = true;',
  'fs.writeFileSync(file, JSON.stringify(config, null, 2));',
]
  .join(NL)
  .split('~')
  .join(QUOTE);

const checkoutWorkspaceBranch = (machineId, repoUrl, projectRoot) => {
  const branch = env.ORCA_REPO_BRANCH || currentBranch();
  const head = env.ORCA_REPO_REF_HEAD || currentHead();
  if (!branch) {
    throw new Error('Orca did not pass the workspace branch and start commit.');
  }
  const git = 'git -C ' + shellQuote(projectRoot) + ' ';
  const fetchFlags = ['--timeout', '600', '--env', 'GIT_TERMINAL_PROMPT=0'];
  const fetchOptions = { quiet: true, timeoutSeconds: 660 };
  const url = env.ORCA_REPO_URL || repoUrl;
  if (env.ORCA_REPO_REF) {
    remote(machineId, git + 'fetch --quiet -- ' + shellQuote(url) + ' ' + shellQuote(env.ORCA_REPO_REF), fetchFlags, fetchOptions);
  }
  if (head) {
    if (remote(machineId, git + 'cat-file -e ' + shellQuote(head + '^{commit}'), [], { quiet: true }).status !== 0) {
      remote(machineId, git + 'fetch --quiet -- ' + shellQuote(url) + ' ' + shellQuote(head), fetchFlags, fetchOptions);
    }
    if (remote(machineId, git + 'cat-file -e ' + shellQuote(head + '^{commit}'), [], { quiet: true }).status !== 0) {
      log('Head ' + head.slice(0, 12) + ' not present on remote, falling back to branch ' + branch);
      remote(machineId, git + 'checkout --quiet ' + shellQuote(branch), [], { quiet: true });
      return;
    }
    log('Checking out ' + branch + ' at ' + head.slice(0, 12) + '.');
    const checkout = remote(machineId, git + 'checkout --quiet -B ' + shellQuote(branch) + ' ' + shellQuote(head));
    if (checkout.status !== 0) {
      throw new Error('Could not check out ' + branch + ' on the machine.');
    }
  } else {
    log('Checking out ' + branch + '.');
    const checkout = remote(machineId, git + 'checkout --quiet ' + shellQuote(branch));
    if (checkout.status !== 0) {
      throw new Error('Could not check out ' + branch + ' on the machine.');
    }
  }
};

const create = () => {
  if (env.ORCA_RECIPE_RESULT_SCHEMA_VERSION !== '2') {
    fail('This Orca did not ask for a provisioned-root result. Update Orca to 1.4.245 or later.');
  }
  const repoUrl = httpsCloneUrl(env.ORCA_REPO_URL || originUrl());
  if (!repoUrl) {
    fail('Instabox clones the repository from its origin remote over HTTPS, and this repository has none. Push it to a Git host first.');
  }
  const name = machineName(env.ORCA_WORKSPACE_NAME, env.ORCA_VM_INSTANCE_ID);
  const createArgs = ['create', '--name', name, '--meta', 'orca-instance=' + (env.ORCA_VM_INSTANCE_ID || name)];
  log('Creating machine ' + name + '.');
  const secrets = agentSecrets();
  if (secrets.length > 0) {
    log('Selecting Instabox Secrets ' + secrets.join(', ') + '.');
  }
  if (secrets.length === 0 || run(createArgs.concat(['--secrets', secrets.join(',')]), { quiet: true }).status !== 0) {
    if (secrets.length > 0 && machineState(name) !== 'gone') {
      removeMachine(name);
      fail('Could not create Instabox machine ' + name + '.');
    }
    must(createArgs);
  }
  let machineId = name;
  try {
    machineId = JSON.parse(must(['get', name, '--json'])).id || name;
    const pwd = remote(machineId, 'pwd');
    const home = pwd.status === 0 ? pwd.stdout.trim() : '';
    if (!home.startsWith('/')) {
      throw new Error('Could not read the home directory of ' + name + '.');
    }
    const projectRoot = home + '/' + repoDirName(repoUrl);
    remote(machineId, 'gh auth setup-git', [], { quiet: true });
    if (secrets.includes('OPENAI_API_KEY')) {
      remote(machineId, 'printenv OPENAI_API_KEY | codex login --with-api-key', [], { quiet: true });
    }
    if (secrets.includes('CLAUDE_CODE_OAUTH_TOKEN')) {
      remote(machineId, 'node', ['--stdin'], { quiet: true, input: CLAUDE_ONBOARDED });
    }
    log('Cloning ' + withoutCredentials(repoUrl) + ' into ' + projectRoot + '.');
    const clone = remote(
      machineId,
      'git clone --quiet -- ' + shellQuote(repoUrl) + ' ' + shellQuote(projectRoot),
      ['--timeout', '600', '--env', 'GIT_TERMINAL_PROMPT=0'],
      { timeoutSeconds: 660 }
    );
    if (clone.status !== 0) {
      throw new Error(
        'git clone failed on the machine. For a private repository, save a GitHub token as an Instabox Secret named GH_TOKEN for github.com, for example: gh auth token | instabox secrets set GH_TOKEN --host github.com --host api.github.com'
      );
    }
    checkoutWorkspaceBranch(machineId, repoUrl, projectRoot);
    process.stdout.write(JSON.stringify(connectionResult(machineId, name, projectRoot)) + NL);
  } catch (error) {
    log(error.message);
    log('Deleting ' + name + ' after the failed create.');
    removeMachine(machineId);
    process.exit(1);
  }
};

const suspend = () => {
  const { machineId } = readPayload();
  must(['suspend', machineId]);
};

const resume = () => {
  const { machineId, recipeResult } = readPayload();
  if (machineState(machineId) !== 'running') {
    must(['resume', machineId]);
  }
  process.stdout.write(JSON.stringify(recipeResult) + NL);
};

const destroy = () => {
  const { machineId } = readPayload();
  if (!removeMachine(machineId)) {
    fail('Could not delete Instabox machine ' + machineId + '.');
  }
};

const phases = {
  create: create,
  suspend: suspend,
  resume: resume,
  destroy: destroy,
};

const phase = phases[env.ORCA_VM_MODE];
if (!phase) {
  fail('Unknown ORCA_VM_MODE ' + env.ORCA_VM_MODE + '.');
}

try {
  phase();
} catch (error) {
  fail(error.message);
}
