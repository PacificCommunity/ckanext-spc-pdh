const { watch } = require('gulp');
const { exec } = require('child_process');

const root = __dirname + '/ckanext/spc/';
const lessPath = root + 'theme/public/base/less';
const publicPath = root + 'fanstatic/styles';

const isProd = () => process.argv.includes('--prod');

const build = () =>
  console.log('Recompiling styles...') ||
  exec(
    `lessc ${lessPath}/spc.less ${publicPath}/spc.css` +
      (isProd() ? '' : ' --source-map-inline --source-map-include-source')
  );

const observeChanges = () =>
  watch(lessPath + '/*.less', { ignoreInitial: false }, build);

exports.default = observeChanges;
exports.watch = observeChanges;
exports.build = build;
