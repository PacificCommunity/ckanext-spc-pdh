const { watch, src, dest } = require('gulp');
const less = require('gulp-less');

const { exec } = require('child_process');

const root = __dirname + '/ckanext/spc/';
const lessPath = root + 'theme/public/base/less';
const publicPath = root + 'fanstatic/styles';


const build = () =>
      src(`${lessPath}/spc.less`).pipe(less()).pipe(dest(publicPath));

const observeChanges = () =>
  watch(lessPath + '/*.less', { ignoreInitial: false }, build);

exports.default = observeChanges;
exports.watch = observeChanges;
exports.build = build;
