const gulp = require('gulp');
const exec = require('child_process').exec;

const root = __dirname + '/ckanext/spc/';
const lessPath = root + 'theme/public/base/less';
const publicPath = root + 'fanstatic/styles';

const isProd = () => process.argv.includes('--prod');

const compile = () =>
  console.log('Recompiling styles...') ||
  exec(
    `lessc ${lessPath}/spc.less ${publicPath}/spc.css` +
      (isProd() ? '' : ' --source-map-inline --source-map-include-source')
  );

const watch = () => gulp.watch(lessPath + '/*.less', compile);

gulp.task('default', watch);
gulp.task('compile', compile);
