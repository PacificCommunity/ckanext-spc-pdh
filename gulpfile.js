const gulp = require('gulp');
const exec = require('child_process').exec;

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

const watch = () => gulp.watch(lessPath + '/*.less', build);

gulp.task('default', watch);
gulp.task('watch', watch);
gulp.task('build', build);
